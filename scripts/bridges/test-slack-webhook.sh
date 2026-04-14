#!/usr/bin/env bash
# Post a minimal fake session summary to Slack via Incoming Webhook (atlas-bridge-slack).
# Requires: SLACK_WEBHOOK_URL in the environment or in repo-root .env
# Optional: venv with requests (same as core/requirements.txt).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

if [[ -f "$REPO/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$REPO/.env"
  set +a
fi
if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  echo "Set SLACK_WEBHOOK_URL to your Slack Incoming Webhook URL (Workspace → Apps → Incoming Webhooks),"
  echo "or add it to $REPO/.env (see .env.example)." >&2
  exit 2
fi

for d in "$REPO/.venv-cc-readme" "$REPO/.venv" "$REPO/venv"; do
  if [[ -d "$d" ]]; then
    # shellcheck source=/dev/null
    source "$d/bin/activate"
    break
  fi
done

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
cat >"$TMP" <<'EOF'
{
  "session_id": "atlas-bridge-smoke",
  "room": "smoke-room",
  "mode": "conversation",
  "bridge_note": "Slack webhook smoke test — if you see this, the bridge is working."
}
EOF

echo "Posting smoke message to Slack…"
python3 "$REPO/skills/atlas-bridge-slack/scripts/post_session.py" -f "$TMP"
echo "Done. Check the Slack channel tied to this webhook."
