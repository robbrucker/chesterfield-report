#!/usr/bin/env python3
"""Chesterfield local-news pipeline — command line entry point.

Commands:
  ingest    Fetch all sources -> filter -> tag -> enrich -> write drafts.
            --ai cli|api|auto|off   AI backend (default: auto = CLI if present)
            --no-ai                 same as --ai off (extractive only)
            --model <id>            e.g. claude-haiku-4-5 (cheaper via CLI)
  build     Render published markdown -> public/index.html.
  review    Render the drafts queue -> public/drafts.html (static, read-only).
  serve     Interactive review server with Approve/Reject/View/Edit buttons:
            python run.py serve   ->   http://localhost:8787
  promote   Move a draft to published (and set status: published).
  article   Rewrite a story as a full long-form article (web-grounded):
            TL;DR · the story w/ history · case for · case against ·
            why it matters · timeline · sources.
            python run.py article <file.md> [--model claude-haiku-4-5]
  timeline  Research + append a cited historical timeline only.
            python run.py timeline <file.md> [--model claude-haiku-4-5]
  status    Show counts.

The CLI backend uses your Claude Code login (no API key). Each item is a full
Claude Code session, so it's slower/pricier than the API — use --model
claude-haiku-4-5 to cut cost on bulk runs.

Typical loop:
  python run.py ingest        # pulls news, writes content/drafts/*.md
  # ...you review/edit drafts, then:
  python run.py promote 2026-06-06-some-headline.md
  python run.py build         # regenerate the site
  open ../public/index.html
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# Allow running as `python run.py` from the pipeline/ dir.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from chesterfield import classify, enrich as enrich_mod, fetch as fetch_mod, geo, render
from chesterfield import board as board_mod, maps as maps_mod
from chesterfield import meetings as meetings_mod
from chesterfield import dining as dining_mod
from chesterfield import neighborhoods as neighborhoods_mod
from chesterfield import business as business_mod
from chesterfield import serve as serve_mod
from chesterfield import newsletter as newsletter_mod, linkqueue as linkqueue_mod
from chesterfield import editor as editor_mod, alerts as alerts_mod, qa as qa_mod
from chesterfield import employees as employees_mod, dedup as dedup_mod
from chesterfield import expire as expire_mod
from chesterfield import taxes as taxes_mod
from chesterfield import schools as schools_mod
from chesterfield import cases as cases_mod
from chesterfield import school_board as school_board_mod
from chesterfield import events as events_mod
from chesterfield import things as things_mod
from chesterfield import housing as housing_mod
from chesterfield import letters as letters_mod
from chesterfield.db import Store
from chesterfield.sources import active_sources

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "pipeline" / "seen.db"

# --- Ingest freshness watermark -------------------------------------------
# Only ingest items published since we last looked, minus a 2h overlap so a
# slightly-late feed item at the boundary is still caught. This stops the
# Google News searches (which rank by relevance, not recency) from dragging in
# months-old stories. Already-published content is untouched.
WATERMARK = ROOT / "pipeline" / "last_ingest.txt"
INGEST_OVERLAP_HOURS = 48    # cutoff = last-run - this. Wide enough to catch the last ~2 days of
                            # genuinely-recent news (not just the last 6h), while dedup (seen.db) +
                            # the window still block the months-old Google News results.
FIRST_RUN_LOOKBACK_DAYS = 2  # if there's no watermark yet, only look back this far


def _parse_dt(s: str):
    """Parse an item's `published` (ISO 8601, or RFC822 fallback) to an aware
    datetime. Returns None if absent/unparseable."""
    s = (s or "").strip()
    if not s:
        return None
    dt = None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = parsedate_to_datetime(s)
        except (TypeError, ValueError):
            return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _ingest_cutoff() -> datetime:
    try:
        wm = datetime.fromisoformat(WATERMARK.read_text(encoding="utf-8").strip())
        if wm.tzinfo is None:
            wm = wm.replace(tzinfo=timezone.utc)
        return wm - timedelta(hours=INGEST_OVERLAP_HOURS)
    except (OSError, ValueError):
        return datetime.now(timezone.utc) - timedelta(days=FIRST_RUN_LOOKBACK_DAYS)


def _save_watermark() -> None:
    try:
        WATERMARK.write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    except OSError:
        pass


def _opt(args: list[str], flag: str, default: str) -> str:
    """Read `--flag value` from argv, else return default."""
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return default


def cmd_ingest(backend: str = "auto", model: str = "claude-haiku-4-5",
               limit: int | None = None) -> None:
    store = Store(DB_PATH)
    cap = f", limit {limit}" if limit else ""
    cutoff = _ingest_cutoff()
    print(f"AI backend: {backend} (model: {model}{cap})")
    print(f"Freshness: only items published since {cutoff:%Y-%m-%d %H:%M %Z} "
          f"(last run - {INGEST_OVERLAP_HOURS}h)")
    total_new = 0
    stale_skipped = 0
    for source in active_sources():
        if limit and total_new >= limit:
            print("(limit reached — stopping)")
            break
        print(f"→ {source['name']}")
        try:
            items = fetch_mod.fetch(source)
        except Exception as e:
            print(f"  ! fetch failed: {e}")
            continue
        new_here = 0
        for item in items:
            if limit and total_new >= limit:
                break
            if store.seen(item.uid):
                continue
            # Freshness gate: skip items older than the cutoff (mark seen so we
            # don't re-check them). Items with no/unparseable date are kept.
            dt = _parse_dt(item.published)
            if dt is not None and dt < cutoff:
                store.add(item, status="skipped")
                stale_skipped += 1
                continue
            if not classify.is_relevant(item, source):
                store.add(item, status="skipped")
                continue
            item.focus = classify.tag_focus(item)
            item.track = source.get("track", "")   # "" local | "regional"
            enrich_mod.enrich(item, backend=backend, model=model)
            path = render.write_draft(item)
            store.add(item, status="drafted")
            new_here += 1
            total_new += 1
            print(f"  + draft: {path.name}  [{item.ai_provider}] {item.focus}")
        print(f"  ({new_here} new of {len(items)})")
    _save_watermark()
    print(f"\nDone. {total_new} new drafts in content/drafts/ "
          f"({stale_skipped} skipped as stale).")
    if total_new:
        print("Review them, then: python run.py promote <file.md>")


def cmd_build() -> None:
    # Drop expired weather watches/warnings/advisories before rendering so passed
    # alerts don't pile up on the homepage. Reversible (-> content/removed/).
    exp = expire_mod.run(apply=True)
    if exp["expired"]:
        print(f"Expired {exp['expired']} stale weather alert(s) before build.")
    out = render.build_site()
    n = render.build_topics()
    render.build_digest()
    render.build_tip()
    render.build_subscribe()
    render.build_about()
    render.build_shoosmith()
    render.build_virginia()                        # regional track -> /virginia.html
    render.build_feed()
    map_out = maps_mod.build_map()
    board_out = board_mod.build_board()
    meetings_out = meetings_mod.build_meetings()  # graceful: [] -> still builds
    dining_mod.build_dining()                      # graceful: cached OSM data
    neighborhoods_mod.build_neighborhoods()        # directory from committed GIS data
    business_mod.build_business()                  # employers + independent directory
    taxes_mod.build_taxes()                        # county budget viz from committed data
    schools_mod.build_schools()                    # CCPS directory + map from committed data
    school_board_mod.build_school_board()          # School Board tracker
    cases_mod.build_cases()                        # live development/zoning cases (graceful on fetch fail)
    events_mod.build_events()                      # county events calendar (graceful on fetch fail)
    things_mod.build_things()                      # Ticketmaster live events -> /things-to-do.html
    housing_mod.build_affordable()                 # affordable-housing finder from committed data
    housing_mod.build_directory()                  # market-rate apartment community directory
    from chesterfield import seo as seo_mod
    seo_mod.build_seo()
    letters_mod.build_form()
    # employees_mod.build()  # salary lookup shelved (county data is FOIA-only)
    print(f"Built {out}")
    print(f"Built {n} topic pages, digest.html (+ digest.md), tip.html")
    print(f"Built {map_out.name}, {board_out.name}, {meetings_out.name}, "
          f"robots.txt, sitemap.xml")


def cmd_preview() -> None:
    out = render.build_preview()
    n = len(list(render.DRAFTS.glob("*.md")))
    print(f"Built draft preview: {out}  ({n} drafts)")
    print("Open it at  http://localhost:8000/drafts.html  (or open the file directly).")
    print("Approve:  python run.py promote <file.md>   Reject: delete the file in content/drafts/")


def cmd_promote(name: str) -> None:
    src = render.DRAFTS / name
    if not src.exists():
        print(f"Draft not found: {src}")
        return
    text = src.read_text(encoding="utf-8").replace("status: draft", "status: published", 1)
    render.PUBLISHED.mkdir(parents=True, exist_ok=True)
    (render.PUBLISHED / name).write_text(text, encoding="utf-8")
    src.unlink()
    print(f"Promoted {name} -> content/published/. Run: python run.py build")


def cmd_letter(subject: str, name: str = "", anonymous: bool = False,
               neighborhood: str = "") -> None:
    """Turn a received Letter to the Editor into an Opinion draft for review.
    Paste the letter body on stdin (end with Ctrl-D), or pipe a file in."""
    body = sys.stdin.read()
    if not body.strip():
        print("No letter body. Usage: python run.py letter \"Subject\" "
              "[--name \"Jane Doe\"] [--neighborhood Midlothian] [--anon] < letter.txt")
        return
    path = letters_mod.create_draft(subject, body, name=name,
                                    anonymous=anonymous, neighborhood=neighborhood)
    print(f"Created Opinion draft: {path.name}")
    print("Review/approve at http://localhost:8787 (it will publish as Opinion).")


def cmd_tidy() -> None:
    """Clear low-value unenriched 'extractive' stub drafts (the day-one import)
    from the review queue. They stay 'seen' in the DB, so they won't re-ingest."""
    removed = 0
    for p in render.DRAFTS.glob("*.md"):
        meta, _ = render._parse_frontmatter(p.read_text(encoding="utf-8"))
        if meta.get("ai_provider") == "extractive":
            p.unlink()
            removed += 1
    print(f"Tidied {removed} unenriched stub draft(s) from the queue.")


