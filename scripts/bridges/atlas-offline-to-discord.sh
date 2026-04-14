#!/usr/bin/env bash
# Atlas POST /v1/generate → jobs-wait → download MP4 → Discord (webhook: attach or link).
#
# Needs: ATLAS_API_KEY, DISCORD_WEBHOOK_URL, venv + requests, curl.
#
# Default audio is the test fixture (440 Hz tone). For speech either:
#   ATLAS_OFFLINE_SPEAK_TEXT="…" + ELEVENLABS_API_KEY in .env (generates WAV via scripts/elevenlabs_to_wav.py), or
#   ATLAS_OFFLINE_AUDIO=/path/to.wav
#
# Usage:
#   ./scripts/bridges/atlas-offline-to-discord.sh ["Caption line(s) for Discord"]
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
if [[ -z "${DISCORD_WEBHOOK_URL:-}" ]]; then
  echo "Set DISCORD_WEBHOOK_URL for the target channel." >&2
  exit 2
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
SIZE="$(python3 -c "import pathlib; print(pathlib.Path('$MP4').stat().st_size)")"
MAX=$((25 * 1024 * 1024))

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

if [[ "$SIZE" -gt "$MAX" ]]; then
  echo "MP4 is ${SIZE} bytes (> ~25 MB Discord attach). Posting link only." >&2
  python3 <<'PY'
import json, os

path = os.environ["POST_JSON"]
with open(path) as f:
    payload = json.load(f)
note = (payload.get("bridge_note") or "").strip()
suffix = "Clip exceeds ~25 MB webhook limit — use the render link below."
if note:
    payload["bridge_note"] = f"{note}\n\n_{suffix}_"
else:
    payload["bridge_note"] = f"_{suffix}_"
with open(path, "w") as f:
    json.dump(payload, f)
PY
  python3 "$REPO/skills/atlas-bridge-discord/scripts/post_session.py" -f "$POST_JSON"
  echo "Posted link to Discord (no attachment)."
  exit 0
fi

echo "Uploading ${SIZE} bytes to Discord…"
python3 "$REPO/skills/atlas-bridge-discord/scripts/post_session.py" -f "$POST_JSON" --video "$MP4"
echo "Done. Check Discord for the message and attached Atlas MP4."
