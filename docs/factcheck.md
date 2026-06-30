# Fact-Check & Story QA — methodology and operations wiki

This documents (1) the live-story fact-check work done on 2026-06-29, (2) the
catalog of failure modes the pipeline can produce, and (3) the design of the
recurring twice-daily fact-check system. The detailed findings log is private
(see `research/story-audit-2026-06-29.md` and the running journal).

---

## 1. What was done (2026-06-29)

**Trigger:** A published story ("Chesterfield approves Marlbank Farms…") asserted
an approval that never happened. That prompted a full audit.

**Process:** 12 parallel agents fact-checked all 163 published stories — each read
the source markdown + cited sources, checked internal consistency, and verified
claims against WTVR/WRIC/NBC12/county. Findings were triaged HIGH/MED/LOW.

**Result:** ~62 issues found. 47 stories corrected, 3 unpublished (a stale 2022
event, an unverifiable report, plus de-duplication), all deployed and committed.

**Also fixed structurally:**
- `enrich.py` system prompt: never assert approves/passes/rejects/votes unless the
  source says it happened (use proposes/reviews/weighs for pending items); keep
  numbers consistent across headline/TL;DR/body.
- `dedup.py`: a same-day content-similarity signal so re-tellings of one event
  (e.g. three write-ups of the same story from different sources) get proposed to
  the QA editor even when headlines/tags differ.
- `seo.build_redirects()` + `redirects.json`: URL redirects survive clean rebuilds.
- `ingest-cron.sh`: a `flock` build-collision guard (two builds can never write
  `public/` at once — this caused an incident during the bulk fix).

---

## 2. Failure-mode catalog (what to check for)

These are the recurring error classes the autonomous pipeline produces. The
fact-check pass checks every story against this list.

| # | Failure mode | Example found | Auto-fixable? |
|---|---|---|---|
| 1 | **Asserted outcome not in source** | "approves" a pending rezoning; "radiation-exposed" patient who tested clean | No — flag for review |
| 2 | **Outcome never updated** | missing person still "missing" after being found safe; teacher "charged" after acquittal | No — flag |
| 3 | **Date / weekday / future-date** | crash dated "Friday June 6" (was Sat); event dated after the publish timestamp | Yes (deterministic) |
| 4 | **Geographic conflation** | a Chesterfield **SC** theft; Henrico towns listed as Chesterfield | Partly (county check) |
| 5 | **Stale-as-current** | a 2022 event ingested as today's news | No — flag/unpublish |
| 6 | **Internal number contradiction** | "four charges" lists three; 311 vs 309 homes; 98+3=99 | Yes (consistency) |
| 7 | **Cross-story inconsistency** | K-9 age 4 vs 5; 71 units to Clark vs Wells | Partly |
| 8 | **Formatting / rendering** | literal `\n\n` in body; broken `CivicAlerts.asp` / spaced URLs | Yes |
| 9 | **Bad geocode** | map pin in Kansas / Illinois (US-centroid fallback) | Yes (clamp to county bbox) |
| 10 | **Unit errors** | "2.9 mg/L below 15 ppb" (193× over) | Partly |
| 11 | **Source attribution** | dispatch-fed brief stamped as a news outlet | No — flag |

---

## 3. Recurring fact-check system (design — approved 2026-06-29)

**Goal:** catch and correct these errors automatically, twice a day, without
colliding with the story pipeline.

**Decisions (locked):**
- **Action:** auto-fix the deterministic/mechanical classes (dates/weekday,
  number consistency, geography/geocode, formatting); **flag** outcome,
  attribution, and nuanced claims for human review. Apply fixes in a batch and
  **deploy once, under the `flock` lock**.
- **Scope:** rolling **48-hour** window of published stories per run.
- **Alerts:** HIGH/MED findings are written to `research/wiki/QA-ALERTS.md`, which
  the runner pushes into the openclaw mirror — **ask lazer to read
  `research/wiki/QA-ALERTS.md`** to hear what needs review. (LOW → journal only.)
- **Schedule:** twice daily at 05:30 and 17:30 (mid-gap between the every-2h
  ingest cron), sharing the build lock so it defers if a pipeline run is active.

**Components (built 2026-06-30):**
- `pipeline/chesterfield/factcheck.py` — selects last-48h stories; SAFE auto-fix
  (formatting artifacts + out-of-county geocodes) + flag-only checks (date/weekday,
  internal contradictions, asserted outcomes, geography, attribution via a Claude
  CLI call).
- `run.py factcheck [--window N] [--apply]` — CLI entry (`--apply` enables safe fixes).
- `scripts/factcheck-cron.sh` — `flock`-locked; runs factcheck → rebuilds+deploys
  ONCE only if a safe fix changed content → refreshes the openclaw mirror so lazer
  sees fresh alerts.
- `research/wiki/factcheck-journal.md` (append-only record) + `QA-ALERTS.md`
  (current HIGH/MED) — both private (research/ is gitignored) but mirrored to lazer.
- crontab: `30 5,17 * * *`.

**Alert delivery:** push email was abandoned — Brevo's SMTP key isn't on the box,
Web3Forms blocks server-side sends, openclaw WhatsApp is inbound-only, and the
Twilio account has no number. The pull-via-lazer file is the channel instead.

**Lesson baked in:** bulk content edits trigger a per-story Spanish re-translation
storm; a 47-story batch ran >1h and collided with the ingest cron. So the runner
flags by default, auto-fixes only safe classes, and always builds/deploys under
the shared lock.
