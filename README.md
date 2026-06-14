# The Chesterfield Report

A hands-off hyperlocal news site for **Chesterfield County, Virginia**, live at
[chesterfieldreport.com](https://chesterfieldreport.com).

Every couple of hours it pulls from local sources, uses an LLM to decide what is
actually news and write plain-language summaries with links back to the original
reporting, builds a static site, and deploys it. No ads, no paywall, no login.

> **Want this for your own town, city, or county?** See **[LOCALIZE.md](LOCALIZE.md)**.
> Fork the repo, point an AI coding agent (Claude Code) at it, say "make this for
> &lt;your place&gt;," and follow the playbook. Most of the work is an agent
> renaming, re-pointing sources, and disabling the few county-specific features
> that do not transfer.

---

## What it does

- **Autonomous pipeline**: ingest -> triage (an LLM editor decides newsworthy /
  significant / actually-local / sensitive) -> QA (a second LLM merges duplicate
  coverage and cleans up) -> web-grounded article writing -> build -> deploy.
  Runs on a schedule with no human in the critical path.
- **Plain-language stories** with a who/what/when/where box, context, and links
  to every source. Nothing is invented; if a fact cannot be verified it says so.
- **Live dispatch ticker**: active Police, Fire/EMS, and Traffic calls from the
  county's public feeds, refreshed every 5 minutes (client-side).
- **Dining guide + map**: ~500 local restaurants by cuisine (OpenStreetMap), plus
  a health-inspection lookup.
- **County meetings**: plain-language summaries of upcoming agendas.
- **Maps, topic pages, RSS, Open Graph share cards, SEO, light/dark theme,** and
  tip + opinion forms (no backend).

## How it works

```
sources.py  ->  ingest (dedup + freshness gate)  ->  triage (LLM editor)
            ->  QA (LLM managing editor, dedup)  ->  enrich (web-grounded article)
            ->  content/published/*.md  ->  render -> public/  ->  deploy (Vercel)
```

Every story is a Markdown file with YAML frontmatter; the renderer compiles
published markdown into the static site. The AI steps shell out to the **Claude
Code CLI** (`claude -p ... --json-schema ...`), so no API key is required (it runs
on a Claude subscription). An Anthropic-API backend and a dependency-free
extractive fallback also exist.

## Stack

Python standard library (no framework), the Claude Code CLI for the AI steps,
SQLite for dedup state, a static-site generator, OpenStreetMap (Nominatim +
Overpass) for geocoding and the dining map, and Vercel for hosting. The pipeline
is scheduled with cron (or launchd, or GitHub Actions).

## Local development

```bash
cd pipeline
python3 run.py ingest      # pull sources -> content/drafts (or auto-publish in autonomous mode)
python3 run.py triage      # LLM editor decides what to publish
python3 run.py qa          # LLM managing editor: dedup + cleanup
python3 run.py build       # compile the static site into public/
python3 -m http.server 8000 --directory ../public   # then open http://localhost:8000
```

Use a Python with a working `pyexpat` (XML). System `/usr/bin/python3` works on
macOS; some Homebrew builds have broken `pyexpat`.

## Deploy

The site is static and deploys to Vercel:

```bash
npx vercel deploy public --prod --yes --token "$VERCEL_TOKEN" --scope "$VERCEL_SCOPE"
```

`scripts/deploy.sh` wraps this and `scripts/ingest-cron.sh` runs the full
pipeline end to end (ingest -> ... -> deploy) for scheduling. Secrets
(`VERCEL_TOKEN`, `WEB3FORMS_KEY`) live in `scripts/.deploy.env`, which is
**gitignored and must never be committed**.

## Legal and ethical

Government content is public record. For copyrighted outlets the site stores only
a headline, a link back, and a short **original** summary, never full article
text. Fetchers send a descriptive User-Agent. Editorial "case for / case against"
sections are clearly labeled balanced framings, not quotes attributed to real
people.

## About

The Chesterfield Report is an independent project published by
[Commonwealth Business Systems](https://www.commonwealth-systems.com/), a
Chesterfield, Virginia company focused on AI consulting for small businesses.
Coverage decisions are made independently. Not affiliated with or endorsed by
Chesterfield County government.
