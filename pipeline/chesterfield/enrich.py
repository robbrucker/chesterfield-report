"""Turn a raw item into a draft: headline, neutral summary, and a
'why it matters to Chesterfield' line.

Backends (selected by `backend=` / auto-detected in this order):
  * cli         -> shells out to the Claude Code `claude` CLI in --print mode
                   with --json-schema for structured output. No API key needed
                   (uses your Claude Code login). This is the default when the
                   `claude` binary is on PATH. NOTE: each call wraps a full
                   Claude Code agent session, so it's slower and pricier per
                   item than the raw API — use --model claude-haiku-4-5 to cut
                   cost, or batch fewer items.
  * api         -> Anthropic API (Opus 4.8) when `anthropic` is installed AND
                   ANTHROPIC_API_KEY is set. Cheapest/fastest per item.
  * extractive  -> dependency-free fallback: strips HTML, first couple of
                   sentences. Lets the whole pipeline run offline.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

from . import ai
from .models import Item
from .sources import FOCUS_AREAS

MODEL = "claude-haiku-4-5"   # default per user; override with --model
CLI_TIMEOUT = 180            # seconds per enrich item
TIMELINE_TIMEOUT = 420       # timeline research does multiple web searches

# JSON schema the model must fill. additionalProperties:false is required for
# structured outputs; every property is required.
_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "tldr": {"type": "string"},
        "summary": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "location": {"type": "string"},
        "focus_tags": {
            "type": "array",
            "items": {"type": "string", "enum": list(FOCUS_AREAS.keys())},
        },
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "tldr", "summary", "why_it_matters", "location",
                 "focus_tags", "tags"],
    "additionalProperties": False,
}

_SYSTEM = (
    "You are the local-news editor for a community blog covering Chesterfield "
    "County, Virginia. You write clear, neutral, factual copy for residents. "
    "Never invent facts not present in the source. "
    "Do NOT assert an outcome the source does not explicitly state: if a "
    "proposal, rezoning, bill, plan, or vote is pending, under review, or "
    "merely proposed, say so (proposes / reviews / weighs / considers) and "
    "NEVER say approves, passes, rejects, or votes unless the source clearly "
    "reports that action already happened. Use numbers exactly as the source "
    "gives them and keep the headline, tldr, and body consistent with each "
    "other. "
    "Summaries are ORIGINAL "
    "writing (never copied sentences). Keep it tight."
)


def _strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = s.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def _build_prompt(item: Item) -> str:
    body = _strip_html(item.raw_summary)[:4000]
    return (
        f"Source: {item.source_name}\n"
        f"Title: {item.title}\n"
        f"Body: {body or '(no body text provided)'}\n\n"
        "Write a draft for the Chesterfield blog with these fields:\n"
        "- headline: a crisp local headline (<= 12 words)\n"
        "- tldr: a single plain-language sentence — the gist for a busy reader\n"
        "- summary: 2-3 sentence neutral summary in your own words\n"
        "- why_it_matters: one sentence on the impact to Chesterfield residents\n"
        "- location: ONE single specific place for this story (one street, "
        "intersection, address, park, school, or facility in Chesterfield "
        "County). Return an empty string if the story has no specific place OR "
        "covers multiple locations (e.g. a county-wide roundup) — do NOT list "
        "several places\n"
        f"- focus_tags: which of {list(FOCUS_AREAS.keys())} apply\n"
        "- tags: 3-6 specific topical/entity tags (people, places, "
        "organizations, neighborhoods, topics) — e.g. \"Board of Supervisors\", "
        "\"rezoning\", \"Hull Street\", \"VDOT\""
    )


def _apply(item: Item, data: dict, provider: str) -> None:
    item.ai_headline = data["headline"]
    item.ai_tldr = data.get("tldr", "")
    item.ai_summary = data["summary"]
    item.ai_why = data.get("why_it_matters", "")
    item.location = data.get("location", "")
    item.tags = data.get("tags", []) or []
    if data.get("focus_tags"):
        # Merge the model's tags with what the keyword pass already found.
        merged = set(item.focus) | set(data["focus_tags"])
        item.focus = [k for k in FOCUS_AREAS if k in merged]
    item.ai_provider = provider


# --- CLI backend (Claude Code; no API key) --------------------------------

def _cli_available() -> bool:
    return shutil.which("claude") is not None


def _enrich_cli(item: Item, model: str) -> None:
    cmd = [
        "claude", "-p", _build_prompt(item),
        "--output-format", "json",
        "--json-schema", json.dumps(_SCHEMA),
        "--append-system-prompt", _SYSTEM,
        "--model", model,
    ]
    proc = ai.run("enrich", cmd, timeout=CLI_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:200] or "claude CLI failed")
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(envelope.get("result", "CLI returned is_error"))
    data = envelope.get("structured_output")
    if not data:
        raise RuntimeError("CLI returned no structured_output")
    _apply(item, data, "claude-cli")


# --- API backend (Anthropic SDK) ------------------------------------------

def _api_available() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def _enrich_api(item: Item, model: str) -> None:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        thinking={"type": "adaptive"},
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": _SCHEMA}},
        system=_SYSTEM,
        messages=[{"role": "user", "content": _build_prompt(item)}],
    )
    text = next(b.text for b in resp.content if b.type == "text")
    _apply(item, json.loads(text), "claude-api")


# --- Timeline research (CLI + web search) ---------------------------------
# Builds a cited, chronological history for a story (e.g. a development plan)
# by letting the Claude Code CLI use its WebSearch/WebFetch tools. Output is
# schema-constrained so every event carries a real source URL.

_TIMELINE_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},      # YYYY, YYYY-MM, or YYYY-MM-DD
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["date", "title", "detail", "source_url"],
                "additionalProperties": False,
            },
        },
        "summary": {"type": "string"},   # short narrative + any gaps/caveats
    },
    "required": ["events", "summary"],
    "additionalProperties": False,
}

_TIMELINE_SYSTEM = (
    "You are a local-news researcher for Chesterfield County, Virginia. "
    "Use web search to reconstruct the factual history of a project or policy. "
    "ONLY include an event if you found a real, working source URL for it via "
    "search — never invent dates, case numbers, or URLs. Prefer official county "
    "sources (chesterfield.gov, planning/Board of Supervisors agendas & minutes) "
    "and reputable local news. If you can't find much, return the few verifiable "
    "events you did find and explain the gaps in 'summary'."
)


def research_timeline(topic: str, model: str = MODEL) -> dict:
    """Return {'events': [...], 'summary': str} for a story topic."""
    prompt = (
        f"Research the history of this Chesterfield County item and build a "
        f"chronological timeline:\n\n{topic}\n\n"
        "Search for the rezoning/case number, planning commission and Board of "
        "Supervisors actions, groundbreakings/openings, and prior news coverage. "
        "Order events oldest-to-newest. Each event needs date, title, a one-line "
        "detail, and the source_url you found it at."
    )
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(_TIMELINE_SCHEMA),
        "--append-system-prompt", _TIMELINE_SYSTEM,
        "--allowedTools", "WebSearch", "WebFetch",
        "--model", model,
    ]
    proc = ai.run("enrich", cmd, timeout=TIMELINE_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:300] or "claude CLI failed")
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(envelope.get("result", "CLI returned is_error"))
    data = envelope.get("structured_output")
    if not data:
        raise RuntimeError("CLI returned no structured_output")
    return data


# --- Full article (web-grounded: TL;DR + story + perspectives + timeline) --
# One web-research CLI call produces the whole long-form treatment. The two
# perspective fields are explicitly BALANCED, clearly-editorial "cases" — never
# fabricated quotes from real people.

_ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "tldr": {"type": "string"},
        "quick_facts": {
            "type": "object",
            "properties": {
                "who": {"type": "string"},
                "what": {"type": "string"},
                "when": {"type": "string"},
                "where": {"type": "string"},
            },
            "required": ["who", "what", "when", "where"],
            "additionalProperties": False,
        },
        "key_players": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                },
                "required": ["name", "role"],
                "additionalProperties": False,
            },
        },
        "detail": {"type": "string"},        # 2-4 short paragraphs, \n\n separated
        "case_for": {"type": "string"},       # the optimistic / supportive case
        "case_against": {"type": "string"},   # the critical / cautionary case
        "why_it_matters": {"type": "string"},
        "location": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "places": {"type": "array", "items": {"type": "string"}},
        "key_dates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "what": {"type": "string"},
                },
                "required": ["date", "what"],
                "additionalProperties": False,
            },
        },
        "related_links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["title", "url"],
                "additionalProperties": False,
            },
        },
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["date", "title", "detail", "source_url"],
                "additionalProperties": False,
            },
        },
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": ["title", "url"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["tldr", "quick_facts", "key_players", "detail", "case_for",
                 "case_against", "why_it_matters", "location", "tags", "places",
                 "key_dates", "related_links", "events", "sources"],
    "additionalProperties": False,
}

_ARTICLE_SYSTEM = (
    "You are a local-news writer for Chesterfield County, Virginia. Use web "
    "search to ground everything in real, verifiable facts — never invent "
    "dates, figures, names, case numbers, or URLs. Write clear, neutral copy. "
    "STYLE RULE (important): do NOT use em dashes or en dashes (the characters "
    "'—' or '–') anywhere in any field of your output. Rewrite with commas, "
    "periods, parentheses, or colons instead. Use a plain hyphen only inside "
    "hyphenated words. "
    "Provide 'case_for' and 'case_against' for MOST stories — readers value "
    "seeing both sides, and a fair pro/con on the real tradeoffs is a core "
    "feature of this publication. Write them for policy, budgets, development, "
    "rezoning, infrastructure (roads, roundabouts, projects), public services, "
    "programs, regulations, events, business, community initiatives, and county "
    "decisions. RETURN EMPTY STRINGS for BOTH ONLY when presenting a 'pro' would "
    "be tasteless or offensive: deaths, fatal accidents, violent crime and its "
    "victims, missing persons, serious injuries, tragedies, grief, or medical "
    "emergencies involving named individuals. When you write them, make them "
    "FAIR, balanced perspectives on the genuine tradeoffs — clearly-labeled "
    "editorial framings, NOT quotes attributed to real people; do not fabricate "
    "quotations or attribute opinions to named individuals. Prefer official "
    "county sources "
    "(chesterfield.gov, Planning, Board of Supervisors agendas/minutes) and "
    "reputable local news, and cite them. If facts are thin, say so plainly "
    "rather than filling gaps with speculation."
)


def write_article(topic: str, model: str = MODEL) -> dict:
    """Web-grounded long-form treatment for a story. Returns a dict matching
    _ARTICLE_SCHEMA (tldr, detail, case_for, case_against, why_it_matters,
    events, sources)."""
    prompt = (
        f"Research and write a fuller article for this Chesterfield County "
        f"story:\n\n{topic}\n\n"
        "Produce:\n"
        "- tldr: one-sentence gist\n"
        "- quick_facts: an object with who/what/when/where — each a SHORT "
        "phrase grounded in real, verified facts (who is involved, what is "
        "happening, when, and where). Use an empty string \"\" for any field "
        "that is genuinely unknown or not applicable; never guess or fabricate\n"
        "- key_players: the people and organizations central to the story, each "
        "as {name, role} (their role in the story). Only include real, verified "
        "names/orgs; return an empty array if none can be confirmed\n"
        "- detail: 2-4 short paragraphs giving the full story WITH real "
        "historical/background context (separate paragraphs with a blank line)\n"
        "- case_for / case_against: a fair pro and con on the genuine tradeoffs "
        "— include for MOST stories (policy, development, infrastructure, "
        "services, programs, events, business, community, county decisions). "
        "Return \"\" for BOTH ONLY when a 'pro' would be tasteless: deaths, fatal "
        "accidents, violent crime/victims, missing persons, serious injury, "
        "tragedy, or grief\n"
        "- why_it_matters: one or two sentences on impact to residents\n"
        "- location: ONE single specific place (one street, intersection, "
        "address, park, school, or facility in Chesterfield County). Empty "
        "string if no specific place OR the story covers multiple locations — "
        "do NOT list several places\n"
        "- tags: 4-8 specific topical/entity tags (people, places, "
        "organizations, neighborhoods, topics)\n"
        "- places: notable places named in the story (parks, roads, schools, "
        "venues) — these can each be mapped/linked\n"
        "- key_dates: important upcoming or scheduled dates/events as "
        "{date, what} (meetings, hearings, openings, deadlines)\n"
        "- related_links: important links a reader should follow for more — "
        "official county pages, agendas, registration, related coverage — as "
        "{title, url} (real URLs only)\n"
        "- events: a chronological timeline (date, title, one-line detail, "
        "source_url) of how this developed\n"
        "- sources: the key sources you cited (title, url)"
    )
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--json-schema", json.dumps(_ARTICLE_SCHEMA),
        "--append-system-prompt", _ARTICLE_SYSTEM,
        "--allowedTools", "WebSearch", "WebFetch",
        "--model", model,
    ]
    proc = ai.run("enrich", cmd, timeout=TIMELINE_TIMEOUT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:300] or "claude CLI failed")
    envelope = json.loads(proc.stdout)
    if envelope.get("is_error"):
        raise RuntimeError(envelope.get("result", "CLI returned is_error"))
    data = envelope.get("structured_output")
    if not data:
        raise RuntimeError("CLI returned no structured_output")
    return data


# --- Extractive fallback ---------------------------------------------------

def _enrich_extractive(item: Item) -> None:
    item.ai_headline = item.title
    body = _strip_html(item.raw_summary)
    sentences = re.split(r"(?<=[.!?])\s+", body)
    item.ai_tldr = (sentences[0].strip() if sentences else "") or item.title
    item.ai_summary = " ".join(sentences[:2]).strip() or item.title
    item.ai_why = ""  # the LLM step adds this; extractive leaves it for the editor
    item.ai_provider = "extractive"


# --- Dispatcher ------------------------------------------------------------

def enrich(item: Item, backend: str = "auto", model: str = MODEL) -> Item:
    """backend: 'auto' (cli -> api -> extractive), 'cli', 'api', or 'off'."""
    if backend in ("auto", "cli") and _cli_available():
        try:
            _enrich_cli(item, model)
            return item
        except Exception as e:
            print(f"  ! claude CLI enrich failed ({e}); falling back")
    if backend in ("auto", "api") and _api_available():
        try:
            _enrich_api(item, model)
            return item
        except Exception as e:
            print(f"  ! claude API enrich failed ({e}); falling back")
    _enrich_extractive(item)
    return item
