#!/usr/bin/env bash
# Smoke test for terminal agents / CI: health + index; optional short realtime if ATLAS_API_KEY set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
export ATLAS_API_BASE="${ATLAS_API_BASE:-https://api.atlasv1.com}"
SESSION="$ROOT/claude-code-avatar/.demo-session.json"

echo "== atlas_session health (no auth) =="
python3 "$ROOT/skills/atlas-avatar/scripts/atlas_session.py" health

echo "== atlas_session index (no auth) =="
python3 "$ROOT/skills/atlas-avatar/scripts/atlas_session.py" index | head -20

if [[ -z "${ATLAS_API_KEY:-}" ]]; then
  echo ""
  echo "ATLAS_API_KEY not set — skipping realtime start/delete."
  echo "To test paid path: export ATLAS_API_KEY then re-run: ./claude-code-avatar/scripts/demo.sh"
  exit 0
fi

echo ""
echo "== realtime passthrough create (uses credits) =="
python3 "$ROOT/skills/atlas-avatar/scripts/atlas_session.py" start --mode passthrough >"$SESSION"
python3 -c "
import json
p = '$SESSION'
d = json.load(open(p))
red = {k: v for k, v in d.items() if k != 'token'}
print(json.dumps(red, indent=2))
"
SID="$(python3 -c "import json;print(json.load(open('$SESSION'))['session_id'])")"
rm -f "$SESSION"
echo "== leave $SID =="
python3 "$ROOT/skills/atlas-avatar/scripts/atlas_session.py" leave --session-id "$SID"
echo "OK — demo finished."
