#!/bin/bash
# One-off: backfill the Quick-facts box onto every published stub, then build+deploy.
export PATH="/usr/local/bin:/usr/bin:/bin"
ROOT="/root/chesterfield-report"
PY="/usr/bin/python3"
LOG="$ROOT/logs/backfill.log"
mkdir -p "$ROOT/logs"
log(){ echo "$(date "+%F %T %Z") $*" >> "$LOG"; }
cd "$ROOT/pipeline" || { log "cd failed"; exit 1; }
log "===== backfill start ====="
log "[1/3] deepen stubs"
"$PY" -c "from chesterfield import qa
import json as J
res = qa.deepen_stubs(apply=True, limit=30)
print(J.dumps(res, indent=0))" >> "$LOG" 2>&1
log "stubs remaining without box:"
c=0; for f in "$ROOT"/content/published/*.md; do grep -q "## Quick facts" "$f" || c=$((c+1)); done
log "  remaining=$c"
if [ -f "$ROOT/scripts/.deploy.env" ]; then set -a; source "$ROOT/scripts/.deploy.env"; set +a; fi
log "[2/3] build"
"$PY" run.py build >> "$LOG" 2>&1 && log "build OK" || { log "build FAILED"; exit 1; }
log "[3/3] deploy"
if [ -n "$VERCEL_TOKEN" ]; then
  npx -y vercel@latest deploy "$ROOT/public" --prod --yes \
    --scope "${VERCEL_SCOPE:-rob-bruckers-projects}" --token "$VERCEL_TOKEN" >> "$LOG" 2>&1 \
    && log "deploy OK" || log "deploy FAILED"
else log "deploy skipped (no token)"; fi
log "===== backfill done ====="
