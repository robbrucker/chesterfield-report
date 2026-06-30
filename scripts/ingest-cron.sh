#!/bin/bash
# AUTONOMOUS news pipeline for The Chesterfield Report (VPS, every 2 hours):
#   ingest -> triage -> qa -> build -> deploy (chesterfieldreport.com)
export PATH="/usr/local/bin:/usr/bin:/bin"
ROOT="/root/chesterfield-report"
PY="/usr/bin/python3"
LOG="$ROOT/logs/ingest.log"
mkdir -p "$ROOT/logs"

# Build-collision guard: the cron AND any manual/audit build hold this same
# lock, so two builds never write public/ concurrently. Skip if one is active.
exec 9>/tmp/chesterfield-pipeline.lock
flock -n 9 || { echo "$(date) pipeline locked; skipping run" >> "$LOG"; exit 0; }
log() { echo "$(date '+%Y-%m-%d %H:%M:%S %Z') $*" >> "$LOG"; }
log "===== pipeline start (VPS) ====="
cd "$ROOT/pipeline" || { log "cd failed"; exit 1; }
log "[1/5] ingest";  "$PY" run.py ingest --limit 20 >> "$LOG" 2>&1
log "[2/5] triage";  "$PY" run.py triage --limit 20 >> "$LOG" 2>&1
log "[3/5] qa";      "$PY" run.py qa >> "$LOG" 2>&1
if [ -f "$ROOT/scripts/.deploy.env" ]; then set -a; source "$ROOT/scripts/.deploy.env"; set +a; fi
log "[4/5] build";   "$PY" run.py build >> "$LOG" 2>&1
log "[5/5] deploy"
if [ -n "$VERCEL_TOKEN" ]; then
  npx -y vercel@latest deploy "$ROOT/public" --prod --yes --archive=tgz \
    --scope "${VERCEL_SCOPE:-rob-bruckers-projects}" --token "$VERCEL_TOKEN" >> "$LOG" 2>&1 \
    && log "deploy OK" || log "deploy FAILED"
else log "deploy skipped (no token)"; fi
log "===== pipeline done ====="