def cmd_timeline(name: str, model: str = "claude-haiku-4-5") -> None:
    """Research and append a cited historical timeline to a draft/published file."""
    path = render.DRAFTS / name
    if not path.exists():
        path = render.PUBLISHED / name
    if not path.exists():
        print(f"Not found in drafts or published: {name}")
        return
    meta, body = render._parse_frontmatter(path.read_text(encoding="utf-8"))
    headline = meta.get("headline") or name
    # Give the researcher the headline + the summary paragraph as context.
    summary = next((ln for ln in body.splitlines() if ln and not ln.startswith("#")), "")
    topic = f"{headline}\n\nContext: {summary}\nSource: {meta.get('source_url','')}"
    print(f"Researching timeline for: {headline}\n(model: {model}, this runs web searches…)")
    try:
        data = enrich_mod.research_timeline(topic, model=model)
    except Exception as e:
        print(f"Timeline research failed: {e}")
        return
    if render.append_timeline(path, data):
        print(f"Added {len(data.get('events', []))} events to {path.name}")
        print("Run: python run.py build")
    else:
        print("Timeline already present; left unchanged.")


def cmd_article(name: str, model: str = "claude-haiku-4-5") -> None:
    """Web-research a story and rewrite its body as a full long-form article
    (TL;DR, the story w/ history, case for, case against, why it matters,
    timeline, sources)."""
    path = render.DRAFTS / name
    if not path.exists():
        path = render.PUBLISHED / name
    if not path.exists():
        print(f"Not found in drafts or published: {name}")
        return
    meta, body = render._parse_frontmatter(path.read_text(encoding="utf-8"))
    if "## The story" in body:
        print("This file already looks like a full article; regenerating it.")
    headline = meta.get("headline") or name
    summary = next((ln for ln in body.splitlines() if ln and not ln.startswith(("#", "*"))), "")
    topic = f"{headline}\n\nContext: {summary}\nSource: {meta.get('source_url','')}"
    print(f"Writing full article: {headline}\n(model: {model}, runs web searches…)")
    try:
        data = enrich_mod.write_article(topic, model=model)
    except Exception as e:
        print(f"Article generation failed: {e}")
        return
    render.write_full_article(path, data)
    # Persist + geocode the location so the site can show a map.
    loc = (data.get("location") or "").strip()
    updates = {}
    if loc:
        updates["location"] = render._yaml_escape(loc)
        g = geo.geocode(loc)
        if g:
            updates["lat"] = g["lat"]
            updates["lon"] = g["lon"]
            print(f"Located: {loc} -> {g['lat']}, {g['lon']}")
        else:
            print(f"Location noted ('{loc}') but geocoding found no match.")
    if updates:
        render.update_frontmatter(path, updates)
    print(f"Rewrote {path.name} as a full article "
          f"({len(data.get('events', []))} timeline events, "
          f"{len(data.get('sources', []))} sources).")
    print("Review it, then: python run.py build")


