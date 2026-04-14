#!/usr/bin/env bash
# Post a tiny synthetic MP4 to Discord via webhook (proves --video path).
# Requires: DISCORD_WEBHOOK_URL, ffmpeg (for a sub-second H.264 clip), venv optional.
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
  echo "Set DISCORD_WEBHOOK_URL or add it to .env" >&2
  exit 2
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Install ffmpeg to generate a tiny test MP4, or run manually:" >&2
  echo "  python3 skills/atlas-bridge-discord/scripts/post_session.py -f session.json --video /path/to/atlas-output.mp4" >&2
  exit 2
fi

for d in "$REPO/.venv-cc-readme" "$REPO/.venv" "$REPO/venv"; do
  if [[ -d "$d" ]]; then
    # shellcheck source=/dev/null
    source "$d/bin/activate"
    break
  fi
done

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT
MP4="$TMPDIR/smoke.mp4"
JSON="$TMPDIR/session.json"

# ~0.5s color bars; small file for webhook limit
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "testsrc=duration=0.5:size=160x120:rate=15" \
  -c:v libx264 -pix_fmt yuv420p -movflags +faststart "$MP4"

cat >"$JSON" <<'EOF'
{
  "session_id": "discord-video-smoke",
  "room": "smoke-room",
  "mode": "offline",
  "bridge_note": "Synthetic MP4 attachment test — not a live session."
}
EOF

echo "Posting text + MP4 attachment to Discord…"
python3 "$REPO/skills/atlas-bridge-discord/scripts/post_session.py" -f "$JSON" --video "$MP4"
echo "Done. Check the Discord channel for the message and playable clip."
