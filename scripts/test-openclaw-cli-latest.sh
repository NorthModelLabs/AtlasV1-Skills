#!/usr/bin/env bash
# Pointers only — OpenClaw install/update/uninstall live in official docs.
set -euo pipefail

echo "OpenClaw documentation (install / update / uninstall / verify):"
echo "  https://docs.openclaw.ai/install"
echo ""

if command -v openclaw >/dev/null 2>&1; then
  openclaw --version
else
  echo "\`openclaw\` not on PATH — follow the URL above on this machine."
fi
