#!/usr/bin/env python3
"""Post Atlas realtime session JSON to Discord webhook."""
from __future__ import annotations

import argparse
import json
import os
import sys

import requests


def main() -> int:
    p = argparse.ArgumentParser(description="Post Atlas session summary to Discord")
    p.add_argument("--file", "-f", help="Path to JSON file (else stdin)")
    args = p.parse_args()
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        print("Set DISCORD_WEBHOOK_URL", file=sys.stderr)
        return 2
    if args.file:
        raw = open(args.file, encoding="utf-8").read()
    else:
        raw = sys.stdin.read()
    data = json.loads(raw)
    sid = data.get("session_id", "?")
    room = data.get("room", "?")
    mode = data.get("mode", "?")
    pricing = data.get("pricing", "")
    lines = [
        "**Atlas realtime session**",
        f"• session_id: `{sid}`",
        f"• room: `{room}`",
        f"• mode: `{mode}`",
    ]
    if pricing:
        lines.append(f"• pricing: {pricing}")
    lines.append(
        "• Use `livekit_url` + `token` in your LiveKit client (keep token out of public channels)."
    )
    content = "\n".join(lines)
    r = requests.post(url, json={"content": content}, timeout=30)
    if not r.ok:
        print(r.text, file=sys.stderr)
        return 3
    print(json.dumps({"ok": True, "discord_status": r.status_code}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
