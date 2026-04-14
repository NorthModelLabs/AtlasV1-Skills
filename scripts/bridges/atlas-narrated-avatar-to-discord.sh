#!/usr/bin/env bash
# LLM script → ElevenLabs TTS → S3 face → Atlas offline → Discord MP4.
# See scripts/avatar_discord_narrator.py and .env.example (narrator / S3 / ElevenLabs block).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO"
exec python3 "$REPO/scripts/avatar_discord_narrator.py" "$@"
