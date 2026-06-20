"""AI editor: triage draft news stories for the Chesterfield County, VA site.

Policy (user-chosen): "auto-approve safe, flag the rest."

For each un-triaged draft, we ask the Claude Code CLI (Haiku by default) to
judge whether the item is safe to AUTO-PUBLISH with no human review. The model's
verdict is then run through a CONSERVATIVE server-side "safety belt": we only
auto-approve when the model AND our own hard rules agree the item is clearly
safe, newsworthy, on-topic, original, government-licensed, and not police/fire.
Anything sensitive, uncertain, press-licensed, or police/fire ALWAYS goes to a
human — regardless of what the model said.

Auto-approved items are (optionally) deepened into a full web-researched
article and then MOVED from content/drafts/ to content/published/. Everything
else is annotated and left in drafts for a human to review.

Idempotent: a draft that already carries an `ai_verdict` frontmatter key is
skipped, so re-running triage() never re-processes the same file.

Stdlib + the `claude` CLI only (shelled out exactly like enrich._enrich_cli).
"""
from __future__ import annotations

import datetime
import json
import re
import shutil
import subprocess
import urllib.request
from collections import defaultdict
from pathlib import Path

from . import dedup
from . import enrich as enrich_mod
from . import render

MODEL = "claude-haiku-4-5"
CLI_TIMEOUT = 120   # seconds per triage call (no web search, so quick)

# --- Auto-approval policy knobs (tune per-locality / per editor's taste) ----
# The pipeline auto-publishes drafts the AI editor approves. These widen or
# narrow what may auto-publish. Defaults are LOOSE — publish most genuinely
# newsworthy local stories, including police/fire — but a likely DUPLICATE of
# an already-published story is NEVER auto-published (it goes to human review).
AUTO_ALLOW_SENSITIVE = True             # False => crime/police/fire/opinion always wait for a human
AUTO_REQUIRE_GOVERNMENT_LICENSE = False  # True  => only government-licensed sources auto-publish
DUP_GUARD = False                        # OFF: the crude same-event test killed legit FOLLOW-UPS
                                         # (e.g. "missing child found safe", project milestones).
                                         # The smarter qa.py agent now handles dedup before publish.
MAX_DEEPEN = 40                          # cap web-research deepens per run. High because the
                                         # CLI is subscription-wrapped (no per-call $). Overflow
                                         # or deepen failures land as stubs; qa.deepen_stubs()
                                         # backfills the Quick-facts box on the next pass.
FRESHNESS_DAYS = 0                        # 0 = no age limit (user: keep everything, never delete)

# QUIET-DAY FILL: on slow news days the strict significance bar can leave the
# feed empty for hours. When fewer than QUIET_THRESHOLD stories have published in
# the last 24h, let up to QUIET_FILL_MAX "lighter" items through PER RUN — items
# that are genuinely newsworthy + Chesterfield-specific + not promo/junk/sensitive
# but didn't clear the `significant` bar (a library program, a minor road project,
# a small-business note, a community event). Every other guardrail still applies.
# On busy days (>= QUIET_THRESHOLD already published) this does nothing.
QUIET_DAY_FILL = True
QUIET_THRESHOLD = 3                       # < this many published in last 24h => quiet day
QUIET_FILL_MAX = 3                        # cap on lighter fill items per run

# AUTONOMOUS: no human in the critical path. Anything newsworthy+significant that
# the editor doesn't outright reject gets PUBLISHED (the pre-publish qa.py agent
# is the safety net); rejects and duplicates are moved out of the queue instead
# of waiting for a human. The localhost review UI becomes optional oversight.
# Set False to go back to "auto-approve safe, hold the rest for a human."
AUTONOMOUS = True

# Rejected/duplicate drafts move here (reversible) instead of lingering in the
# queue marked 'reject'. Mirrors serve.py / qa.py conventions.
REMOVED = render.DRAFTS.parent / "removed"

# Review decisions the human logged at localhost:8787 (Approve / reason-tagged
# Reject). The editor reads this to mimic the human's demonstrated taste.
FEEDBACK_LOG = Path(__file__).resolve().parents[1] / "review_feedback.jsonl"

