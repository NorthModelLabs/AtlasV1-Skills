#!/usr/bin/env python3
"""Post Atlas realtime session JSON to an incoming webhook (team chat).

Optional: upload a local MP4 with a **bot token** (``BOT_OAUTH_TOKEN`` / ``SLACK_BOT_TOKEN``)
+ ``SLACK_CHANNEL_ID`` using Slack's external file upload API — Incoming Webhooks cannot attach bytes.

**Message style:** ``SLACK_MESSAGE_STYLE`` — ``minimal`` (default): ``bridge_note`` / ``slack_intro`` only,
plus optional render link for webhooks. Set ``full`` for session_id / room / mode / LiveKit debug lines.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests


def _slack_bot_token() -> str:
    return (
        os.environ.get("SLACK_BOT_TOKEN", "").strip()
        or os.environ.get("SLACK_BOT_OAUTH_TOKEN", "").strip()
        or os.environ.get("BOT_OAUTH_TOKEN", "").strip()
    )


def _slack_message_style() -> str:
    return (os.environ.get("SLACK_MESSAGE_STYLE", "minimal") or "minimal").strip().lower()


def _format_message_full(data: dict, *, render_link: str) -> list[str]:
    sid = data.get("session_id", "?")
    room = data.get("room", "?")
    mode = data.get("mode", "?")
    pricing = data.get("pricing", "")
    note = (data.get("bridge_note") or data.get("slack_intro") or "").strip()
    lines = [
        "*Atlas realtime session*",
        f"• session_id: `{sid}`",
        f"• room: `{room}`",
        f"• mode: `{mode}`",
    ]
    if note:
        lines.append(note)
    if pricing:
        lines.append(f"• pricing: {pricing}")
    lines.append(
        "• Connect your LiveKit client with `livekit_url` + `token` from the full JSON (omit from channel if sensitive)."
    )
    if render_link:
        lines.append(f"• offline render (link): {render_link}")
    return lines


def _format_message_minimal(data: dict, *, render_link: str) -> list[str]:
    """Human-facing default: caption / spoken line only, optional link (webhook path)."""
    note = (data.get("bridge_note") or data.get("slack_intro") or "").strip()
    link = (render_link or "").strip()
    if note and link:
        return [note, link]
    if note:
        return [note]
    if link:
        return [link]
    mode = str(data.get("mode") or "").lower()
    if mode == "offline":
        return ["Atlas offline clip attached."]
    return ["Atlas session update."]


def _format_message(data: dict, *, render_link: str) -> list[str]:
    if _slack_message_style() == "full":
        return _format_message_full(data, render_link=render_link)
    return _format_message_minimal(data, render_link=render_link)


def _initial_comment_from_lines(lines: list[str]) -> str:
    text = "\n".join(lines).strip()
    return text if text else " "


def _slack_upload_mp4_to_channel(
    bot_token: str,
    channel_id: str,
    mp4: Path,
    *,
    initial_comment: str,
) -> None:
    """Slack: files.getUploadURLExternal → POST bytes → files.completeUploadExternal."""
    mp4 = mp4.expanduser().resolve()
    if not mp4.is_file():
        raise FileNotFoundError(mp4)
    size = mp4.stat().st_size
    if size < 1:
        raise ValueError("empty file")
    fn = mp4.name
    auth = {"Authorization": f"Bearer {bot_token}"}
    r1 = requests.post(
        "https://slack.com/api/files.getUploadURLExternal",
        headers=auth,
        data={"filename": fn, "length": str(size)},
        timeout=60,
    )
    j1 = r1.json()
    if not j1.get("ok"):
        raise RuntimeError(f"getUploadURLExternal: {j1.get('error', r1.text[:500])}")
    upload_url = j1["upload_url"]
    file_id = j1["file_id"]

    body = mp4.read_bytes()
    # Slack upload URLs expect raw bytes or multipart; raw binary is most reliable.
    r2 = requests.post(
        upload_url,
        data=body,
        headers={"Content-Type": "video/mp4"},
        timeout=600,
    )
    if r2.status_code != 200:
        with mp4.open("rb") as fh:
            r2 = requests.post(upload_url, files={"file": (fn, fh, "video/mp4")}, timeout=600)
        if r2.status_code != 200:
            raise RuntimeError(f"upload to Slack storage failed: HTTP {r2.status_code} {r2.text[:300]}")

    r3 = requests.post(
        "https://slack.com/api/files.completeUploadExternal",
        headers={**auth, "Content-Type": "application/json"},
        json={
            "files": [{"id": file_id, "title": fn}],
            "channel_id": channel_id,
            "initial_comment": initial_comment[:12000],
        },
        timeout=120,
    )
    j3 = r3.json()
    if not j3.get("ok"):
        raise RuntimeError(f"completeUploadExternal: {j3.get('error', r3.text[:500])}")


def main() -> int:
    p = argparse.ArgumentParser(description="Post Atlas session summary to incoming webhook")
    p.add_argument("--file", "-f", help="Path to JSON file (else stdin)")
    p.add_argument(
        "--video-url",
        default="",
        metavar="URL",
        help="Append this render URL to the message (Incoming Webhooks cannot upload file bytes)",
    )
    p.add_argument(
        "--video",
        metavar="PATH",
        help="Local MP4: requires BOT_OAUTH_TOKEN (or SLACK_BOT_TOKEN) + SLACK_CHANNEL_ID; uses Web API upload (not the webhook).",
    )
    args = p.parse_args()
    if args.file:
        raw = open(args.file, encoding="utf-8").read()
    else:
        raw = sys.stdin.read()
    data = json.loads(raw)

    render = (
        (args.video_url or "").strip()
        or (data.get("video_url") or data.get("result_url") or "").strip()
    )

    if getattr(args, "video", None):
        bot = _slack_bot_token()
        ch = os.environ.get("SLACK_CHANNEL_ID", "").strip()
        if not bot or not ch:
            print(
                "For --video, set SLACK_CHANNEL_ID (channel ID like C0…) and a bot token:\n"
                "  BOT_OAUTH_TOKEN=xoxb-…   (OAuth & Permissions → Bot User OAuth Token)\n"
                "Also add bot scopes files:write + chat:write, reinstall the app, and /invite the bot to the channel.",
                file=sys.stderr,
            )
            return 2
        path = Path(args.video)
        # Omit long presigned URL in text when the MP4 is attached.
        lines = _format_message(data, render_link="")
        try:
            _slack_upload_mp4_to_channel(bot, ch, path, initial_comment=_initial_comment_from_lines(lines))
        except Exception as e:
            print(str(e), file=sys.stderr)
            return 3
        print(json.dumps({"ok": True, "via": "files.completeUploadExternal"}))
        return 0

    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not url:
        print("Set SLACK_WEBHOOK_URL (or use --video with bot token + SLACK_CHANNEL_ID)", file=sys.stderr)
        return 2

    lines = _format_message(data, render_link=render)
    payload = {"text": "\n".join(lines)}
    r = requests.post(url, json=payload, timeout=30)
    if not r.ok:
        print(r.text, file=sys.stderr)
        return 3
    print(json.dumps({"ok": True, "http_status": r.status_code}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
