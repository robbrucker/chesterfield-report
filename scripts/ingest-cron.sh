#!/bin/bash
# AUTONOMOUS news pipeline for The Chesterfield Report (runs every 2 hours):
#   ingest  -> pull new stories into the local draft queue
#   triage  -> AI editor (autonomous): publishes newsworthy+significant items,
#              deepens them, and drops the rest (reject/duplicate) reversibly.
#              Learns the human's taste from review_feedback.jsonl.
#   qa      -> managing-editor agent: adjudicates duplicate clusters and pulls
#              empty/placeholder/junk stories BEFORE publish (all reversible).
#   build   -> regenerate the site (only published stories)
#   deploy  -> push to chesterfieldreport.com (if a token is configured)
#
# No human is in the critical path. http://localhost:8787 (python3 run.py serve)
# is now OPTIONAL oversight — approve/reject there to keep teaching the editor.
# Scheduled by the launchd LaunchAgent com.chesterfieldreport.ingest (every 2h).
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

ROOT="/Users/robbrucker/development/chesterfield"
LOG="$ROOT/logs/ingest.log"
mkdir -p "$ROOT/logs"

# Pin to the system python: Homebrew's python3 (3.14) has a BROKEN pyexpat
# ("No module named expat"), which silently degrades XML/RSS parsing. The
# stdlib-only pipeline runs fine on macOS system python (3.9), which is healthy.
PY="/usr/bin/python3"

log() { echo "$(date '+%Y-%m-%d %H:%M:%S %Z') $*" >> "$LOG"; }

log "===== pipeline start ====="
cd "$ROOT/pipeline" || { log "cd failed"; exit 1; }

log "[1/5] ingest"
"$PY" run.py ingest --limit 20 >> "$LOG" 2>&1

log "[2/5] triage (autonomous AI editor: publish newsworthy, drop the rest)"
"$PY" run.py triage --limit 20 >> "$LOG" 2>&1

log "[3/5] qa (managing-editor agent: adjudicate dups + pull junk before publish)"
"$PY" run.py qa >> "$LOG" 2>&1

if [ -f "$ROOT/scripts/.deploy.env" ]; then source "$ROOT/scripts/.deploy.env"; fi

log "[4/5] build"
"$PY" run.py build >> "$LOG" 2>&1

log "[5/5] deploy"
if [ -f "$ROOT/scripts/.deploy.env" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/scripts/.deploy.env"
  if [ -n "$VERCEL_TOKEN" ]; then
    npx -y vercel@latest deploy "$ROOT/public" --prod --yes --archive=tgz \
      --scope "${VERCEL_SCOPE:-rob-bruckers-projects}" --token "$VERCEL_TOKEN" \
      >> "$LOG" 2>&1 && log "deploy OK" || log "deploy FAILED"
  else
    log "deploy skipped (VERCEL_TOKEN empty in scripts/.deploy.env)"
  fi
else
  log "deploy skipped (no scripts/.deploy.env)"
fi

log "===== pipeline done ====="
