"""Pre-publish QA agent — the "managing editor" pass.

This is the final sweep the cron runs AFTER triage and BEFORE build/deploy. It
does the judgment work a careful human editor does: it adjudicates duplicate
clusters intelligently (keeping the best version and — crucially — NOT merging
stories that merely share a topic), and it unpublishes empty placeholder stubs
and junk that slipped through.

It uses the Claude Code CLI (`claude -p ... --json-schema ...`), exactly like
enrich.py / editor.py, so it needs no API key. Everything it does is REVERSIBLE:
merged-away files move to content/merged/, unpublished files move to
content/removed/. Nothing is hard-deleted.

Why an LLM and not just dedup.py? Because the mechanical same-event test
over-merges (it will happily fold a brush fire into a townhouse fire). The dedup
clustering is reused only to PROPOSE candidate groups; the agent decides.

Usage:
    from chesterfield import qa
    qa.run()                 # adjudicate + sweep, apply changes, return summary
    qa.run(apply=False)      # dry run: report only, mutate nothing
"""
from __future__ import annotations

import json
import re
import subprocess

from . import dedup
from . import enrich
from . import geo
from . import render
from .render import PUBLISHED, _parse_frontmatter

MODEL = "claude-haiku-4-5"
CLI_TIMEOUT = 120

# Reversible destinations (shared with serve.py / dedup.py conventions).
REMOVED = PUBLISHED.parent / "removed"
MERGED = PUBLISHED.parent / "merged"

# Caps so a single run can't run away on cost.
MAX_UNPUBLISH = 12
MAX_CLUSTERS = 12
MAX_DEEPEN_STUBS = 12   # backfill the Quick-facts box on this many stubs per run

# User policy: keep everything. Only pull literal EMPTY placeholders (zero real
# content) — never let the agent unpublish a real story for being thin/low-value.
# Set True to re-enable LLM-judged junk removal.
QA_UNPUBLISH_JUNK = False

_PLACEHOLDER_RE = re.compile(r"Candidate story surfaced from related coverage", re.I)


# --------------------------------------------------------------------------- #
# Claude Code CLI helper
# --------------------------------------------------------------------------- #

