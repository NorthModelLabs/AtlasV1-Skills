#!/usr/bin/env bash
# Verifies everything in claude-code-avatar/README.md that does NOT require a vendor agent CLI on PATH.
# Optional: ATLAS_API_KEY for paid leg (same as demo.sh).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
echo "== Repo root: $ROOT"

fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -f core/requirements.txt ]] || fail "missing core/requirements.txt"
[[ -f skills/atlas-avatar/scripts/atlas_session.py ]] || fail "missing atlas_session.py"
[[ -f CLAUDE.md ]] || fail "missing root CLAUDE.md"
[[ -f claude-code-avatar/CLAUDE.md ]] || fail "missing claude-code-avatar/CLAUDE.md"
[[ -f claude-code-avatar/PROMPTS.md ]] || fail "missing PROMPTS.md"
[[ -x claude-code-avatar/scripts/demo.sh ]] || fail "demo.sh not executable"
echo "== README file paths OK"

echo "== venv + pip install -r core/requirements.txt (avoids PEP 668 on Homebrew Python)"
VENV="$ROOT/.venv-cc-readme"
if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q -r core/requirements.txt
export PATH="$VENV/bin:$PATH"
echo "== pip OK (venv: $VENV)"

echo "== README §4: ./claude-code-avatar/scripts/demo.sh"
./claude-code-avatar/scripts/demo.sh

[[ ! -f claude-code-avatar/.demo-session.json ]] || fail ".demo-session.json should not remain after no-key demo"

if command -v claude >/dev/null 2>&1; then
  echo "== Agent CLI on PATH: $(claude --version 2>/dev/null || true)"
else
  echo "== No vendor agent CLI in PATH (expected in CI; install per claude-code-avatar/README §1–3 on your machine)"
fi

echo ""
echo "ALL README CHECKS PASSED (automatable parts)."
