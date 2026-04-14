---
name: atlas_bridge_discord
description: "Post Atlas avatar session info via incoming webhook: text, rich embed with viewer URL, optional MP4 attachment. Use after atlas_session start or offline render — not a voice/video bot inside calls."
version: "0.2.0"
tags: ["atlas", "discord", "webhook", "bridge", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [DISCORD_WEBHOOK_URL]
      bins: [python3]
---

# Atlas → team chat (webhook bridge)

Posts to a text channel via **incoming webhook** URL. This matches an **avatar agent** story: participants open your **browser viewer** from the channel, or you attach a **short finished video** — not live streaming into voice channels.

### What gets posted (`DISCORD_MESSAGE_STYLE`)

- **Default (`DISCORD_MESSAGE_STYLE=minimal` or unset):** `bridge_note` / `discord_intro` from the JSON, plus plain Discord links for **Viewer** and **Render** when set. With `--video`, the render link is omitted (the file is the render). No `session_id` bullet list unless you switch style.
- **`DISCORD_MESSAGE_STYLE=full`:** verbose template (`session_id`, `room`, `mode`, optional `pricing`) and **rich embeds** for viewer / video URLs (same shape as before).

## What it still is **not**

- Does **not** join **voice** channels or stream realtime WebRTC into calls (needs a full bot + media gateway + bridge to LiveKit — separate product).
- Does **not** host the **browser viewer** — use your app or the planned **`viewer/`** local UI in this repo.

## Prerequisites

1. Channel → Integrations → Webhooks → copy URL.
2. `export DISCORD_WEBHOOK_URL="https://example.com/api/webhooks/..."`  # replace with your real webhook URL

## Usage

```bash
pip install -r skills/atlas-bridge-discord/requirements.txt
export DISCORD_WEBHOOK_URL="https://example.com/api/webhooks/..."
python3 skills/atlas-bridge-discord/scripts/post_session.py --file session.json
```

### Rich embed: viewer link (recommended)

Add a **HTTPS** field to the same JSON you get from Atlas (merge before posting):

| JSON field | Purpose |
|------------|---------|
| `viewer_url` or `client_url` | Your hosted page that loads the LiveKit room (token minted server-side or one-time link — **never** paste `token` into the channel). |
| `video_url` or `result_url` | Optional second embed pointing at a public or presigned MP4 URL. |
| `bridge_note` or `discord_intro` | Caption / intro (in **minimal** style this is most of the message body). |
| `pricing` | Only shown in **`full`** style (debug / billing reminder). |

Example merged payload:

```json
{
  "session_id": "…",
  "room": "…",
  "mode": "conversation",
  "viewer_url": "https://yourapp.com/avatar/abc123"
}
```

### Attach a local MP4 (offline job, under ~25 MB)

```bash
python3 skills/atlas-bridge-discord/scripts/post_session.py --file session.json --video ./out.mp4
```

The webhook provider rejects oversized files; use a link embed (`video_url`) for long renders.

## Shell tip (webhook env + pipe)

```bash
echo '{"session_id":"x","room":"r","mode":"passthrough","viewer_url":"https://example.com/v"}' \
  | DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK_URL" python3 skills/atlas-bridge-discord/scripts/post_session.py
```

## Test the webhook (no Atlas session required)

From repo root, with `DISCORD_WEBHOOK_URL` in `.env` or exported:

```bash
./scripts/bridges/test-discord-webhook.sh
```

**Text + real MP4 attachment** (tiny synthetic clip; needs `ffmpeg` on `PATH`):

```bash
./scripts/bridges/test-discord-with-mp4.sh
```

You should see one message with a playable **file** attachment (`session_id` `discord-video-smoke`).

## Security

Webhook URL is a secret. Do not commit it. Do not post LiveKit `token` values into public channels.
