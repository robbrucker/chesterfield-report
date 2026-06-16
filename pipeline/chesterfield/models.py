"""Core data model: a single ingested news item."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class Item:
    """One piece of content from any source, at any pipeline stage."""

    source_id: str
    source_name: str
    title: str
    url: str
    # Raw description/summary as provided by the feed (may contain HTML).
    raw_summary: str = ""
    # Original publish time from the source, ISO 8601 if known.
    published: str = ""
    # Editorial focus tags (keys from sources.FOCUS_AREAS).
    focus: list[str] = field(default_factory=list)
    # Free-form topical/entity tags (people, places, orgs, topics) — richer
    # than the fixed focus areas. Used for cross-linking and discovery.
    tags: list[str] = field(default_factory=list)
    license: str = "press"  # "government" (free to use) | "press" (link-only)
    # Editorial track: "" = local Chesterfield news; "regional" = Virginia /
    # regional news that affects residents but isn't Chesterfield-specific.
    track: str = ""
    # Geocodable place for this story ("" if not tied to a location) + coords.
    location: str = ""
    lat: str = ""
    lon: str = ""
    # Media: hero image / video thumbnail URL, and a video watch URL if any.
    image: str = ""
    video_url: str = ""
    media_kind: str = ""   # "" | "video"

    # --- Filled in by the enrich step -------------------------------------
    ai_headline: str = ""
    ai_tldr: str = ""         # one-sentence "the gist"
    ai_summary: str = ""
    ai_why: str = ""          # why it matters to Chesterfield
    ai_provider: str = ""     # "claude" | "extractive"

    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def uid(self) -> str:
        """Stable dedup key. URL is the natural identity; fall back to title."""
        basis = (self.url or self.title).strip().lower()
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]

    @property
    def slug(self) -> str:
        base = self.ai_headline or self.title
        s = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
        return s[:60] or self.uid

    def to_row(self) -> dict:
        d = asdict(self)
        d["uid"] = self.uid
        d["focus"] = ",".join(self.focus)
        d["tags"] = ",".join(self.tags)
        return d
