#!/usr/bin/env bash
# Long-running Telegram bot: /ask → Claude + MP4 (auto-plays), /talk → realtime Web App, /generate → verbatim.
# Needs: TELEGRAM_BOT_TOKEN, ATLAS_API_KEY; optional ELEVENLABS_API_KEY, ATLAS_VIEWER_BASE_URL, .env at repo root.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"

if [[ -f "$REPO/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$REPO/.env"
  set +a
fi

for d in "$REPO/.venv-cc-readme" "$REPO/.venv" "$REPO/venv"; do
  if [[ -d "$d" ]]; then
    # shellcheck source=/dev/null
    source "$d/bin/activate"
    break
  fi
done

exec python3 "$REPO/skills/atlas-bridge-telegram/scripts/telegram_avatar_bot.py"
