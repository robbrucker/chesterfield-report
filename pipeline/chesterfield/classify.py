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


def is_relevant(item: Item, source: dict) -> bool:
    """County-government & weather sources are relevant by definition.
    Broad sources must mention a Chesterfield place name."""
    if not source.get("geo_filter", True):
        return True
    hay = f"{item.title} {_strip_html(item.raw_summary)}".lower()
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
