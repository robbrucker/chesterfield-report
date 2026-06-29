"""Topic-dedup engine: merge multiple stories covering the SAME event into one.

A newsroom pipeline often publishes several stories about a single underlying
event from different outlets/angles (e.g. the officer-shooting coverage that
spawned separate pieces on the shooting, the charges, the K-9's death, the
honoring of the K-9, and a GoFundMe). This module finds those clusters,
picks the most complete story as the *canonical*, folds the others' source
links into it, and moves the merged-in files aside (reversibly).

Stdlib only. Clustering is deliberately CONSERVATIVE: we want precision over
recall, so two stories merge only when there is strong same-event evidence
(shared distinctive named-entity tags AND/OR very high headline overlap AND
a shared focus area AND publish dates within a short window). Two unrelated
rezonings, or two different roundabouts, must NEVER cluster.

Usage:
    from chesterfield import dedup
    dedup.dry_run()                 # inspect, mutates nothing
    plan = dedup.plan(dedup.find_clusters())
    dedup.apply(plan)               # actually merge + move files
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

# We import these from render so the two stay in lockstep on where content
# lives and how frontmatter is parsed.
from .render import PUBLISHED, _parse_frontmatter, slugify  # noqa: F401  (slugify re-exported for callers)

ROOT = PUBLISHED.parents[1]
MERGED = ROOT / "content" / "merged"


# --------------------------------------------------------------------------- #
# Token / tag normalization
# --------------------------------------------------------------------------- #

# Words that carry no same-event signal: pure stopwords plus generic local-news
# filler that appears across nearly every Chesterfield story.
_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "for", "with",
    "after", "amid", "as", "by", "from", "into", "over", "set", "see", "sees",
    "is", "are", "was", "were", "be", "been", "this", "that", "these", "those",
    "new", "two", "one", "three", "four", "five", "up", "out", "off", "since",
    "near", "across", "ahead", "join", "joins", "honor", "honors", "honored",
}

# Generic place/agency words that recur constantly and would create false
# topical links if treated as significant.
_GENERIC = {
    "chesterfield", "county", "police", "department", "virginia", "va",
    "local", "news", "community", "officials", "officers", "officer",
    "residents", "resident", "area", "road", "street", "rd", "st", "dot",
    "vdot", "government", "board", "supervisors", "commission",
}

_STRIP = _STOPWORDS | _GENERIC

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9\-]*")


def _summary_text(body: str) -> str:
    """The gist of a story — its TL;DR sentence plus the lead of the body. Used
    for content-level similarity when two write-ups of the same event are
    headlined and tagged differently across sources (e.g. three versions of the
    same toddler-prosthetic story), which headline-token / named-tag overlap
    alone misses."""
    body = body or ""
    parts = []
    m = re.search(r"\*\*TL;DR:\*\*\s*(.+)", body)
    if m:
        parts.append(m.group(1))
    m = re.search(r"^##\s+The story\b(.*?)(?=^##\s)", body, re.MULTILINE | re.DOTALL)
    if m:
        parts.append(m.group(1)[:700])
    return " ".join(parts)


def _sig_tokens(text: str) -> set[str]:
    """Significant lowercase word tokens (stopwords + generic words removed)."""
    out = set()
    for w in _WORD_RE.findall((text or "").lower()):
        w = w.strip("-")
        if len(w) < 3 or w in _STRIP:
            continue
        out.add(w)
    return out


def _parse_tags(raw: str) -> list[str]:
    """Parse a YAML-ish inline-list tag value: `[a, b, c]` -> ['a','b','c']."""
    raw = (raw or "").strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    parts = [p.strip().strip('"').strip("'") for p in raw.split(",")]
    return [p for p in parts if p]


def _norm_tag(tag: str) -> str:
    """Normalize a tag for comparison: lowercase, collapse separators."""
    return re.sub(r"[\s_\-]+", " ", tag.strip().lower()).strip()


# Tags that are highly distinctive of a specific event: multi-word proper nouns
# and named people. A *shared* distinctive tag between two stories is strong
# same-event evidence. We exclude generic single-word tags from this set.
def _distinctive_tags(tags: list[str]) -> set[str]:
    out = set()
    for t in tags:
        n = _norm_tag(t)
        # significant words within the tag, generic words removed
        words = [w for w in n.split() if w not in _STRIP and len(w) >= 2]
        if not words:
            continue
        # Multi-word named entity (e.g. "gary shaw", "k 9 knight",
        # "jacob clark", "river city sportsplex") OR a clearly specific single
        # significant word. Drop tags that are entirely generic.
        if len(words) >= 2:
            out.add(" ".join(words))
    return out


# --------------------------------------------------------------------------- #
# Story model
# --------------------------------------------------------------------------- #

class _Story:
    __slots__ = (
        "path", "meta", "body", "headline", "focus", "tags",
        "dist_tags", "head_tokens", "summary_tokens", "date", "n_sources",
        "has_story", "body_len",
    )

    def __init__(self, path: Path):
        self.path = path
        text = path.read_text(encoding="utf-8")
        self.meta, self.body = _parse_frontmatter(text)
        self.headline = self.meta.get("headline", path.stem)
        self.focus = {f.strip() for f in _parse_tags(self.meta.get("focus", "")) if f.strip()}
        self.tags = _parse_tags(self.meta.get("tags", ""))
        self.dist_tags = _distinctive_tags(self.tags)
        self.head_tokens = _sig_tokens(self.headline)
        self.summary_tokens = _sig_tokens(_summary_text(self.body))
        self.date = _parse_date(self.meta.get("published", "")) or _date_from_name(path)
        self.n_sources = self._count_sources()
        self.has_story = bool(re.search(r"^##\s+The story\b", self.body, re.MULTILINE))
        self.body_len = len(self.body)

    def _count_sources(self) -> int:
        m = re.search(r"^##\s+Sources\b", self.body, re.MULTILINE)
        if not m:
            return 0
        section = self.body[m.end():]
        nxt = re.search(r"^##\s+", section, re.MULTILINE)
        if nxt:
            section = section[: nxt.start()]
        return len(re.findall(r"^\s*-\s+\[", section, re.MULTILINE))


def _parse_date(s: str):
    s = (s or "").strip().strip('"')
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
        if m:
            try:
                return datetime.fromisoformat(m.group(1)).date()
            except ValueError:
                return None
    return None


def _date_from_name(path: Path):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        try:
            return datetime.fromisoformat(m.group(1)).date()
        except ValueError:
            return None
    return None


# --------------------------------------------------------------------------- #
# Similarity
# --------------------------------------------------------------------------- #

def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


_DATE_WINDOW_DAYS = 14


def _same_event(a: _Story, b: _Story, threshold: float) -> bool:
    """CONSERVATIVE same-event test. Returns True only on strong evidence.

    Evidence combined:
      * shared distinctive named-entity tags (strongest signal),
      * headline significant-token Jaccard overlap,
      * a shared focus area,
      * publish dates within a short window.
    """
    # Must be temporally close. Same-event coverage clusters in time.
    if a.date and b.date:
        if abs((a.date - b.date).days) > _DATE_WINDOW_DAYS:
            return False

    # Must share at least one focus area (e.g. both Police). This is a cheap
    # guard against cross-topic merges.
    if a.focus and b.focus and not (a.focus & b.focus):
        return False

    shared_dist = a.dist_tags & b.dist_tags
    head_j = _jaccard(a.head_tokens, b.head_tokens)

    # Signal 1: two or more shared distinctive named-entity tags is, on its own,
    # near-conclusive same-event evidence (e.g. "gary shaw" + "k 9 knight").
    if len(shared_dist) >= 2:
        return True

    # Signal 2: one shared distinctive named-entity tag (e.g. "k 9 knight")
    # plus some corroborating headline overlap.
    if len(shared_dist) >= 1 and head_j >= 0.10:
        return True

    # Signal 3: no shared named entity, but the headlines overlap very heavily
    # on significant words AND tag sets overlap substantially. This catches
    # rare cases where two outlets used the same wording. Kept strict so that
    # generic same-topic stories (roundabouts, rezonings) do not trip it.
    tag_j = _jaccard(
        {_norm_tag(t) for t in a.tags}, {_norm_tag(t) for t in b.tags}
    )
    if head_j >= max(threshold, 0.5) and tag_j >= 0.30:
        return True

    # Signal 4: no shared named entity and headlines/tags barely overlap, but
    # the stories describe the same thing — their TL;DR + lead content overlaps.
    # Catches the same event re-headlined across sources (e.g. three write-ups
    # of one toddler-prosthetic story, tagged only with generic descriptors).
    # Restricted to stories published the SAME DAY: same-event re-tellings land
    # together in time, whereas a multi-week saga (officer shooting, data center)
    # shares vocabulary across many days and would over-chain via union-find if
    # we used the wider window. The QA editor still adjudicates every cluster.
    if a.date and b.date and a.date == b.date:
        if _jaccard(a.summary_tokens, b.summary_tokens) >= 0.22:
            return True

    return False


# --------------------------------------------------------------------------- #
# Clustering (union-find over the same-event graph)
# --------------------------------------------------------------------------- #

def find_clusters(threshold: float = 0.5) -> list[list[Path]]:
    """Cluster content/published/*.md by same underlying event.

    Returns groups of 2+ Paths that cover the same event. Conservative: only
    clear same-event matches cluster; merely same-topic stories do not.
    """
    files = sorted(PUBLISHED.glob("*.md"))
    stories = [_Story(p) for p in files]
    n = len(stories)

    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if _same_event(stories[i], stories[j], threshold):
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    clusters = [
        [stories[i].path for i in idxs]
        for idxs in groups.values()
        if len(idxs) >= 2
    ]
    # Stable ordering: largest clusters first, then by earliest path name.
    clusters.sort(key=lambda g: (-len(g), str(min(g))))
    return clusters


# --------------------------------------------------------------------------- #
# Planning
# --------------------------------------------------------------------------- #

def _canonical_rank(s: _Story) -> tuple:
    """Higher is better: prefer 'The story' section, more sources, longer body."""
    return (1 if s.has_story else 0, s.n_sources, s.body_len)


def plan(clusters: list[list[Path]]) -> list[dict]:
    """For each cluster choose the most complete story as canonical.

    Returns [{canonical: Path, merge: [Path,...], headline: str}].
    """
    out = []
    for group in clusters:
        stories = [_Story(p) for p in group]
        stories.sort(key=_canonical_rank, reverse=True)
        canonical = stories[0]
        merge = [s.path for s in stories[1:]]
        out.append({
            "canonical": canonical.path,
            "merge": merge,
            "headline": canonical.headline,
        })
    return out


# --------------------------------------------------------------------------- #
# Applying
# --------------------------------------------------------------------------- #

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def _existing_source_urls(body: str) -> set[str]:
    return {m.group(2) for m in _LINK_RE.finditer(body)}


def _source_line(story: _Story) -> str | None:
    """A markdown bullet linking the story's headline to its source_url."""
    url = (story.meta.get("source_url") or "").strip().strip('"')
    if not url:
        return None
    head = story.headline.strip().strip('"') or story.path.stem
    return f"- [{head}]({url})"


def _append_sources(canonical_path: Path, merge_paths: list[Path]) -> int:
    """Fold merged-in stories' source links into the canonical file.

    Adds them under the existing `## Sources` section (or a new
    `## Also reported` section). Deduped on URL. Returns count of links added.
    """
    text = canonical_path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    have = _existing_source_urls(text)

    new_lines: list[str] = []
    for mp in merge_paths:
        s = _Story(mp)
        line = _source_line(s)
        if not line:
            continue
        url = _LINK_RE.search(line).group(2)
        if url in have:
            continue
        have.add(url)
        new_lines.append(line)

    if not new_lines:
        return 0

    # Find an insertion point. Prefer extending an existing "## Sources"
    # section; otherwise append a fresh "## Also reported" section.
    m = re.search(r"^##\s+Sources\b.*$", text, re.MULTILINE)
    if m:
        # Determine the end of the Sources section.
        after = text[m.end():]
        nxt = re.search(r"^##\s+", after, re.MULTILINE)
        insert_at = m.end() + (nxt.start() if nxt else len(after))
        chunk = "\n" + "\n".join(new_lines) + "\n"
        # Trim a trailing blank gap so bullets stay contiguous.
        head = text[:insert_at].rstrip("\n")
        tail = text[insert_at:]
        new_text = head + "\n" + "\n".join(new_lines) + "\n" + ("\n" + tail.lstrip("\n") if tail.strip() else "\n")
    else:
        section = "\n\n## Also reported\n\n" + "\n".join(new_lines) + "\n"
        new_text = text.rstrip("\n") + "\n" + section

    canonical_path.write_text(new_text, encoding="utf-8")
    return len(new_lines)


def apply(plan: list[dict]) -> int:
    """Execute a plan: fold sources into canonicals, move merge-ins to merged/.

    Returns the number of files merged away (moved out of published/).
    Reversible: merged files are MOVED, never deleted.
    """
    MERGED.mkdir(parents=True, exist_ok=True)
    moved = 0
    for cluster in plan:
        canonical: Path = cluster["canonical"]
        merge: list[Path] = cluster["merge"]
        merge = [p for p in merge if p.exists() and p != canonical]
        if not merge:
            continue
        _append_sources(canonical, merge)
        for p in merge:
            dest = MERGED / p.name
            if dest.exists():
                dest = MERGED / f"{p.stem}.dup{p.suffix}"
            p.rename(dest)
            moved += 1
    return moved


# --------------------------------------------------------------------------- #
# Dry run
# --------------------------------------------------------------------------- #

def dry_run(threshold: float = 0.5) -> list[dict]:
    """Print each detected cluster (canonical + merge-ins) and counts.

    Mutates nothing. Returns the plan for programmatic inspection.
    """
    clusters = find_clusters(threshold)
    the_plan = plan(clusters)

    if not the_plan:
        print("No same-event clusters found among", len(list(PUBLISHED.glob("*.md"))), "published stories.")
        return the_plan

    total_merge = sum(len(c["merge"]) for c in the_plan)
    print(f"Found {len(the_plan)} cluster(s) covering the same event "
          f"({total_merge} file(s) would be merged away):\n")

    for i, c in enumerate(the_plan, 1):
        can = _Story(c["canonical"])
        print(f"Cluster {i}: {len(c['merge']) + 1} stories")
        print(f"  ⭐ {c['headline']}")
        print(f"     {c['canonical'].name}  "
              f"(sources={can.n_sources}, has_story={can.has_story}, body={can.body_len})")
        for mp in c["merge"]:
            ms = _Story(mp)
            print(f"     + {ms.headline}")
            print(f"       {mp.name}  (sources={ms.n_sources}, body={ms.body_len})")
        print()

    print(f"Summary: {len(the_plan)} cluster(s), {total_merge} file(s) to merge, "
          f"{len(the_plan)} canonical(s) retained.")
    return the_plan
