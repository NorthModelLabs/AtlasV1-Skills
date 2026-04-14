#!/usr/bin/env bash
# Post session text + an offline render URL to Slack (Incoming Webhooks cannot attach MP4 bytes).
# Uses a placeholder URL unless you pass a real presigned URL as first argument.
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
  echo "Set SLACK_WEBHOOK_URL or add it to .env" >&2
  exit 2
fi

for d in "$REPO/.venv-cc-readme" "$REPO/.venv" "$REPO/venv"; do
  if [[ -d "$d" ]]; then
    # shellcheck source=/dev/null
    source "$d/bin/activate"
    break
  fi
done

URL="${1:-https://example.com/replace-with-presigned-mp4-from-jobs-result}"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 -c "import json,sys; print(json.dumps({
  'session_id': 'slack-video-link-smoke',
  'room': 'smoke-room',
  'mode': 'offline',
  'bridge_note': 'Offline render link (smoke test).',
  'result_url': sys.argv[1],
}))" "$URL" >"$TMP"

echo "Posting to Slack with result_url in message…"
python3 "$REPO/skills/atlas-bridge-slack/scripts/post_session.py" -f "$TMP"
echo "Done. Slack shows the link; replace with a real presigned URL from: atlas_session jobs-result JOB_ID"
