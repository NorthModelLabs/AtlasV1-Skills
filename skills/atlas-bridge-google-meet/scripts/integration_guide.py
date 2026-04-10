#!/usr/bin/env python3
"""Emit JSON guidance for Atlas + Google Meet (no Meet join implementation)."""
from __future__ import annotations

import json

GUIDE = {
    "platform": "google_meet",
    "atlas_capability": "Creates LiveKit-backed realtime sessions via Atlas API; does not join Meet URLs.",
    "honest_status": "no_automated_meet_join_in_this_repo",
    "suggested_product_paths": [
        "Share a web client link in Meet chat that uses livekit_url + token from Atlas.",
        "Screen-share a browser tab running your Atlas + LiveKit UI.",
        "Evaluate Google Meet add-ons / Workspace APIs for your org (admin + compliance).",
        "Partner with a meeting-bot / media-bridge vendor if you need synthetic participants.",
    ],
    "references": [
        "https://developers.google.com/workspace/meet",
        "https://github.com/NorthModelLabs/atlas-realtime-example",
    ],
}


def main() -> int:
    print(json.dumps(GUIDE, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