# Strict structured-output schema. additionalProperties:false + all required,
# exactly as the enrich backends do for Claude Code structured outputs.
_SCHEMA = {
    "type": "object",
    "properties": {
        "newsworthy": {"type": "boolean"},
        "significant": {"type": "boolean"},
        "chesterfield_specific": {"type": "boolean"},
        "sensitive": {"type": "boolean"},
        "duplicate_or_promo": {"type": "boolean"},
        "verdict": {"type": "string", "enum": ["approve", "review", "reject"]},
        "reason": {"type": "string"},
    },
    "required": ["newsworthy", "significant", "chesterfield_specific", "sensitive",
                 "duplicate_or_promo", "verdict", "reason"],
    "additionalProperties": False,
}

_RUBRIC = (
    "You are the editor of a hyperlocal news site, deciding whether each draft "
    "can be AUTO-PUBLISHED now or should wait for the human editor. Lean toward "
    "approving genuinely newsworthy local stories — readers want timely coverage "
    "— while routing the low-value and the genuinely fraught to review.\n"
    "Set significant=true for real news value to residents: a decision or vote, a "
    "development/opening/closure, a budget or policy change, a public-safety or "
    "court/crime development, an event with broad impact, or anything consequential "
    "and new. ALSO treat as significant: (a) LOCAL SPORTS RESULTS and achievements "
    "— a local team winning or losing a notable game, a title or playoff run, a "
    "record or streak, a player's college commitment or all-state honor — but NOT "
    "bare game schedules or previews that have no result; and (b) clearly-LOCAL "
    "COMMUNITY and human-interest stories — youth programs and camps, volunteer or "
    "student recognition, fundraisers and drives, scholarships, neighborhood events, "
    "a named local business milestone — even when they are feel-good rather than "
    "hard news. Set significant=FALSE for routine filler: bare calendars/meeting "
    "notices, bare sports schedules or previews with no result, recruitment, "
    "real-estate or property listings, generic promotional/PR content with no named "
    "specifics, thin stubs, and status updates with no real news.\n"
    "Set sensitive=true for crime, police, courts, arrests, accidents, death, "
    "lawsuits, named individuals in a negative light, or strong opinion.\n"
    "chesterfield_specific=true ONLY if the story is about Chesterfield COUNTY, "
    "VIRGINIA, USA (or its communities: Midlothian, Chester, Chesterfield, Moseley, "
    "Bon Air, Matoaca, Ettrick, Brandermill, Woodlake) or its residents, government, "
    "schools, or businesses. CRITICAL: there is also a Chesterfield in Derbyshire, "
    "England, and Chesterfields in other US states. If the story is about a "
    "Chesterfield OUTSIDE Chesterfield County, Virginia, set chesterfield_specific="
    "FALSE and verdict='reject'. Tell-tale signs it is the UK Chesterfield "
    "(Derbyshire, England): mentions of Derbyshire, England, the UK, a Crown Court "
    "or magistrates' court, amounts in pounds (£), Sheffield, the M1, or UK "
    "place/road names. When the location is ambiguous and there is no clear "
    "Virginia or US signal, lean toward chesterfield_specific=false.\n"
    "ALSO reject (chesterfield_specific=false) when the underlying SOURCE is "
    "really about somewhere else and Chesterfield was added without support, e.g. "
    "a regional story about data centers, projects, or policy in OTHER Virginia "
    "counties (Louisa, Spotsylvania, Stafford, Caroline, Henrico, etc.) that does "
    "not itself concern Chesterfield County. If the local angle is not clearly in "
    "the source, do not approve it as Chesterfield news.\n"
    "verdict: 'approve' = newsworthy and fit to publish as-is; 'review' = needs a "
    "human (low-value-but-real, or fraught in a way the editor below would hold "
    "back); 'reject' = spam/promo/recruitment/off-topic/trivial/duplicate. "
    "reason: one short sentence.\n"
    "If a HUMAN EDITOR'S DEMONSTRATED TASTE section is provided below, match it: "
    "approve things like what they publish, and route to review/reject things like "
    "what they reject — especially items resembling their 'sensitive' rejections."
)


