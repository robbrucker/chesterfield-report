"""Auto-expire transient weather alerts.

NWS watches / warnings / advisories are time-sensitive: a severe-thunderstorm
warning lives ~1 hour, a watch a few hours. They are real and worth publishing
*while active*, but once the window passes they are dead weight on the homepage
(and three near-identical "severe thunderstorm" headlines after one storm reads
as clutter, not coverage).

This module deterministically unpublishes those alerts once they are older than
EXPIRE_HOURS. It is conservative on purpose:

  * Only touches stories whose headline says watch / warning / advisory AND that
    are tagged as weather/NWS content. An evergreen weather *service* story
    ("County opens call center for winter-storm questions") has no alert verb in
    the headline, so it is never expired.
  * Reversible: expired files move to content/removed/ (same convention qa.py
    uses), never hard-deleted. Restore by moving the file back.

No AI, no network. Run before the build so expired alerts drop off the site.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from .render import PUBLISHED, _parse_frontmatter

# How long each alert type stays live, measured from its `published` timestamp.
# These mirror how NWS products actually behave: a warning is nearly over within
# an hour, a watch runs through the afternoon/evening, an advisory (heat, wind)
# can span a full day. Past the window the alert is dead weight on the homepage.
EXPIRE_HOURS_BY_TYPE = {
    "warning": 2,
    "watch": 8,
    "advisory": 24,
}
EXPIRE_HOURS = 12  # fallback if an alert type is somehow unrecognized

REMOVED = PUBLISHED.parent / "removed"

# Headline verbs that mark a story as a time-bound alert (not evergreen weather).
_ALERT_RE = re.compile(r"\b(watch|warning|advisory)\b", re.IGNORECASE)

# Frontmatter markers that confirm this is weather/NWS content.
_WEATHER_MARKERS = ("weather", "thunderstorm", "tornado", "flood",
                    "national weather service", "winter storm", "heat")


def _alert_type(meta: dict) -> str | None:
    """Return 'warning' / 'watch' / 'advisory' if this published item is a
    time-bound weather alert, else None (evergreen weather coverage)."""
    m = _ALERT_RE.search(meta.get("headline") or "")
    if not m:
        return None
    haystack = f"{meta.get('focus', '')} {meta.get('tags', '')}".lower()
    if not any(w in haystack for w in _WEATHER_MARKERS):
        return None
    return m.group(1).lower()


def _published_dt(meta: dict) -> datetime | None:
    """Parse the `published` ISO timestamp into an aware datetime, or None."""
    raw = (meta.get("published") or "").strip().strip('"')
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    # Treat a naive timestamp as UTC so the age math always works.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def prune_expired_alerts(now: datetime | None = None,
                         apply: bool = True) -> list[dict]:
    """Unpublish weather alerts past their per-type window. Reversible
    (-> content/removed/).

    Returns a list of {file, headline, type, age_hours} for each expired alert.
    With apply=False it reports without moving anything (dry run).
    """
    now = now or datetime.now(timezone.utc)
    expired: list[dict] = []

    for p in sorted(PUBLISHED.glob("*.md")):
        meta, _ = _parse_frontmatter(p.read_text(encoding="utf-8"))
        kind = _alert_type(meta)
        if kind is None:
            continue
        pub = _published_dt(meta)
        if pub is None:
            continue
        age = now - pub
        window = timedelta(hours=EXPIRE_HOURS_BY_TYPE.get(kind, EXPIRE_HOURS))
        if age <= window:
            continue  # still within its active window
        expired.append({
            "file": p.name,
            "headline": meta.get("headline", ""),
            "type": kind,
            "age_hours": round(age.total_seconds() / 3600, 1),
        })
        if apply:
            REMOVED.mkdir(parents=True, exist_ok=True)
            dest = REMOVED / p.name
            if dest.exists():
                dest = REMOVED / f"{p.stem}.dup{p.suffix}"
            p.rename(dest)

    return expired


def run(apply: bool = True) -> dict:
    """Entry point used by run.py / the cron pipeline."""
    expired = prune_expired_alerts(apply=apply)
    return {"expired": len(expired), "items": expired}
