#!/usr/bin/env bash
# End-to-end: fixtures → POST /v1/generate → poll → result URL. Requires ATLAS_API_KEY.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
cd "$REPO"

if [[ -f "$REPO/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$REPO/.env"
  set +a
fi
if [[ -z "${ATLAS_API_KEY:-}" ]]; then
  echo "Set ATLAS_API_KEY or add it to $REPO/.env (see .env.example)." >&2
  exit 2
fi

"$ROOT/scripts/make-test-assets.sh" >/dev/null
AUDIO="$ROOT/test-fixtures/speech.wav"
IMAGE="$ROOT/test-fixtures/face.jpg"

for d in "$REPO/.venv-cc-readme" "$REPO/.venv" "$REPO/venv"; do
  if [[ -d "$d" ]]; then
    # shellcheck source=/dev/null
    source "$d/bin/activate"
    break
  fi
done

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
echo "Submitting offline job…"
python3 "$REPO/skills/atlas-avatar/scripts/atlas_session.py" offline --audio "$AUDIO" --image "$IMAGE" | tee "$TMP"
export _ATLAS_E2E_JSON="$TMP"
JOB="$(python3 -c 'import json, os; d=json.load(open(os.environ["_ATLAS_E2E_JSON"])); print(d.get("job_id") or d.get("id") or "")')"
unset _ATLAS_E2E_JSON
if [[ -z "$JOB" ]]; then
  echo "Could not read job_id from offline response." >&2
  exit 3
fi
echo "Waiting on job $JOB …"
python3 "$REPO/skills/atlas-avatar/scripts/atlas_session.py" jobs-wait "$JOB" --interval 3 --timeout 600
echo "Result:"
python3 "$REPO/skills/atlas-avatar/scripts/atlas_session.py" jobs-result "$JOB"
