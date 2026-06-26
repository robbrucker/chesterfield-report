#!/bin/bash
# Daily Facebook recap for The Chesterfield Report (VPS).
#
# Cron runs this at 22:00 and 23:00 UTC. The Python gate
# (--at-hour 18 --tz America/New_York) makes it post exactly once, at 6 p.m.
# Eastern, year-round and DST-proof: only the run whose Eastern hour is 18
# proceeds. --no-fallback skips days with no new stories; --skip-if-posted
# guards against double-posting the same day.
export PATH="/usr/local/bin:/usr/bin:/bin"
ROOT="/root/chesterfield-report"
PY="/usr/bin/python3"
LOG="$ROOT/logs/fb-recap.log"
mkdir -p "$ROOT/logs"
cd "$ROOT" || exit 1
if [ -f "$ROOT/scripts/.deploy.env" ]; then set -a; source "$ROOT/scripts/.deploy.env"; set +a; fi
echo "$(date '+%Y-%m-%d %H:%M:%S %Z') fb-recap run" >> "$LOG"
"$PY" scripts/post_facebook.py --post --bilingual --quiet-fallback --skip-if-posted \
  --at-hour 18 --tz America/New_York >> "$LOG" 2>&1
