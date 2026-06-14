#!/usr/bin/env bash
# Deploy the static site (public/) to Vercel production and point the domain at it.
#
# Usage:
#   VERCEL_TOKEN=xxxxx ./scripts/deploy.sh
#   ./scripts/deploy.sh <token>
#
# Get a token at https://vercel.com/account/tokens
set -euo pipefail

TOKEN="${VERCEL_TOKEN:-${1:-}}"
if [ -z "$TOKEN" ]; then
  echo "No token. Run:  VERCEL_TOKEN=xxxxx ./scripts/deploy.sh   (token: vercel.com/account/tokens)"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "→ Building site…"
( cd pipeline && python3 run.py build )

echo "→ Deploying public/ to Vercel (production)…"
URL=$(npx -y vercel@latest deploy public --prod --yes --token="$TOKEN" | tail -1)
echo "Deployment URL: $URL"

echo "→ Attaching domain chesterfieldreport.com…"
npx -y vercel@latest alias set "$URL" chesterfieldreport.com --token="$TOKEN" \
  || echo "  (alias step failed — attach the domain to the project in the Vercel dashboard)"

echo "Done → https://chesterfieldreport.com"
