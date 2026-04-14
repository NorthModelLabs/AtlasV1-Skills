#!/usr/bin/env bash
# Create portrait JPG + short WAV under claude-code-avatar/test-fixtures/ for offline /v1/generate tests.
# Face image priority:
#   1) ATLAS_LOCAL_FACE_PATH (copy)
#   2) S3 curated prefixes (same buckets as ~/Desktop/agents/demo_video/scripts/pull-assets.ts) if AWS_* set and ATLAS_SKIP_S3_FACE unset
#   3) ATLAS_FIXTURE_FACE_URL or fixed Unsplash portrait — not random stock (picsum gave non-faces).
# Safe to re-run; files are gitignored.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
OUT="$ROOT/test-fixtures"
mkdir -p "$OUT"
IMG="$OUT/face.jpg"
WAV="$OUT/speech.wav"
# Stable headshot-style crop (same URL every run).
FACE_URL="${ATLAS_FIXTURE_FACE_URL:-https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=256&h=256&fit=crop&q=85}"

if [[ -n "${ATLAS_LOCAL_FACE_PATH:-}" ]]; then
  echo "Copying local face: $ATLAS_LOCAL_FACE_PATH"
  cp -f "$ATLAS_LOCAL_FACE_PATH" "$IMG"
elif [[ "${ATLAS_SKIP_S3_FACE:-0}" != "1" ]] && python3 "$REPO/scripts/pull_atlas_demo_face.py" "$IMG" 2>/dev/null; then
  echo "Face image from S3 (showcase / simmy_demo / seed)."
else
  echo "Downloading portrait fixture…"
  curl -fsSL -o "$IMG" "$FACE_URL"
fi

if [[ ! -f "$WAV" ]]; then
  echo "Writing 1s 440Hz mono WAV…"
  export _ATLAS_FIXTURE_WAV="$WAV"
  python3 - <<'PY'
import math, os, struct, wave
path = os.environ["_ATLAS_FIXTURE_WAV"]
fr, dur, vol = 44100, 1.0, 0.08
n = int(fr * dur)
with wave.open(path, "w") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(fr)
    for i in range(n):
        v = int(32767 * vol * math.sin(2 * math.pi * 440 * i / fr))
        w.writeframes(struct.pack("<h", v))
PY
  unset _ATLAS_FIXTURE_WAV
fi

ls -la "$OUT"
echo ""
echo "Assets ready:"
echo "  IMAGE=$IMG"
echo "  AUDIO=$WAV"
echo ""
echo "Offline job (needs venv + requests + ATLAS_API_KEY):"
echo "  source .venv/bin/activate   # or .venv-cc-readme from verify-readme"
echo "  python3 skills/atlas-avatar/scripts/atlas_session.py offline --audio \"$WAV\" --image \"$IMG\""
