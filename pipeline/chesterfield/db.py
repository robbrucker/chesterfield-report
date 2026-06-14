"""SQLite-backed seen-store + state.

The database's job is deduplication and tracking what we've already drafted —
NOT serving the site. The review queue is the markdown files in content/drafts;
published content is content/published. This keeps the human-in-the-loop step
in plain files you can edit in any editor and version with git.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Item

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    uid          TEXT PRIMARY KEY,
    source_id    TEXT,
    source_name  TEXT,
    title        TEXT,
    url          TEXT,
    raw_summary  TEXT,
    published    TEXT,
    focus        TEXT,
    tags         TEXT,
    license      TEXT,
    location     TEXT,
    lat          TEXT,
    lon          TEXT,
    image        TEXT,
    video_url    TEXT,
    media_kind   TEXT,
    ai_headline  TEXT,
    ai_tldr      TEXT,
    ai_summary   TEXT,
    ai_why       TEXT,
    ai_provider  TEXT,
    fetched_at   TEXT,
    status       TEXT DEFAULT 'new'   -- new | drafted | skipped
);
"""


class Store:
    def __init__(self, path: str | Path):
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        # Lightweight migration for DBs created before a column was added.
        have = {r[1] for r in self.conn.execute("PRAGMA table_info(items)")}
        for col in ("ai_tldr", "location", "lat", "lon", "image", "video_url",
                    "media_kind", "tags"):
            if col not in have:
                self.conn.execute(f"ALTER TABLE items ADD COLUMN {col} TEXT")
        self.conn.commit()

    def seen(self, uid: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM items WHERE uid = ?", (uid,))
        return cur.fetchone() is not None

    def add(self, item: Item, status: str = "new") -> None:
        row = item.to_row()
        row["status"] = status
        cols = ",".join(row.keys())
        placeholders = ",".join("?" for _ in row)
        self.conn.execute(
            f"INSERT OR IGNORE INTO items ({cols}) VALUES ({placeholders})",
            list(row.values()),
        )
        self.conn.commit()

    def mark(self, uid: str, status: str) -> None:
        self.conn.execute("UPDATE items SET status = ? WHERE uid = ?", (status, uid))
        self.conn.commit()

    def counts(self) -> dict:
        cur = self.conn.execute(
            "SELECT status, COUNT(*) c FROM items GROUP BY status"
        )
        return {r["status"]: r["c"] for r in cur.fetchall()}