def _taste_block() -> str:
    """Summarize the human's logged review decisions into a few-shot taste guide
    that gets appended to the editor's system prompt. Empty string until there
    is feedback to learn from, so the editor degrades gracefully on day one."""
    try:
        raw = FEEDBACK_LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    recs = []
    for ln in raw[-400:]:
        try:
            recs.append(json.loads(ln))
        except Exception:
            continue
    if not recs:
        return ""

    def heads(rows, k=6):
        out = []
        for r in rows[-k:]:
            h = (r.get("headline") or "").strip().strip('"')
            if h:
                out.append(h)
        return out

    appr = [r for r in recs if r.get("action") == "approve"]
    rej = [r for r in recs if r.get("action") == "reject"]
    by_reason: dict[str, list] = defaultdict(list)
    for r in rej:
        by_reason[r.get("reason") or "other"].append(r)

    parts = [f"\n\nHUMAN EDITOR'S DEMONSTRATED TASTE "
             f"({len(appr)} approvals, {len(rej)} rejections — mimic it):"]
    if appr:
        parts.append("APPROVED (publish things like these): " + "; ".join(heads(appr)))
    for reason in ("sensitive", "boring", "duplicate", "other"):
        rows = by_reason.get(reason)
        if rows:
            parts.append(f"REJECTED as {reason} (lean review/reject on things like "
                         f"these): " + "; ".join(heads(rows)))
    return "\n".join(parts)


def _published_stories() -> list:
    """Load all currently-published stories for the duplicate guard."""
    out = []
    for p in dedup.PUBLISHED.glob("*.md"):
        try:
            out.append(dedup._Story(p))
        except Exception:
            continue
    return out


def _too_old(meta: dict, path) -> bool:
    """True if the story is older than FRESHNESS_DAYS (stale for a news site).
    Uses the published-date frontmatter, falling back to the filename date."""
    if not FRESHNESS_DAYS:
        return False
    d = dedup._parse_date(meta.get("published", "")) or dedup._date_from_name(path)
    if not d:
        return False
    return (datetime.date.today() - d).days > FRESHNESS_DAYS


def _published_last_24h() -> int:
    """Count stories in content/published whose `published` timestamp is within
    the last 24 hours. Best-effort (items with no/unparseable date are skipped);
    used only to decide whether it's a 'quiet day' for the fill logic."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
    n = 0
    for p in render.PUBLISHED.glob("*.md"):
        try:
            meta, _ = render._parse_frontmatter(p.read_text(encoding="utf-8"))
            raw = (meta.get("published") or "").strip().strip('"')
            d = datetime.datetime.fromisoformat(raw)
            if d.tzinfo is None:
                d = d.replace(tzinfo=datetime.timezone.utc)
            if d >= cutoff:
                n += 1
        except (ValueError, OSError):
            continue
    return n


def _looks_duplicate(path, pub: list) -> bool:
    """True if this draft is the SAME underlying event as something already
    published (reuses the conservative dedup same-event test)."""
    try:
        s = dedup._Story(path)
    except Exception:
        return False
    for ps in pub:
        try:
            if dedup._same_event(s, ps, 0.5):
                return True
        except Exception:
            continue
    return False


def _yq(s: str) -> str:
    """Quote a string for a YAML frontmatter value (matches render's style)."""
    return '"' + (s or "").replace('"', '\\"') + '"'


def _triage_cli(meta: dict, body: str, model: str, system: str = _RUBRIC) -> dict:
    """Ask the Claude Code CLI for a triage verdict on one draft.

    Returns the parsed structured_output dict (matching _SCHEMA). Raises on any
    CLI / parse failure so the caller can decide how to handle it.
    """
    headline = meta.get("headline", "")
    summary = next(
        (ln for ln in body.splitlines() if ln and not ln.startswith(("#", "*"))),
        "",
    )
    prompt = (
        "Triage this draft news item for the Chesterfield County, VA news site. "
        "Decide whether it can be auto-published with no human review.\n\n"
        f"Headline: {headline}\n"
        f"Source: {meta.get('source', '')}\n"
        f"License: {meta.get('license', '')}\n"
        f"Focus: {meta.get('focus', '')}\n"
        f"Tags: {meta.get('tags', '')}\n"
        f"Summary: {summary}\n\n"
        "Fill the schema: newsworthy, chesterfield_specific, sensitive, "
        "duplicate_or_promo, verdict (approve/review/reject), and a one-sentence "
        "reason."
    )
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(_SCHEMA),
        "--append-system-prompt", system,
        "--model", model,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:200] or "claude CLI failed")
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(envelope.get("result", "CLI returned is_error"))
    data = envelope.get("structured_output")
    if not data:
        raise RuntimeError("CLI returned no structured_output")
    return data


def _focus_labels(meta: dict) -> list[str]:
    """Lower-cased focus labels from the frontmatter `focus: [..]` list."""
    raw = meta.get("focus", "")
    return [x.strip().lower() for x in raw.strip("[]").split(",") if x.strip()]


