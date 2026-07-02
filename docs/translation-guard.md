# Spanish translation storm guard (READ BEFORE any site-wide template edit)

## What happened (the incident this prevents)
On 2026-07-02 a site-wide template change (new per-page `<title>` + `<meta
description>` across ~60 section pages) invalidated many Spanish translation
cache keys at once. A single `run.py build` then queued **~1,000 Spanish
translation calls** ("the storm"), each a full `claude -p` subprocess, which
hammered the Claude subscription. The build ran for tens of minutes and looked
"stuck." Nothing was broken; it was doing 1,000 serial translations.

## Why it can't happen anymore
Three layers, cheapest first:

1. **Per-string / per-story caches** (`es_cache.json`, `es_ui_cache.json`) —
   an unchanged story or UI string is never re-translated. Normal builds do ~0
   translation calls.
2. **Per-build translation cap** (`translate.py`, `CR_TRANSLATE_MAX`, default
   **200** CLI calls) — the translation-specific check. When a build tries to
   fire more than this many translation calls, the guard trips: it stops making
   new calls, leaves the remaining strings/pages in **English for that build**
   (pages still ship), logs a loud `TRANSLATION STORM GUARD tripped` line, and
   the deferred items are picked up on a later build. A normal cron build never
   comes close; only a mass cache-invalidation would.
3. **Global AI budget** (`ai.py`, `CR_AI_BUDGET`, default **400** calls per
   `run.py` process) — the hard ceiling across *all* AI features, the ultimate
   backstop.

The ES page-hash gate (`es_page_hashes.json`) deliberately does **not** record
the hash of a page that the guard left partly-English, so that page is retried
and completed on a later build instead of being frozen half-translated.

## If you make a site-wide template change (titles, meta, nav, footer, shell)
Expect a one-time translation catch-up. Do it as a **controlled backfill**, not
via the 4-hour cron:

```bash
# On the VPS, hold the pipeline lock so it can't collide with the cron, and
# raise BOTH caps for this one intentional run:
cd /root/chesterfield-report/pipeline
flock -n /tmp/chesterfield-pipeline.lock \
  env CR_TRANSLATE_MAX=3000 CR_AI_BUDGET=3500 /usr/bin/python3 run.py build
# then deploy public/ as usual (see handoff / ingest-cron.sh for the vercel cmd)
```

If the ES pages look stuck half-English after such a change, delete the page
gate so every page re-localizes on the next (raised-cap) build:

```bash
rm -f /root/chesterfield-report/pipeline/es_page_hashes.json
```

## Watching for it
- The dashboard (`analytics.chesterfieldreport.com/cr-ai/`) shows `translate`
  calls per day in the usage chart — a green spike is a catch-up in progress.
- The cron log (`logs/ingest.log`) prints `TRANSLATION STORM GUARD tripped`
  whenever the cap engages — if you see it on a *routine* build (no template
  change), investigate what invalidated the cache.
- Turn translation off entirely from the dashboard or `run.py ai off translate`
  if it ever misbehaves.

## Tunables
| knob | where | default | meaning |
|------|-------|---------|---------|
| `CR_TRANSLATE_MAX` | env | 200 | max translation CLI calls per build |
| `CR_AI_BUDGET`     | env | 400 | max AI calls per `run.py` process (all features) |
| `es_page_hashes.json` | pipeline/ | — | delete to force full ES re-localize |
