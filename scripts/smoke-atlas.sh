#!/usr/bin/env bash
# Optional end-to-end smoke: health + index always; realtime create/delete only if ATLAS_API_KEY set.
# Realtime session may incur cost — use a test key / low-traffic window.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ATLAS_API_BASE="${ATLAS_API_BASE:-https://api.atlasv1.com}"

echo "== GET /v1/health (no auth) =="
python3 "$ROOT/core/atlas_cli.py" health

echo "== GET / (index) =="
python3 "$ROOT/core/atlas_cli.py" index | head -25

if [[ -z "${ATLAS_API_KEY:-}" ]]; then
  echo ""
  echo "ATLAS_API_KEY not set — skipping /v1/me and realtime create/delete."
  echo "To test realtime: export ATLAS_API_KEY then re-run this script."
  exit 0
fi

echo "== GET /v1/me =="
python3 "$ROOT/core/atlas_cli.py" me

echo "== POST /v1/realtime/session (passthrough, no face — may 4xx if invalid) =="
TMP="$(mktemp)"
set +e
python3 "$ROOT/core/atlas_cli.py" realtime create --mode passthrough >"$TMP" 2>&1
EC=$?
set -e
cat "$TMP"
if [[ "$EC" -ne 0 ]]; then
  echo "Realtime create exited $EC (e.g. no_capacity, auth, validation) — not deleting."
  rm -f "$TMP"
  exit "$EC"
fi
SID="$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('session_id') or '')" "$TMP" 2>/dev/null || true)"
rm -f "$TMP"
if [[ -z "$SID" ]]; then
  echo "No session_id in response; skip delete."
  exit 0
fi
echo "== DELETE /v1/realtime/session/$SID =="
python3 "$ROOT/core/atlas_cli.py" realtime delete "$SID"
echo "OK — realtime round-trip finished."