def _can_auto_approve(meta: dict, v: dict) -> bool:
    """Server-side safety belt, governed by the policy knobs at the top of this
    module. Defaults are loose (police/fire/most things may auto-publish), but
    the basics always hold: the model approved, it's significant, newsworthy,
    on-topic, not promo, and it's a real AI-written draft (never a raw extractive
    stub or linkqueue candidate). The duplicate guard is applied separately in
    triage()."""
    if not (
        v.get("verdict") == "approve"
        and v.get("significant")
        and not v.get("duplicate_or_promo")
        and v.get("newsworthy")
        and v.get("chesterfield_specific")
        and meta.get("ai_provider") in ("claude-cli", "claude-api")
    ):
        return False
    if not AUTO_ALLOW_SENSITIVE and v.get("sensitive"):
        return False
    if AUTO_REQUIRE_GOVERNMENT_LICENSE and meta.get("license") != "government":
        return False
    return True


# Chesterfield County, VA place names used to confirm a cited source actually
# concerns our county (not a "Chesterfield" elsewhere, and not a story the model
# pinned to Chesterfield without support, e.g. Amazon data centers in other VA
# counties). "chester" intentionally last via word boundary in the regex.
_CHES_PLACE_RE = re.compile(
    r"\bchesterfield\b|\b(midlothian|matoaca|moseley|ettrick|brandermill|"
    r"woodlake|winterpock|bon air|robious|enon|dale district|clover hill|"
    r"hull street|iron bridge|courthouse road|swift creek|magnolia green|"
    r"rountrey|pocahontas state park|virginia state university|\bvsu\b|"
    r"manchester high|cosby high|monacan high|thomas dale|l\.?c\.? bird|"
    r"meadowbrook high|james river high|clover hill high|matoaca high|"
    r"midlothian high|chester\b)", re.I)

# Other Virginia localities that signal a story is really about somewhere else.
# We only treat "no Chesterfield mention" as a problem when the source clearly
# concerns one of these instead (the Amazon-data-centers-in-other-counties case).
# Richmond/metro neighbors are deliberately excluded to avoid false holds.
_OTHER_LOCALITY_RE = re.compile(
    r"\b(louisa|spotsylvania|powhatan|goochland|dinwiddie|nottoway|fluvanna|"
    r"loudoun|prince william|prince george county|new kent|stafford county|"
    r"caroline county|amelia county|cumberland county)\b", re.I)

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _source_grounds_chesterfield(url: str):
    """Best-effort grounding: fetch the cited source. Returns True if it mentions
    a Chesterfield County, VA place; False ONLY if it never mentions Chesterfield
    AND clearly concerns another locality (the misattribution signature); and None
    when we can't judge (no URL, a trusted county source, a block/paywall, too
    little text, or simply no competing-locality signal). None and True both allow
    publishing; only False routes to human review. This stays deliberately
    conservative so legitimate local stories are not held just because the source
    omits the word 'Chesterfield'."""
    url = (url or "").strip().strip('"')
    if not url.startswith("http"):
        return None
    if "chesterfield.gov" in url:        # county sources are inherently local
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read(500_000).decode("utf-8", "ignore")
    except Exception:
        return None                      # blocked/timeout -> don't judge
    text = re.sub(r"<[^>]+>", " ", html)
    if len(text) < 800:                  # JS-only/paywall/redirect stub
        return None
    if _CHES_PLACE_RE.search(text):
        return True                      # grounded in Chesterfield
    if _OTHER_LOCALITY_RE.search(text):
        return False                     # about another county, not Chesterfield
    return None                          # can't tell -> publish (fail open)


def _deepen(path, meta: dict, body: str, model: str) -> None:
    """Web-research the draft into a full long-form article in place.
    Mirrors run.cmd_article's topic construction."""
    headline = meta.get("headline") or path.stem
    summary = next(
        (ln for ln in body.splitlines() if ln and not ln.startswith(("#", "*"))),
        "",
    )
    topic = f"{headline}\n\nContext: {summary}\nSource: {meta.get('source_url', '')}"
    data = enrich_mod.write_article(topic, model=model)
    render.write_full_article(path, data)