def cmd_status() -> None:
    store = Store(DB_PATH)
    print("Item counts by status:", store.counts())
    print("Drafts awaiting review:", len(list(render.DRAFTS.glob("*.md"))))
    print("Published:", len(list(render.PUBLISHED.glob("*.md"))))


def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "ingest"
    if cmd == "ingest":
        # backend: --no-ai => off; --ai cli|api|auto|off; default auto (prefers CLI)
        backend = "off" if "--no-ai" in args else _opt(args, "--ai", "auto")
        model = _opt(args, "--model", "claude-haiku-4-5")
        limit_s = _opt(args, "--limit", "")
        limit = int(limit_s) if limit_s.isdigit() else None
        cmd_ingest(backend=backend, model=model, limit=limit)
    elif cmd == "build":
        cmd_build()
    elif cmd in ("preview", "review"):
        cmd_preview()
    elif cmd == "digest":
        print(f"Built {render.build_digest()} (+ digest.md)")
    elif cmd == "topics":
        print(f"Built {render.build_topics()} topic pages")
    elif cmd == "meetings":
        print(f"Built {meetings_mod.build_meetings().name} (county meetings)")
    elif cmd == "serve":
        port_s = _opt(args, "--port", "8787")
        serve_mod.serve(int(port_s) if port_s.isdigit() else 8787)
    elif cmd == "promote" and len(args) > 1:
        cmd_promote(args[1])
    elif cmd == "timeline" and len(args) > 1:
        cmd_timeline(args[1], model=_opt(args, "--model", "claude-haiku-4-5"))
    elif cmd == "article" and len(args) > 1:
        cmd_article(args[1], model=_opt(args, "--model", "claude-haiku-4-5"))
    elif cmd == "linkqueue":
        n = int(args[1]) if len(args) > 1 and args[1].isdigit() else 12
        print(f"Wrote {linkqueue_mod.build_candidates(limit=n)} candidate draft(s) "
              f"from related links. Review/deepen them like any draft.")
    elif cmd == "newsletter":
        out = newsletter_mod.build()
        print(f"Built {out}")
        if len(args) > 1 and args[1] == "send":
            newsletter_mod.send(args[2:] or [])
    elif cmd == "dedup":
        if "--apply" in args:
            plan = dedup_mod.plan(dedup_mod.find_clusters())
            print(f"Merged {dedup_mod.apply(plan)} duplicate stories into their canonicals.")
        else:
            dedup_mod.dry_run()
            print("\n(dry run — re-run with --apply to merge)")
    elif cmd == "letter" and len(args) > 1:
        cmd_letter(args[1], _opt(args, "--name", ""), "--anon" in args,
                   _opt(args, "--neighborhood", ""))
    elif cmd == "tidy":
        cmd_tidy()
    elif cmd == "alert":
        alerts_mod.email_flagged(_opt(args, "--to", "brucker.rob@gmail.com"))
    elif cmd == "qa":
        # Pre-publish managing-editor agent: adjudicate duplicate clusters,
        # unpublish empty stubs/junk. --dry-run reports without changing files.
        result = qa_mod.run(apply="--dry-run" not in args)
        print(f"QA: {result['merged_away']} merged, {result['unpublished']} unpublished")
    elif cmd == "cases-backfill":
        # One-time: enrich every development/zoning case (no per-build cap).
        print(cases_mod.backfill_cases())
    elif cmd == "events-backfill":
        # One-time: enrich every upcoming event (no per-build cap).
        print(events_mod.backfill_events())
    elif cmd == "expire":
        # Deterministic: unpublish weather watches/warnings/advisories older than
        # EXPIRE_HOURS so passed alerts don't pile up on the homepage. Reversible.
        result = expire_mod.run(apply="--dry-run" not in args)
        print(f"Expire: {result['expired']} stale weather alert(s) unpublished")
        for it in result["items"]:
            print(f"  - [{it['type']}] {it['headline']} ({it['age_hours']}h old)")
    elif cmd == "triage":
        # AI editor: auto-approve safe/newsworthy drafts, flag the rest.
        lim = _opt(args, "--limit", "12")
        result = editor_mod.triage(
            limit=int(lim) if lim.isdigit() else 12,
            deepen="--no-deepen" not in args,
        )
        print(f"Triage: {result}")
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
