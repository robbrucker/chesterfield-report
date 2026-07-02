#!/bin/bash
# AUTONOMOUS news pipeline for The Chesterfield Report (VPS, every 4 hours):
#   ingest -> triage -> qa -> (build -> deploy, only if content changed)
# Empty-run short-circuit: if triage published nothing and QA changed nothing,
# skip the build+deploy entirely (quiet runs cost nothing). A daily forced
# build at 08:00 still refreshes directory data (events/cases/farmers) even on
# a quiet news day.
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

# Capture each step's output so we can read the CRON_* change markers, while
# still teeing everything into the log.
log "[1/4] ingest"; ING=$("$PY" run.py ingest --limit 20 2>>"$LOG"); echo "$ING" >> "$LOG"
log "[2/4] triage"; TRI=$("$PY" run.py triage --limit 20 2>>"$LOG"); echo "$TRI" >> "$LOG"
log "[3/4] qa";     QA=$("$PY" run.py qa 2>>"$LOG");                  echo "$QA"  >> "$LOG"

new=$(printf '%s\n' "$ING" | sed -n 's/^CRON_INGEST_NEW=//p'       | tail -1)
pub=$(printf '%s\n' "$TRI" | sed -n 's/^CRON_TRIAGE_PUBLISHED=//p' | tail -1)
chg=$(printf '%s\n' "$QA"  | sed -n 's/^CRON_QA_CHANGED=//p'       | tail -1)
new=${new:-0}; pub=${pub:-0}; chg=${chg:-0}
hour=$(date +%H)

if [ "$pub" = "0" ] && [ "$chg" = "0" ] && [ "$hour" != "08" ]; then
  log "no published changes (ingest_new=$new triage_pub=$pub qa_changed=$chg); skipping build+deploy"
  log "===== pipeline done (no-op) ====="
  exit 0
fi

log "building (ingest_new=$new triage_pub=$pub qa_changed=$chg, hour=$hour)"
if [ -f "$ROOT/scripts/.deploy.env" ]; then set -a; source "$ROOT/scripts/.deploy.env"; set +a; fi
log "[4/4] build";   "$PY" run.py build >> "$LOG" 2>&1
log "deploy"
if [ -n "$VERCEL_TOKEN" ]; then
  npx -y vercel@latest deploy "$ROOT/public" --prod --yes --archive=tgz \
    --scope "${VERCEL_SCOPE:-rob-bruckers-projects}" --token "$VERCEL_TOKEN" >> "$LOG" 2>&1 \
    && log "deploy OK" || log "deploy FAILED"
else log "deploy skipped (no token)"; fi
log "===== pipeline done ====="