def _cli(prompt: str, schema: dict, system: str, model: str) -> dict:
    """One structured-output Claude Code call. Raises on any failure."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(schema),
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


def _excerpt(body: str, n: int = 600) -> str:
    text = re.sub(r"\s+", " ", body).strip()
    return text[:n]


# --------------------------------------------------------------------------- #
# 1. Duplicate adjudication
# --------------------------------------------------------------------------- #

_DUP_SCHEMA = {
    "type": "object",
    "properties": {
        "same_event": {"type": "boolean"},
        "keep": {"type": "string"},
        "merge_away": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
    "required": ["same_event", "keep", "merge_away", "reason"],
    "additionalProperties": False,
}

_DUP_SYSTEM = (
    "You are a managing editor doing a final duplicate check. You are shown a "
    "GROUP of published stories an automated tool THINKS are duplicates — but the "
    "tool is over-eager and often wrong. Your job is PRECISION: merge only true "
    "redundancy, never distinct journalism.\n"
    "Merge two stories ONLY when they report essentially the SAME specific "
    "development/facts — e.g. two outlets covering the very same arrest, or two "
    "write-ups of the same fire at the same place. Do NOT merge stories that are "
    "different DEVELOPMENTS or ANGLES of one larger incident: an arrest, a "
    "criminal-charges update, a GoFundMe, a memorial/vigil, and a new-evidence "
    "story about one shooting are FIVE different stories — keep them all. Two "
    "different crashes, two different fires, and distinct school-board actions are "
    "also NOT duplicates.\n"
    "If (and only if) two or more are genuinely the same specific story: set "
    "same_event=true, set keep to the filename of the best version (fullest "
    '"## The story" body, most sources, AND a clear representative headline — '
    "never keep a narrow side-angle like a GoFundMe as the canonical if a fuller "
    "main story exists), and list ONLY the truly redundant filenames in "
    "merge_away. Anything that is a distinct story must NOT appear in merge_away. "
    "If nothing is a true duplicate, set same_event=false and merge_away=[]. "
    "Use EXACT filenames as given."
)


def _story_brief(s: "dedup._Story") -> dict:
    return {
        "file": s.path.name,
        "headline": s.headline.strip().strip('"'),
        "focus": sorted(s.focus),
        "has_full_story": s.has_story,
        "sources": s.n_sources,
        "excerpt": _excerpt(s.body, 400),
    }


def adjudicate_clusters(model: str = MODEL, apply: bool = True) -> list[dict]:
    """Ask the agent to confirm/curate each candidate duplicate cluster.
    Returns a list of action records. Applies merges reversibly when apply=True.
    """
    clusters = dedup.find_clusters()[:MAX_CLUSTERS]
    results: list[dict] = []
    for group in clusters:
        stories = [dedup._Story(p) for p in group]
        briefs = [_story_brief(s) for s in stories]
        names = {b["file"] for b in briefs}
        prompt = (
            "Candidate same-event group:\n\n"
            + json.dumps(briefs, ensure_ascii=False, indent=2)
            + "\n\nReturn the schema. keep + merge_away must be filenames from "
              "this group."
        )
        try:
            v = _cli(prompt, _DUP_SCHEMA, _DUP_SYSTEM, model)
        except Exception as e:
            results.append({"files": sorted(names), "action": "skip",
                            "reason": f"qa cli failed: {e}"})
            continue

        keep = (v.get("keep") or "").strip()
        merge_away = [m.strip() for m in (v.get("merge_away") or []) if m.strip()]
        # Validate: everything must be real files in this group, keep not merged.
        merge_away = [m for m in merge_away if m in names and m != keep]
        if not v.get("same_event") or keep not in names or not merge_away:
            results.append({"files": sorted(names), "action": "keep_all",
                            "reason": v.get("reason", "")})
            continue

        rec = {"keep": keep, "merge_away": merge_away,
               "action": "merge", "reason": v.get("reason", "")}
        if apply:
            keep_path = PUBLISHED / keep
            merge_paths = [PUBLISHED / m for m in merge_away if (PUBLISHED / m).exists()]
            if keep_path.exists() and merge_paths:
                dedup._append_sources(keep_path, merge_paths)
                MERGED.mkdir(parents=True, exist_ok=True)
                for p in merge_paths:
                    dest = MERGED / p.name
                    if dest.exists():
                        dest = MERGED / f"{p.stem}.dup{p.suffix}"
                    p.rename(dest)
                rec["merged"] = len(merge_paths)
        results.append(rec)
    return results


# --------------------------------------------------------------------------- #
# 2. Stub / junk sweep
# --------------------------------------------------------------------------- #

_STUB_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["keep", "unpublish"]},
        "reason": {"type": "string"},
    },
    "required": ["action", "reason"],
    "additionalProperties": False,
}

_STUB_SYSTEM = (
    "You are a managing editor reviewing a SHORT published item that has no "
    "full-length body yet. Decide whether it is a legitimate local news brief "
    "worth keeping live (action=keep) or whether it should be pulled from the "
    "site (action=unpublish) because it is an empty placeholder, content-free "
    "stub, pure promo/recruitment, a bare calendar entry, or otherwise not "
    "publishable. Be decisive but not destructive: a real, if short, news brief "
    "should be kept. reason: one short sentence."
)


def _published_stubs() -> list:
    out = []
    for p in sorted(PUBLISHED.glob("*.md")):
        try:
            meta, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        if "## The story" not in body:
            out.append((p, meta, body))
    return out


def sweep_stubs(model: str = MODEL, apply: bool = True) -> list[dict]:
    """Unpublish empty placeholders/junk among the published stubs. Obvious
    'Candidate story surfaced...' placeholders are pulled without an LLM call;
    the rest are judged by the agent. Reversible (-> content/removed/)."""
    results: list[dict] = []
    unpublished = 0
    for p, meta, body in _published_stubs():
        if unpublished >= MAX_UNPUBLISH:
            break
        headline = meta.get("headline", p.stem)

        # Deterministic: literal linkqueue placeholder -> always unpublish.
        if _PLACEHOLDER_RE.search(body):
            decision, reason = "unpublish", "empty linkqueue placeholder"
        elif not QA_UNPUBLISH_JUNK:
            # Policy: keep everything real. Don't judge thin-but-real stories.
            decision, reason = "keep", "kept (keep-everything policy)"
        else:
            prompt = (
                f"Headline: {headline}\n"
                f"Source: {meta.get('source','')}\n"
                f"License: {meta.get('license','')}\n"
                f"Focus: {meta.get('focus','')}\n"
                f"Body: {_excerpt(body, 700)}\n\n"
                "Keep this live, or unpublish it? Return the schema."
            )
            try:
                v = _cli(prompt, _STUB_SCHEMA, _STUB_SYSTEM, model)
            except Exception as e:
                results.append({"file": p.name, "action": "keep",
                                "reason": f"qa cli failed, kept: {e}"})
                continue
            decision = v.get("action", "keep")
            reason = v.get("reason", "")

        if decision == "unpublish":
            if apply:
                REMOVED.mkdir(parents=True, exist_ok=True)
                dest = REMOVED / p.name
                if dest.exists():
                    dest = REMOVED / f"{p.stem}.dup{p.suffix}"
                p.rename(dest)
            unpublished += 1
            results.append({"file": p.name, "action": "unpublish", "reason": reason})
        else:
            results.append({"file": p.name, "action": "keep", "reason": reason})
    return results


# --------------------------------------------------------------------------- #
# 3. Backfill: deepen thin stubs into full articles (adds the Quick-facts box)
# --------------------------------------------------------------------------- #

def _needs_deepen(meta: dict, body: str) -> bool:
    """A published article that never got the long-form treatment, so it has no
    'Quick facts' (who/what/when/where) box. We backfill those. Skip reader
    letters/opinion (written as-is) and empty linkqueue placeholders (sweep_stubs
    pulls those)."""
    if "## Quick facts" in body or "## The story" in body:
        return False
    if meta.get("ai_provider") == "letter":
        return False
    if _PLACEHOLDER_RE.search(body):
        return False
    return True


def _deepen_in_place(path, meta: dict, body: str, model: str) -> None:
    """Web-research a published stub into a full article, in place. Mirrors
    serve._deepen_published / editor._deepen so the Quick-facts box appears."""
    headline = meta.get("headline") or path.stem
    summary = next((ln for ln in body.splitlines()
                    if ln and not ln.startswith(("#", "*", "["))), "")
    topic = (f"{headline}\n\nContext: {summary}\n"
             f"Source: {meta.get('source_url', '')}")
    data = enrich.write_article(topic, model=model)
    render.write_full_article(path, data)
    loc = (data.get("location") or "").strip()
    if loc:
        upd = {"location": json.dumps(loc)}
        g = geo.geocode(loc)
        if g:
            upd["lat"], upd["lon"] = g["lat"], g["lon"]
        render.update_frontmatter(path, upd)


def deepen_stubs(model: str = MODEL, apply: bool = True,
                 limit: int = MAX_DEEPEN_STUBS) -> list[dict]:
    """Backfill the Quick-facts box onto published stubs that slipped through
    without being deepened (triage deepen-cap overflow, deepen failures, or
    legacy items). Reversible in spirit — it only enriches the body in place,
    never deletes. Capped per run; successive cron passes chip through a backlog."""
    results: list[dict] = []
    done = 0
    for p in sorted(PUBLISHED.glob("*.md")):
        if done >= limit:
            break
        try:
            meta, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not _needs_deepen(meta, body):
            continue
        if not apply:
            results.append({"file": p.name, "action": "would-deepen"})
            done += 1
            continue
        try:
            _deepen_in_place(p, meta, body, model)
            results.append({"file": p.name, "action": "deepened"})
        except Exception as e:
            results.append({"file": p.name, "action": "skip",
                            "reason": f"deepen failed: {e}"})
        done += 1
    return results


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def run(model: str = MODEL, apply: bool = True) -> dict:
    """Full pre-publish QA pass. Returns a summary dict."""
    dups = adjudicate_clusters(model=model, apply=apply)
    stubs = sweep_stubs(model=model, apply=apply)
    deepened = deepen_stubs(model=model, apply=apply)
    merged = sum(d.get("merged", 0) for d in dups if d.get("action") == "merge")
    pulled = sum(1 for s in stubs if s["action"] == "unpublish")
    filled = sum(1 for s in deepened if s["action"] == "deepened")
    summary = {
        "clusters_reviewed": len(dups),
        "merged_away": merged,
        "stubs_reviewed": len(stubs),
        "unpublished": pulled,
        "stubs_deepened": filled,
        "details": {"duplicates": dups, "stubs": stubs, "deepened": deepened},
    }
    # Concise console trace for the cron log.
    for d in dups:
        if d.get("action") == "merge":
            print(f"QA dup: keep {d['keep']} <- {', '.join(d['merge_away'])}  ({d['reason']})")
    for s in stubs:
        if s["action"] == "unpublish":
            print(f"QA pull: {s['file']}  ({s['reason']})")
    for s in deepened:
        if s["action"] == "deepened":
            print(f"QA deepen: {s['file']}  (added Quick-facts box)")
        elif s["action"] == "skip":
            print(f"QA deepen skip: {s['file']}  ({s.get('reason','')})")
    print(f"QA summary: {merged} duplicate(s) merged, {pulled} stub(s) unpublished, "
          f"{filled} stub(s) deepened, "
          f"{len(dups)} cluster(s) + {len(stubs)} stub(s) reviewed.")
    return summary
