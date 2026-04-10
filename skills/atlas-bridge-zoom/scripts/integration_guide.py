#!/usr/bin/env python3
"""Emit JSON guidance for Atlas + Zoom (no Zoom join implementation)."""
from __future__ import annotations

import json

GUIDE = {
    "platform": "zoom",
    "atlas_capability": "Creates LiveKit-backed realtime sessions via Atlas API; does not join zoom.us links.",
    "honest_status": "no_automated_zoom_join_in_this_repo",
    "suggested_product_paths": [
        "Share your Atlas/LiveKit web client link in Zoom chat.",
        "Screen-share a browser tab with the avatar UI.",
        "Use Zoom Marketplace / SDK documentation for certified meeting integrations.",
        "Use a meeting-bot vendor if you require a synthetic participant.",
    ],
    "references": [
        "https://developers.zoom.us/",
        "https://github.com/NorthModelLabs/atlas-realtime-example",
    ],
}


def main() -> int:
    print(json.dumps(GUIDE, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
