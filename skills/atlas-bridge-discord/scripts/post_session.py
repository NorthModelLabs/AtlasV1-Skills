#!/usr/bin/env python3
"""Post Atlas session info via incoming webhook: text + optional embeds + optional video file.

Webhook cannot join voice or stream live video into a call. For an *avatar agent* workflow:
  - Put ``viewer_url`` (or ``client_url``) in the JSON — your hosted page that connects to
    LiveKit server-side or via short-lived links (never paste ``token`` into the channel).
  - Optional ``--video`` attaches a finished MP4 (e.g. offline job) if under the provider’s limit.

**Message style:** ``DISCORD_MESSAGE_STYLE`` — ``minimal`` (default): caption / links only, no
session_id bullets. Set ``full`` for verbose debug layout + rich embeds.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from pathlib import Path

import requests

# Typical incoming-webhook attachment limit (MiB); confirm with your provider’s docs.
MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024


def _discord_message_style() -> str:
    return (os.environ.get("DISCORD_MESSAGE_STYLE", "minimal") or "minimal").strip().lower()


def _embeds_from_json(data: dict) -> list[dict]:
    out: list[dict] = []
    viewer = (data.get("viewer_url") or data.get("client_url") or "").strip()
    if viewer:
        out.append(
            {
                "title": "Open avatar (browser)",
                "description": (
                    "Hosted viewer — keep LiveKit tokens off public channels; "
                    "issue short-lived links or embed credentials server-side."
                ),
                "url": viewer,
                "color": 0x5865F2,
            }
        )
    video_url = (data.get("video_url") or data.get("result_url") or "").strip()
    if video_url:
        out.append(
            {
                "title": "Video / render link",
                "url": video_url,
                "description": "Public or signed URL to a finished render (optional).",
            }
        )
    return out


def _build_body_minimal(data: dict, *, has_video_attachment: bool) -> tuple[str, list[dict]]:
    """Caption + plain Discord links; no rich embeds, no session_id block."""
    bridge = (data.get("bridge_note") or data.get("discord_intro") or "").strip()
    viewer = (data.get("viewer_url") or data.get("client_url") or "").strip()
    render = (data.get("video_url") or data.get("result_url") or "").strip()
    parts: list[str] = []
    if bridge:
        parts.append(bridge)
    if viewer:
        parts.append(f"**Viewer:** <{viewer}>")
    if render and not has_video_attachment:
        parts.append(f"**Render:** <{render}>")
    text = "\n\n".join(parts).strip()
    if not text:
        mode = str(data.get("mode") or "").lower()
        text = "Atlas offline clip attached." if mode == "offline" else "Atlas session update."
    return text, []


def _build_body_full(data: dict) -> tuple[str, list[dict]]:
    sid = data.get("session_id", "?")
    room = data.get("room", "?")
    mode = data.get("mode", "?")
    pricing = data.get("pricing", "")
    bridge = (data.get("bridge_note") or data.get("discord_intro") or "").strip()
    lines = ["**Atlas avatar session**"]
    if bridge:
        lines.append(bridge)
    lines += [
        f"• session_id: `{sid}`",
        f"• room: `{room}`",
        f"• mode: `{mode}`",
    ]
    if pricing:
        lines.append(f"• pricing: {pricing}")
    embeds = _embeds_from_json(data)
    if not embeds:
        lines.append(
            "• Add **`viewer_url`** (HTTPS) to this JSON for a clickable in-channel link to your web viewer."
        )
        lines.append(
            "• Or use **`--video`** with a short MP4 from an offline job (under 25 MB)."
        )
    return "\n".join(lines), embeds


def main() -> int:
    p = argparse.ArgumentParser(
        description="Post Atlas session summary via webhook (embeds + optional MP4 attach)",
    )
    p.add_argument("--file", "-f", help="Path to JSON file (else stdin)")
    p.add_argument(
        "--video",
        metavar="PATH",
        help="Attach local MP4/video file (max ~25 MB; typical for offline /v1/generate output)",
    )
    args = p.parse_args()
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        print("Set DISCORD_WEBHOOK_URL", file=sys.stderr)
        return 2
    if args.file:
        raw = Path(args.file).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    data = json.loads(raw)

    video_path = Path(args.video).resolve() if args.video else None
    if video_path is not None:
        if not video_path.is_file():
            print(f"Error: --video not a file: {video_path}", file=sys.stderr)
            return 2
        n = video_path.stat().st_size
        if n > MAX_ATTACHMENT_BYTES:
            print(
                f"Error: file {n} bytes exceeds webhook attachment limit (~25 MB).",
                file=sys.stderr,
            )
            return 2

    has_vid = video_path is not None
    if _discord_message_style() == "full":
        content, embeds = _build_body_full(data)
    else:
        content, embeds = _build_body_minimal(data, has_video_attachment=has_vid)

    body: dict = {"content": content}
    if embeds:
        body["embeds"] = embeds

    if video_path is not None:
        mime = mimetypes.guess_type(str(video_path))[0] or "application/octet-stream"
        with video_path.open("rb") as fh:
            r = requests.post(
                url,
                data={"payload_json": json.dumps(body)},
                files={"files[0]": (video_path.name, fh, mime)},
                timeout=120,
            )
    else:
        r = requests.post(url, json=body, timeout=30)

    if not r.ok:
        print(r.text, file=sys.stderr)
        return 3
    print(json.dumps({"ok": True, "http_status": r.status_code}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
