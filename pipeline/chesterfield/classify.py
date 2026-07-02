"""Relevance filtering + focus-area tagging (deterministic, no LLM).

This runs on every item before the (optional, paid) LLM step, so the cheap
keyword pass does the bulk filtering and the LLM only sees things worth
spending tokens on.
"""
from __future__ import annotations

import re

from .models import Item
from .sources import FOCUS_AREAS, CHESTERFIELD_PLACES


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "").replace("&nbsp;", " ").strip()


# There is also a Chesterfield in Derbyshire, England (and others in the US).
# Broad "Chesterfield" searches pull in UK stories that mention our place name
# but are clearly about the British town. Reject anything with strong UK markers.
_UK_MARKERS = re.compile(
    r"\b(derbyshire|england|scotland|wales|united kingdom|"
    r"crown court|magistrates|sheffield|nottingham|"
    r"chesterfield fc|spireites|"
    r"borough council|parish council|county council|town hall|"
    r"staveley|brimington|whittington|hasland|dronfield|bolsover|"
    r"clay cross|holme hall|peak district|high peak)\b")


def _looks_uk(hay: str) -> bool:
    return "£" in hay or _UK_MARKERS.search(hay) is not None


# There is ALSO a Chesterfield County in SOUTH CAROLINA (county seat Chesterfield,
# towns Pageland/Cheraw/McBee). Broad "Chesterfield County" news feeds repeatedly
# pull SC crime stories that read as local because they literally say "Chesterfield
# County." Reject anything with clear South Carolina markers. (Deliberately avoids
# ambiguous tokens like "Jefferson" — Jefferson Davis Hwy is in Chesterfield, VA.)
_SC_MARKERS = re.compile(
    r"(south carolina|\bpageland\b|\bcheraw\b|\bmcbee\b|\bmount croghan\b|"
    r"cambo streater|south carolina law enforcement|"
    r"\bwbtv\b|\bwcnc\b|\bwsoc\b|\bwltx\b)")


def _looks_sc(hay: str) -> bool:
    return _SC_MARKERS.search(hay) is not None


def is_relevant(item: Item, source: dict) -> bool:
    """County-government & weather sources are relevant by definition.
    Broad sources must mention a Chesterfield place name. Anything with clear
    UK markers (the Chesterfield in Derbyshire, England) or South Carolina markers
    (Chesterfield County, SC) is rejected outright."""
    hay = f"{item.title} {_strip_html(item.raw_summary)}".lower()
    if _looks_uk(hay) or _looks_sc(hay):
        return False
    if not source.get("geo_filter", True):
        return True
    return any(place in hay for place in CHESTERFIELD_PLACES)


def tag_focus(item: Item) -> list[str]:
    """Union of the source's default tags and any keyword-matched areas."""
    tags = set(item.focus)
    hay = f"{item.title} {_strip_html(item.raw_summary)}".lower()
    for key, (_label, triggers) in FOCUS_AREAS.items():
        if any(t in hay for t in triggers):
            tags.add(key)
    # Keep a stable, defined order.
    return [k for k in FOCUS_AREAS if k in tags]
