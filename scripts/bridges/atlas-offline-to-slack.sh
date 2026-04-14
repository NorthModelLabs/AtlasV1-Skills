#!/usr/bin/env bash
# Atlas POST /v1/generate → jobs-wait → download MP4 → Slack.
#
# If BOT_OAUTH_TOKEN (or SLACK_BOT_TOKEN) + SLACK_CHANNEL_ID are set: uploads the MP4 via Slack Web API
# (playable in-channel, like Discord attach). Otherwise posts only a presigned link via Incoming Webhook
# (Slack usually does not inline‑play raw storage URLs).
#
# Needs: ATLAS_API_KEY, and either SLACK_WEBHOOK_URL (link-only) or bot token + SLACK_CHANNEL_ID (file upload).
# Optional: SLACK_WEBHOOK_URL still used only on link-only path.
#
# Default audio is the test fixture (440 Hz tone). For speech either:
#   ATLAS_OFFLINE_SPEAK_TEXT="…" + ELEVENLABS_API_KEY in .env (generates WAV via scripts/elevenlabs_to_wav.py), or
#   ATLAS_OFFLINE_AUDIO=/path/to.wav
#
# Usage:
#   ./scripts/bridges/atlas-offline-to-slack.sh ["Intro line for Slack"]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

if [[ -f "$REPO/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$REPO/.env"
  set +a
fi
if [[ -z "${ATLAS_API_KEY:-}" ]]; then
  echo "Set ATLAS_API_KEY (see .env.example)." >&2
  exit 2
fi

BOT="${SLACK_BOT_TOKEN:-${SLACK_BOT_OAUTH_TOKEN:-${BOT_OAUTH_TOKEN:-}}}"
CH="${SLACK_CHANNEL_ID:-}"
CH="${CH//$'\r'/}"
BOT="${BOT//$'\r'/}"
if [[ -n "$CH" && "$CH" != C* ]]; then
  echo "WARNING: SLACK_CHANNEL_ID should look like C01234ABCDE (from the Slack client URL). Current value may be wrong." >&2
fi
if [[ -n "$BOT" && -n "$CH" ]]; then
  echo "Slack: using bot file upload (channel ${CH:0:12}…)." >&2
elif [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  echo "Either set SLACK_WEBHOOK_URL (link-only), or set BOTH BOT_OAUTH_TOKEN and SLACK_CHANNEL_ID (MP4 upload)." >&2
  [[ -z "$BOT" ]] && echo "  → BOT_OAUTH_TOKEN is empty (need xoxb-… from OAuth & Permissions)." >&2
  [[ -z "$CH" ]] && echo "  → SLACK_CHANNEL_ID is empty (need C… from channel URL)." >&2
  exit 2
else
  echo "Slack: BOT_OAUTH_TOKEN or SLACK_CHANNEL_ID missing — falling back to Incoming Webhook (link only, no in-channel player)." >&2
fi

CAPTION="${*:-}"
if [[ -z "$CAPTION" ]]; then
  CAPTION=""
fi
export CAPTION

for d in "$REPO/.venv-cc-readme" "$REPO/.venv" "$REPO/venv"; do
  if [[ -d "$d" ]]; then
    # shellcheck source=/dev/null
    source "$d/bin/activate"
    break
  fi
done

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

"$REPO/claude-code-avatar/scripts/make-test-assets.sh" >/dev/null

if [[ -n "${ATLAS_OFFLINE_SPEAK_TEXT:-}" && -z "${ATLAS_OFFLINE_AUDIO:-}" ]]; then
  echo "ElevenLabs: generating speech WAV for Atlas…" >&2
  ELEVEN_OUT="$WORKDIR/atlas-eleven.wav"
  python3 "$REPO/scripts/elevenlabs_to_wav.py" "$ATLAS_OFFLINE_SPEAK_TEXT" "$ELEVEN_OUT"
  AUDIO="$ELEVEN_OUT"
elif [[ -n "${ATLAS_OFFLINE_AUDIO:-}" ]]; then
  AUDIO="${ATLAS_OFFLINE_AUDIO}"
else
  echo "Audio: default 1s test tone. Set ATLAS_OFFLINE_SPEAK_TEXT (+ ELEVENLABS_API_KEY) or ATLAS_OFFLINE_AUDIO for speech." >&2
  AUDIO="$REPO/claude-code-avatar/test-fixtures/speech.wav"
fi

IMAGE="${ATLAS_OFFLINE_IMAGE:-$REPO/claude-code-avatar/test-fixtures/face.jpg}"
if [[ ! -f "$AUDIO" ]] || [[ ! -f "$IMAGE" ]]; then
  echo "Missing audio/image. Check ATLAS_OFFLINE_AUDIO paths or ElevenLabs env." >&2
  exit 2
fi

OFFLINE_JSON="$WORKDIR/offline.json"
RESULT_JSON="$WORKDIR/result.json"
MP4="$WORKDIR/atlas-render.mp4"
POST_JSON="$WORKDIR/post.json"

echo "Submitting Atlas offline job…"
python3 "$REPO/skills/atlas-avatar/scripts/atlas_session.py" offline --audio "$AUDIO" --image "$IMAGE" >"$OFFLINE_JSON"
JOB="$(python3 -c "import json; print(json.load(open('$OFFLINE_JSON')).get('job_id') or json.load(open('$OFFLINE_JSON')).get('id') or '')")"
if [[ -z "$JOB" ]]; then
  echo "Could not read job_id from offline response." >&2
  exit 3
fi
echo "Submitted job $JOB"

echo "Waiting on job $JOB …"
python3 "$REPO/skills/atlas-avatar/scripts/atlas_session.py" jobs-wait "$JOB" --interval 3 --timeout 600 >/dev/null

echo "Fetching result…"
python3 "$REPO/skills/atlas-avatar/scripts/atlas_session.py" jobs-result "$JOB" >"$RESULT_JSON"
URL="$(python3 -c "import json; print(json.load(open('$RESULT_JSON')).get('url') or '')")"
if [[ -z "$URL" ]]; then
  echo "No url in jobs-result JSON." >&2
  exit 3
fi

echo "Downloading render…"
curl -fsSL -o "$MP4" "$URL"

export JOB URL POST_JSON
python3 <<'PY'
import json, os

speak = os.environ.get("ATLAS_OFFLINE_SPEAK_TEXT", "").strip()
cap = os.environ.get("CAPTION", "").strip()
if speak and cap:
    body = f"{speak}\n\n{cap}"
elif speak:
    body = speak
else:
    body = cap

payload = {
    "session_id": os.environ["JOB"],
    "room": "offline-generate",
    "mode": "offline",
    "bridge_note": body,
    "result_url": os.environ.get("URL", ""),
}
with open(os.environ["POST_JSON"], "w") as f:
    json.dump(payload, f)
PY

if [[ -n "$BOT" && -n "$CH" ]]; then
  echo "Uploading MP4 to Slack (bot + channel)…"
  python3 "$REPO/skills/atlas-bridge-slack/scripts/post_session.py" -f "$POST_JSON" --video "$MP4"
  echo "Done. Check Slack for the file attachment."
  exit 0
fi

echo "Posting presigned link to Slack (Incoming Webhook only — no inline player)…"
python3 "$REPO/skills/atlas-bridge-slack/scripts/post_session.py" -f "$POST_JSON"
