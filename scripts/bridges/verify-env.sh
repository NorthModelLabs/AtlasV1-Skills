#!/usr/bin/env bash
# Checks ATLAS_API_KEY and probes the same health surface as the public API docs (GET /v1/health).
set -euo pipefail

BASE="${ATLAS_API_BASE:-https://api.atlasv1.com}"

if [[ -z "${ATLAS_API_KEY:-}" ]]; then
  echo "ERROR: Set ATLAS_API_KEY (see .env.example)" >&2
  exit 1
fi

echo "GET ${BASE}/v1/health"
code=$(curl -sS -o /tmp/atlas-v1-health.txt -w "%{http_code}" "${BASE}/v1/health")
echo "HTTP ${code}"
head -c 800 /tmp/atlas-v1-health.txt
echo

echo "GET ${BASE}/v1/me (auth check)"
code=$(curl -sS -o /tmp/atlas-me.txt -w "%{http_code}" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  "${BASE}/v1/me")
echo "HTTP ${code}"
head -c 800 /tmp/atlas-me.txt
echo

if [[ "${code}" != "200" ]]; then
  echo "WARNING: /v1/me did not return 200 — check API key and base URL." >&2
  exit 2
fi

echo "OK"
