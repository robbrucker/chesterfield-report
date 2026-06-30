#!/bin/bash
# Twice-daily story QA for The Chesterfield Report (05:30 & 17:30, between the
# every-2h ingest cron). Re-checks the last 48h of published stories:
#   - SAFE auto-fix: formatting artifacts + out-of-county map geocodes
#   - FLAG for review: outcome/attribution/date/number issues
# Findings -> research/wiki/factcheck-journal.md (record) + QA-ALERTS.md (what
# lazer reads). Shares the pipeline flock lock so it never builds concurrently
# with ingest. Only rebuilds/deploys if a safe auto-fix was actually applied.
export PATH="/usr/local/bin:/usr/bin:/bin"
ROOT="/root/chesterfield-report"
PY="/usr/bin/python3"
LOG="$ROOT/logs/factcheck.log"
mkdir -p "$ROOT/logs"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S %Z') $*" >> "$LOG"; }

exec 9>/tmp/chesterfield-pipeline.lock
flock -n 9 || { log "pipeline locked (ingest running); skipping factcheck"; exit 0; }

log "===== factcheck start ====="
cd "$ROOT/pipeline" || { log "cd failed"; exit 1; }
if [ -f "$ROOT/scripts/.deploy.env" ]; then set -a; source "$ROOT/scripts/.deploy.env"; set +a; fi

OUT=$("$PY" run.py factcheck --window 48 --apply 2>>"$LOG")
log "$OUT"

# Rebuild + deploy ONCE only if safe auto-fixes changed content (we hold the lock).
if echo "$OUT" | grep -q "'apply_built': True"; then
  log "auto-fixes applied -> build + deploy"
  if "$PY" run.py build >> "$LOG" 2>&1 && [ -n "$VERCEL_TOKEN" ]; then
    npx -y vercel@latest deploy "$ROOT/public" --prod --yes --archive=tgz \
      --scope "${VERCEL_SCOPE:-rob-bruckers-projects}" --token "$VERCEL_TOKEN" >> "$LOG" 2>&1 \
      && log "deploy OK" || log "deploy FAILED"
  fi
fi

# Push the fresh QA-ALERTS to the openclaw mirror so lazer can read them now.
if [ -x /root/chesterfield-mirror-refresh.sh ]; then
  /root/chesterfield-mirror-refresh.sh >> "$LOG" 2>&1 && log "mirror refreshed (lazer can read QA-ALERTS.md)"
fi
log "===== factcheck done ====="
