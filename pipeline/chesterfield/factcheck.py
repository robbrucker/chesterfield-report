"""Twice-daily story fact-check / QA pass.

Re-checks recently-published stories against the failure-mode catalog learned
from the 2026-06-29 audit (see docs/factcheck.md):

  * SAFE auto-fix (deterministic, non-semantic): formatting artifacts (literal
    "\\n" / escaped quotes in the body) and out-of-county map geocodes.
  * FLAG for review (ambiguous or semantic): asserted outcomes not supported by
    the body, date/weekday mismatches, future-dated events, internal number
    contradictions, geography conflation, and source-attribution problems.

Findings are always written to research/wiki/factcheck-journal.md (the record)
and the current HIGH/MED items to research/wiki/QA-ALERTS.md (what lazer reads).
Only when a SAFE auto-fix is applied does run() report apply_built=True, so the
cron knows to rebuild + deploy (once, under the shared flock lock).

Stdlib only; the LLM check shells out to the Claude Code CLI like enrich/qa.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from . import ai
from .render import PUBLISHED, ROOT
from .dedup import _parse_frontmatter

# Two-tier fact-check: the cheap ROUTINE_MODEL screens every story; only stories
# it flags as HIGH (a wrong/misleading published claim) get re-checked by the
# stronger ESCALATE_MODEL. Most days nothing escalates, so the priciest model
# runs a handful of times instead of on all ~30 stories twice a day.
ROUTINE_MODEL = "claude-haiku-4-5"
ESCALATE_MODEL = "claude-sonnet-4-6"
MODEL = ROUTINE_MODEL          # default for _cli(); escalation passes the model explicitly
CLI_TIMEOUT = 240

WIKI_DIR = ROOT / "research" / "wiki"
JOURNAL = WIKI_DIR / "factcheck-journal.md"
ALERTS = WIKI_DIR / "QA-ALERTS.md"

# Chesterfield County, VA bounding box (padded). A map pin outside this is wrong
# (the geocoder's US-centroid / wrong-state fallback put pins in KS / IL).
LAT_MIN, LAT_MAX = 37.15, 37.60
LON_MIN, LON_MAX = -77.95, -77.25

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
             "Saturday", "Sunday"]
_MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

_DATEWORD_RE = re.compile(
    r"\b(" + "|".join(_WEEKDAYS) + r"),?\s+"
    r"(" + "|".join(_MONTHS) + r")\s+(\d{1,2}),?\s+(\d{4})\b")


# --------------------------------------------------------------------------- #
# Story selection
# --------------------------------------------------------------------------- #

def _published_dt(meta: dict, path: Path):
    s = (meta.get("published") or "").strip().strip('"')
    if s:
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        return datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc)
    return None


def recent_stories(window_hours: int, now: datetime) -> list[Path]:
    """Published stories whose publish timestamp is within the rolling window."""
    cutoff = now - timedelta(hours=window_hours)
    out = []
    for p in sorted(PUBLISHED.glob("*.md"), reverse=True):
        meta, _ = _parse_frontmatter(p.read_text(encoding="utf-8"))
        dt = _published_dt(meta, p)
        if dt and dt >= cutoff:
            out.append(p)
    return out


# --------------------------------------------------------------------------- #
# Deterministic checks
# --------------------------------------------------------------------------- #

def _fix_formatting(body: str) -> tuple[str, bool]:
    """Repair literal escape sequences that render as a blob. Returns (body, changed)."""
    orig = body
    if "\\n" in body:
        body = body.replace("\\n\\n", "\n\n").replace("\\n", "\n")
    # Stray escaped quotes outside of code: \" -> "
    body = body.replace('\\"', '"')
    return body, (body != orig)


def _frontmatter_coords(meta: dict):
    out = {}
    for k in ("lat", "lon"):
        v = meta.get(k)
        if v in (None, ""):
            return None
        try:
            out[k] = float(str(v).strip().strip('"'))
        except ValueError:
            return None
    return out


def _check_geocode(meta: dict) -> str | None:
    c = _frontmatter_coords(meta)
    if not c:
        return None
    if not (LAT_MIN <= c["lat"] <= LAT_MAX and LON_MIN <= c["lon"] <= LON_MAX):
        return f"map geocode ({c['lat']}, {c['lon']}) is outside Chesterfield County"
    return None


def _check_dates(text: str, published: datetime | None) -> list[str]:
    """Weekday/date mismatches and impossible dates. FLAG only — we can't tell
    whether the weekday or the numeric date is the wrong one. (We deliberately do
    NOT flag future-dated events: upcoming meetings/events legitimately carry a
    date after the publish date; the LLM check catches genuinely stale outcomes.)"""
    issues = []
    seen = set()
    for wd, mon, day, yr in _DATEWORD_RE.findall(text):
        key = (wd, mon, day, yr)
        if key in seen:
            continue
        seen.add(key)
        try:
            d = datetime(int(yr), _MONTHS[mon], int(day))
        except ValueError:
            issues.append(f"impossible date '{wd}, {mon} {day}, {yr}'")
            continue
        actual = _WEEKDAYS[d.weekday()]
        if actual != wd:
            issues.append(
                f"date/weekday mismatch: '{wd}, {mon} {day}, {yr}' is actually a {actual}")
    return issues


# --------------------------------------------------------------------------- #
# LLM claim check (flag only)
# --------------------------------------------------------------------------- #

_SYSTEM = (
    "You are a meticulous fact-checker for a hyperlocal news site covering "
    "Chesterfield County, Virginia. You catch claims a careful editor would "
    "flag. You are conservative: only report a problem you are confident about, "
    "and never invent issues. Output strictly matches the schema."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["HIGH", "MED", "LOW"]},
                    "type": {"type": "string"},
                    "detail": {"type": "string"},
                    "suggested_fix": {"type": "string"},
                },
                "required": ["severity", "type", "detail", "suggested_fix"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["issues"],
    "additionalProperties": False,
}


def _llm_prompt(headline: str, body: str, source: str) -> str:
    return (
        f"Source outlet: {source}\n"
        f"HEADLINE: {headline}\n\n"
        f"STORY (markdown):\n{body[:6000]}\n\n"
        "Check ONLY for these problems and report any you are confident about:\n"
        "1. The HEADLINE or TL;DR asserts an OUTCOME the body does not support "
        "(e.g. 'approves'/'passes'/'convicted'/'killed' when the body says "
        "proposed/pending/alleged/charged). \n"
        "2. Internal CONTRADICTIONS (a number, name, date, or count that "
        "disagrees with another part of the same story).\n"
        "3. GEOGRAPHY: a place attributed to Chesterfield County, VA that is "
        "actually elsewhere (another county, or another state's Chesterfield).\n"
        "4. SOURCE ATTRIBUTION that looks fabricated or mismatched.\n"
        "5. An OUTCOME that is plainly stale (e.g. still 'missing'/'charged' when "
        "the story itself or its own timeline shows resolution).\n"
        "Do NOT flag style, tone, or things that are merely thin. For each issue "
        "give severity (HIGH=wrong/misleading published claim, MED=unsupported/"
        "unverified, LOW=minor), a short type, the detail, and a one-line fix. "
        "If there are no problems, return an empty issues array."
    )


def _cli(prompt: str, model: str = MODEL) -> dict:
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(_SCHEMA),
        "--append-system-prompt", _SYSTEM,
        "--model", model,
    ]
    proc = ai.run("factcheck", cmd, timeout=CLI_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:200] or "claude CLI failed")
    env = json.loads(proc.stdout)
    if env.get("is_error"):
        raise RuntimeError(env.get("result", "CLI is_error"))
    data = env.get("structured_output")
    if not data:
        raise RuntimeError("no structured_output")
    return data


# --------------------------------------------------------------------------- #
# Per-story audit
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Skip-unchanged cache: the paid LLM claim check is the only per-story cost, so
# we remember the post-fix content hash + last findings per story.  On the next
# run an unchanged story reuses its cached findings instead of paying for the
# sonnet call again.  Pruned to the live window each run so it stays small.
# --------------------------------------------------------------------------- #

FC_CACHE = ROOT / "pipeline" / "factcheck_seen.json"


def _fc_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _load_fc_cache() -> dict:
    try:
        return json.loads(FC_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_fc_cache(cache: dict) -> None:
    try:
        FC_CACHE.write_text(
            json.dumps(cache, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")
    except Exception:
        pass


def audit_story(path: Path, apply_safe: bool, llm_cache: dict | None = None) -> dict:
    """Return {file, headline, fixed: [..], flags: [{severity,type,detail,fix}]}.
    Applies SAFE deterministic fixes in place when apply_safe is True."""
    raw = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(raw)
    headline = (meta.get("headline") or path.stem).strip().strip('"')
    published = _published_dt(meta, path)
    fixed, flags = [], []

    # --- SAFE auto-fixes (deterministic) ---
    new_body, changed = _fix_formatting(body)
    if changed:
        if apply_safe:
            path.write_text(raw.replace(body, new_body, 1), encoding="utf-8")
            raw = path.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(raw)
        fixed.append("repaired literal \\n / escaped-quote formatting in body")

    geo = _check_geocode(meta)
    if geo:
        if apply_safe:
            # Blank the bad coords rather than guess a location (no wrong pin).
            out = []
            for line in raw.splitlines():
                if re.match(r'^(lat|lon):', line.strip()):
                    out.append(line.split(":", 1)[0] + ': ""')
                else:
                    out.append(line)
            path.write_text("\n".join(out) + ("\n" if raw.endswith("\n") else ""),
                            encoding="utf-8")
            fixed.append(f"blanked out-of-county geocode ({geo})")
        else:
            flags.append({"severity": "MED", "type": "geocode",
                          "detail": geo, "fix": "blank or correct lat/lon"})

    # --- FLAG-only deterministic checks ---
    for d in _check_dates(body, published):
        sev = "HIGH" if "AFTER the publish" in d else "MED"
        flags.append({"severity": sev, "type": "date", "detail": d,
                      "fix": "verify and correct the date or weekday"})

    # --- LLM claim check (flag only) ---
    # Only this call costs money.  If the (post-fix) body is byte-identical to
    # the last time we checked it and we applied no fresh fix this run, reuse the
    # cached findings and skip the paid call.
    h = _fc_hash(body)
    cached = llm_cache.get(path.name) if llm_cache is not None else None
    if cached and cached.get("hash") == h and not fixed:
        flags.extend(cached.get("flags", []))
    else:
        llm_flags = []
        prompt = _llm_prompt(headline, body, meta.get("source", ""))
        try:
            issues = _cli(prompt, model=ROUTINE_MODEL).get("issues", [])
            # Escalate to the stronger model ONLY when the cheap pass flags
            # something serious. Its verdict then supersedes the routine one.
            if any(it.get("severity") == "HIGH" for it in issues):
                try:
                    issues = _cli(prompt, model=ESCALATE_MODEL).get("issues", issues)
                except Exception:
                    pass  # escalation failed: keep the routine result
            for it in issues:
                llm_flags.append({"severity": it["severity"], "type": it["type"],
                                  "detail": it["detail"], "fix": it.get("suggested_fix", "")})
        except Exception as e:  # non-fatal: record but don't abort the run
            llm_flags.append({"severity": "LOW", "type": "checker-error",
                              "detail": f"LLM check failed: {str(e)[:120]}", "fix": ""})
        flags.extend(llm_flags)
        # Cache only a clean (non-errored) check so a transient CLI failure is retried.
        if llm_cache is not None and not any(
                f["type"] == "checker-error" for f in llm_flags):
            llm_cache[path.name] = {"hash": h, "flags": llm_flags}

    return {"file": path.name, "headline": headline, "fixed": fixed, "flags": flags}


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #

_SEV_RANK = {"HIGH": 0, "MED": 1, "LOW": 2}


def _write_reports(results: list[dict], now: datetime, window_hours: int) -> dict:
    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    fixed = [r for r in results if r["fixed"]]
    flagged = [r for r in results if r["flags"]]
    hi = [r for r in flagged if any(f["severity"] in ("HIGH", "MED") for f in r["flags"])]

    # Journal (append-only record)
    j = [f"\n## {stamp} — {len(results)} stories ({window_hours}h window)",
         f"- auto-fixed: {len(fixed)} | flagged: {len(flagged)}"]
    for r in fixed:
        j.append(f"- FIXED **{r['file']}**: " + "; ".join(r["fixed"]))
    for r in sorted(flagged, key=lambda r: min(_SEV_RANK[f['severity']] for f in r['flags'])):
        for f in sorted(r["flags"], key=lambda f: _SEV_RANK[f["severity"]]):
            j.append(f"- {f['severity']} **{r['file']}** [{f['type']}]: "
                     f"{f['detail']}  _fix:_ {f['fix']}")
    JOURNAL.write_text(
        (JOURNAL.read_text(encoding="utf-8") if JOURNAL.exists()
         else "# Fact-check journal\n\nAppended by the twice-daily QA runner.\n")
        + "\n".join(j) + "\n", encoding="utf-8")

    # QA-ALERTS (current HIGH/MED only — what lazer reads; overwritten each run)
    a = [f"# Chesterfield Report — QA alerts",
         f"_Updated {stamp}. {len(hi)} stories need review._\n"]
    if not hi:
        a.append("No HIGH/MED items in the last run. All clear.")
    for r in sorted(hi, key=lambda r: min(_SEV_RANK[f['severity']] for f in r['flags'])):
        a.append(f"\n## {r['headline']}")
        a.append(f"`{r['file']}`")
        for f in sorted(r["flags"], key=lambda f: _SEV_RANK[f["severity"]]):
            if f["severity"] in ("HIGH", "MED"):
                a.append(f"- **{f['severity']}** [{f['type']}] {f['detail']} — fix: {f['fix']}")
    ALERTS.write_text("\n".join(a) + "\n", encoding="utf-8")

    return {"checked": len(results), "auto_fixed": len(fixed),
            "flagged": len(flagged), "review_needed": len(hi)}


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def run(window_hours: int = 48, apply_safe: bool = True, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    stories = recent_stories(window_hours, now)
    cache = _load_fc_cache()
    results = [audit_story(p, apply_safe, cache) for p in stories]
    # Prune to the live window so the cache never grows unbounded.
    live = {p.name for p in stories}
    _save_fc_cache({k: v for k, v in cache.items() if k in live})
    summary = _write_reports(results, now, window_hours)
    summary["apply_built"] = apply_safe and summary["auto_fixed"] > 0
    return summary
