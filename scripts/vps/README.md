# scripts/vps — production VPS copies (backup / reference)

These are the **live scripts from the production server**, kept here only so the
prod automation has an off-machine backup. They are **not generic** and forks
should not run them as-is:

- Paths are hardcoded to the server layout (`/root/chesterfield-report`) and the
  system Python (`/usr/bin/python3`, which has a working `pyexpat`).
- The portable/example versions live one level up in `scripts/` (`deploy.sh`,
  `ingest-cron.sh`). Start from those when adapting the pipeline for your own
  locality — see `LOCALIZE.md`.

Contents:

- `ingest-cron.sh` — the every-2-hours pipeline the VPS runs (ingest -> triage ->
  qa -> build -> deploy to Vercel).
- `backfill-boxes.sh` — one-off maintenance: backfill the Quick-facts box onto
  older published stubs, then build + deploy.
- `deploy.sh` — the VPS build-and-deploy variant.

Secrets (`VERCEL_TOKEN`, etc.) are read from `scripts/.deploy.env`, which is
gitignored and lives only on the server.
