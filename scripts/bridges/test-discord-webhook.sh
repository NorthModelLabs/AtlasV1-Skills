#!/usr/bin/env bash
# Post a minimal session summary (+ embed) to Discord via webhook (atlas-bridge-discord).
# Requires: DISCORD_WEBHOOK_URL in the environment or in repo-root .env
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

if [[ -f "$REPO/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$REPO/.env"
  set +a
fi
if [[ -z "${DISCORD_WEBHOOK_URL:-}" ]]; then
  echo "Set DISCORD_WEBHOOK_URL (Server → Integrations → Webhooks), or add it to $REPO/.env (see .env.example)." >&2
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
  "bridge_note": "Smoke test — not a live Atlas session.",
  "viewer_url": "https://example.com/avatar-viewer-smoke"
}
EOF

echo "Posting smoke message to Discord…"
python3 "$REPO/skills/atlas-bridge-discord/scripts/post_session.py" -f "$TMP"
echo "Done. Check the Discord channel tied to this webhook."