def _reject_file(path, meta: dict, kind: str, reason: str, sensitive: bool) -> None:
    """Record the verdict, then move a non-publishable draft to content/removed/
    (reversible) so the queue doesn't fill with rejected items."""
    try:
        render.update_frontmatter(path, {
            "ai_verdict": kind,
            "ai_verdict_reason": _yq(reason),
            "ai_sensitive": "true" if sensitive else "false",
        })
    except Exception:
        pass
    try:
        REMOVED.mkdir(parents=True, exist_ok=True)
        dest = REMOVED / path.name
        if dest.exists():
            dest = REMOVED / f"{path.stem}.dup{path.suffix}"
        path.rename(dest)
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Regional track: Virginia / area news that affects residents but isn't local.
# These drafts (track=regional) get a separate judgment and, if they pass, move
# to content/regional/ (rendered on /virginia.html, never the local feed).
# --------------------------------------------------------------------------- #

REGIONAL = render.PUBLISHED.parent / "regional"

_REGIONAL_SCHEMA = {
    "type": "object",
    "properties": {
        "publish": {"type": "boolean"},
        "chesterfield_local": {"type": "boolean"},
        "affects_residents": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["publish", "chesterfield_local", "reason"],
}


def _regional_decide(meta: dict, body: str, model: str) -> dict:
    headline = meta.get("headline", "")
    summary = next((ln for ln in body.splitlines() if ln and not ln.startswith(("#", "*"))), "")
    prompt = (
        "You are the regional-news editor for a Chesterfield County, Virginia local "
        "news site. This item arrived from a statewide/regional feed. Make TWO judgments.\n\n"
        f"Headline: {headline}\nSource: {meta.get('source','')}\nSummary: {summary}\n\n"
        "1) publish: set true ONLY if it is newsworthy, real (not a press release, ad, "
        "listicle, sports trivia, or fluff), and a typical Chesterfield resident would "
        "care because it MATERIALLY affects them: a new or proposed state law, the state "
        "budget, taxes, a Dominion/utility rate change, regional transportation (I-95, "
        "tolls, CVTA), a statewide election, a court ruling, education funding, or a "
        "public-safety policy change. Set publish=false for another locality's purely "
        "local news, national politics not specific to Virginia, lifestyle/fluff, thin "
        "items, or duplicates.\n"
        "2) chesterfield_local: set true if the story is SPECIFICALLY centered on "
        "Chesterfield County itself, a project, development, business, decision, vote, "
        "event, or incident located IN or directly about Chesterfield County (examples: "
        "a data center being built in Chesterfield, a county Board vote, a local road "
        "project, a Chesterfield company expanding). Those are FRONT-PAGE LOCAL news, not "
        "a regional sidebar. Set chesterfield_local=false for genuinely statewide or "
        "multi-locality news that merely affects Chesterfield among others.\n\n"
        "Return publish, chesterfield_local, and a one-sentence reason. Do not use em dashes."
    )
    cmd = ["claude", "-p", prompt, "--output-format", "json",
           "--json-schema", json.dumps(_REGIONAL_SCHEMA), "--model", model]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:200] or "regional CLI failed")
    data = json.loads(proc.stdout).get("structured_output")
    if not data:
        raise RuntimeError("regional CLI returned no structured_output")
    return data


def _handle_regional(path, meta: dict, body: str, model: str) -> str:
    """Judge a regional-track draft; publish to content/regional/ or reject
    (reversible). Returns 'publish' or 'reject'. Never raises."""
    try:
        v = _regional_decide(meta, body, model)
    except Exception as e:                       # noqa: BLE001
        v = None
        print(f"  ! regional triage failed for {path.name}: {e}")
    if not v or not v.get("publish"):
        reason = ((v or {}).get("reason") or "not regionally relevant").strip()
        _reject_file(path, meta, "regional", reason, False)
        print(f"{path.name} — regional reject — {reason[:80]}")
        return "reject"
    reason = (v.get("reason") or "").strip()
    if v.get("chesterfield_local"):
        # Came from a regional feed but is squarely a Chesterfield County story:
        # route it to the LOCAL front page (track="") instead of /virginia.html.
        render.update_frontmatter(path, {
            "track": "",
            "ai_verdict": "approve",
            "ai_verdict_reason": _yq(reason),
            "ai_sensitive": "false",
            "status": "published",
        })
        render.PUBLISHED.mkdir(parents=True, exist_ok=True)
        dest = render.PUBLISHED / path.name
        dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.unlink()
        print(f"{path.name} — local publish (Chesterfield-specific, from regional feed) — {reason[:60]}")
        return "publish"
    render.update_frontmatter(path, {
        "ai_verdict": "approve",
        "ai_verdict_reason": _yq(reason),
        "ai_sensitive": "false",
        "status": "published",
    })
    REGIONAL.mkdir(parents=True, exist_ok=True)
    dest = REGIONAL / path.name
    dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
    print(f"{path.name} — regional publish — {reason[:80]}")
    return "publish"


def triage(model: str = "claude-haiku-4-5", deepen: bool = True,
           max_deepen: int = MAX_DEEPEN, limit: int = 12) -> dict:
    """Triage un-triaged drafts: auto-approve clearly-safe items and route the
    rest to a human.

    For each draft in content/drafts/*.md WITHOUT an `ai_verdict` frontmatter
    key (idempotent), up to `limit` drafts:
      1. Ask the Claude Code CLI (Haiku) for a structured verdict.
      2. Apply the conservative server-side safety belt.
      3. If it qualifies to auto-approve: optionally deepen (up to `max_deepen`),
         set status: published, and MOVE the file to content/published/.
         Otherwise annotate and leave it in drafts.
      4. ALWAYS annotate frontmatter with ai_verdict / ai_verdict_reason /
         ai_sensitive (these mark the draft "triaged" so it's skipped next run).

    Returns {"approved", "deepened", "review", "rejected", "processed"}.
    """
    drafts = sorted(render.DRAFTS.glob("*.md"))
    approved = deepened = review = rejected = duplicate = regional_pub = 0

    # Build the taste-tuned system prompt once, and load the published set for
    # the duplicate guard (we append to it as we auto-publish this run).
    system = _RUBRIC + _taste_block()
    pub = _published_stories() if DUP_GUARD else []

    # Quiet-day fill: if the last 24h have been slow, allow a few lighter items
    # through (see the QUIET_* knobs at the top of this module).
    quiet_day = QUIET_DAY_FILL and _published_last_24h() < QUIET_THRESHOLD
    quiet_filled = 0

    processed_files = 0
    for path in drafts:
        if processed_files >= limit:
            break
        text = path.read_text(encoding="utf-8")
        meta, body = render._parse_frontmatter(text)
        if "ai_verdict" in meta:
            continue  # already triaged — idempotent skip

        # Regional-track drafts get a separate judgment and go to content/regional/.
        if meta.get("track") == "regional":
            if _handle_regional(path, meta, body, model) == "publish":
                regional_pub += 1
            else:
                rejected += 1
            processed_files += 1
            continue

        try:
            v = _triage_cli(meta, body, model, system=system)
        except Exception as e:
            # Could not get a verdict — be conservative: flag for review, leave
            # in drafts, and mark it triaged so we don't loop on a broken item.
            reason = f"triage failed ({e}); flagged for human review"
            render.update_frontmatter(path, {
                "ai_verdict": "review",
                "ai_verdict_reason": _yq(reason),
                "ai_sensitive": "true",
            })
            print(f"{path.name} — review — {reason}")
            review += 1
            processed_files += 1
            continue

        reason = (v.get("reason") or "").strip()
        sensitive = bool(v.get("sensitive"))
        model_verdict = v.get("verdict", "review")

        can_approve = _can_auto_approve(meta, v)
        # In autonomous mode we also publish newsworthy+significant items the
        # model merely flagged 'review' (no human to wait on) — but never junk,
        # promo, or raw stubs, and never an outright 'reject'.
        autonomous_ok = (
            AUTONOMOUS
            and model_verdict != "reject"
            and meta.get("ai_provider") in ("claude-cli", "claude-api")
            and v.get("newsworthy")
            and v.get("significant")
            and v.get("chesterfield_specific")   # must be Chesterfield County, VA —
            and not v.get("duplicate_or_promo")  # not a "Chesterfield" elsewhere (e.g.
        )                                        # Chesterfield Ave, Lancaster SC)
        # Quiet-day fill: a lighter (not "significant") but genuinely local item,
        # only when the day's been slow and we're under the per-run cap. Keeps
        # every other guardrail (newsworthy, on-topic, not promo/junk/sensitive).
        quiet_ok = (
            quiet_day
            and quiet_filled < QUIET_FILL_MAX
            and model_verdict != "reject"
            and meta.get("ai_provider") in ("claude-cli", "claude-api")
            and v.get("newsworthy")
            and v.get("chesterfield_specific")
            and not v.get("duplicate_or_promo")
            and not v.get("sensitive")
        )
        too_old = _too_old(meta, path)
        want_publish = (can_approve or autonomous_ok or quiet_ok) and not too_old

        # Source-grounding gate: if the cited source is a real article that never
        # mentions Chesterfield County, the local angle is unsupported (e.g. a
        # Virginia Mercury story about data centers in OTHER counties). Route to
        # human review rather than auto-publishing a misattributed story.
        if want_publish and _source_grounds_chesterfield(meta.get("source_url", "")) is False:
            reason = ("Cited source does not mention Chesterfield County; "
                      "unsupported or misattributed local angle.")
            render.update_frontmatter(path, {
                "ai_verdict": "review",
                "ai_verdict_reason": _yq(reason),
                "ai_sensitive": "true" if sensitive else "false",
            })
            print(f"{path.name} — review — {reason}")
            review += 1
            processed_files += 1
            continue

        via_quiet = bool(want_publish and quiet_ok and not (can_approve or autonomous_ok))
        is_dup = bool(want_publish and DUP_GUARD and _looks_duplicate(path, pub))

        if want_publish and not is_dup:
            # Annotate as approved BEFORE moving the file.
            render.update_frontmatter(path, {
                "ai_verdict": "approve",
                "ai_verdict_reason": _yq(reason),
                "ai_sensitive": "true" if sensitive else "false",
                "status": "published",
            })
            did_deepen = False
            if deepen and deepened < max_deepen:
                try:
                    # Re-read: update_frontmatter rewrote the file.
                    m2, b2 = render._parse_frontmatter(
                        path.read_text(encoding="utf-8"))
                    _deepen(path, m2, b2, model)
                    did_deepen = True
                except Exception as e:
                    print(f"  ! deepen failed for {path.name} ({e}); "
                          f"publishing quick draft")

            # MOVE the file from drafts/ to published/.
            render.PUBLISHED.mkdir(parents=True, exist_ok=True)
            dest = render.PUBLISHED / path.name
            dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            path.unlink()
            if DUP_GUARD:
                try:
                    pub.append(dedup._Story(dest))   # so later drafts dedup against it
                except Exception:
                    pass

            approved += 1
            if did_deepen:
                deepened += 1
            if via_quiet:
                quiet_filled += 1
            tail = " (deepened)" if did_deepen else ""
            qmark = " [quiet-fill]" if via_quiet else ""
            print(f"{path.name} — approve{tail}{qmark} — {reason}")
        elif is_dup:
            # Duplicates a published story. Autonomous: drop it (the canonical is
            # already live). Otherwise: route to a human to verify/merge.
            note = (reason + " [likely duplicate of a published story]").strip()
            if AUTONOMOUS:
                _reject_file(path, meta, "duplicate", note, sensitive)
                print(f"{path.name} — reject (duplicate) — {note}")
            else:
                render.update_frontmatter(path, {
                    "ai_verdict": "review",
                    "ai_verdict_reason": _yq(note),
                    "ai_sensitive": "true" if sensitive else "false",
                    "ai_duplicate": "true",
                })
                print(f"{path.name} — review (duplicate) — {note}")
            duplicate += 1
        elif too_old and AUTONOMOUS:
            # Stale news — drop it (reversible) rather than publish old items.
            note = (reason + f" [older than {FRESHNESS_DAYS} days — stale]").strip()
            _reject_file(path, meta, "stale", note, sensitive)
            rejected += 1
            print(f"{path.name} — reject (stale) — {note}")
        elif AUTONOMOUS or model_verdict == "reject":
            # Not publishable and no human to defer to -> drop it (reversible).
            _reject_file(path, meta, "reject", reason, sensitive)
            rejected += 1
            print(f"{path.name} — reject — {reason}")
        else:
            # Non-autonomous: leave borderline items in drafts for a human.
            final = model_verdict if model_verdict in ("review", "reject") else "review"
            render.update_frontmatter(path, {
                "ai_verdict": final,
                "ai_verdict_reason": _yq(reason),
                "ai_sensitive": "true" if sensitive else "false",
            })
            if final == "reject":
                rejected += 1
            else:
                review += 1
            print(f"{path.name} — {final} — {reason}")

        processed_files += 1

    return {
        "approved": approved,
        "deepened": deepened,
        "review": review,
        "rejected": rejected,
        "duplicate": duplicate,
        "quiet_fill": quiet_filled,
        "regional": regional_pub,
        "processed": approved + review + rejected + duplicate,
    }
