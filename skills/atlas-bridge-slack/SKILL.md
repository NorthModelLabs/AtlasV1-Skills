---
name: atlas_bridge_slack
description: "Post an Atlas realtime session summary (WebRTC / LiveKit join hints) to a team channel via incoming webhook. Use when the user wants a channel notification or to bridge Atlas session info after creating a session with atlas-avatar."
version: "0.1.0"
tags: ["atlas", "slack", "webhook", "bridge", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [SLACK_WEBHOOK_URL]
      bins: [python3]
---

# Atlas → team chat (incoming webhook)

This skill does **not** join voice/huddle calls or inject video. It **posts a message** to a channel using an **incoming webhook** URL (create one in your chat provider’s integrations UI).

## Prerequisites (Slack webhook URL)

Yes — Slack needs a **Slack app** (one minute) so you get an **Incoming Webhook URL**. Same *idea* as Discord’s webhook URL, but Slack’s UI is heavier.

**Fast path — use this repo’s manifest**

1. Open [Your Apps](https://api.slack.com/apps) → **Create New App** → **From a manifest**.
2. Pick your workspace → paste **YAML** from **`skills/atlas-bridge-slack/slack-app-manifest.yaml`** or **JSON** from **`skills/atlas-bridge-slack/slack-app-manifest.json`** (Slack accepts either in “From a manifest”).
3. **Create** → left sidebar **Install App** → **Install to Workspace** (approve).
4. Left sidebar **Incoming Webhooks** → turn **On** if needed → **Add New Webhook to Workspace** → pick the **channel** → **Allow**.
5. Copy **Webhook URL** (`https://hooks.slack.com/services/...`) → put in `.env` as `SLACK_WEBHOOK_URL=...` (never commit `.env`).

**Manual path** — **Create New App** → **From scratch** → name it → **Incoming Webhooks** → enable → install → add webhook to channel → copy URL.

Official reference: [Incoming webhooks for Slack](https://api.slack.com/messaging/webhooks).

Then:

`export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."`  # your real URL

## Where each value lives (api.slack.com → your app)

Use the **left sidebar** inside [Your Apps](https://api.slack.com/apps) → select **Atlas Avatar Bridge** (or your app name).

| You need | Slack UI location | Notes |
|----------|-------------------|--------|
| **`SLACK_WEBHOOK_URL`** | **Features → Incoming Webhooks** → *Add New Webhook to Workspace* | `https://hooks.slack.com/services/…` — text posts + link-only video. |
| **`BOT_OAUTH_TOKEN`** (`xoxb-…`) | **Features → OAuth & Permissions** → scroll to **Bot User OAuth Token** | **Not** on *Settings → Basic Information*. Only appears after **Install App → Install to Workspace**. Treat like a password. |
| **`SLACK_CHANNEL_ID`** (`C…`) | Open the channel in **Slack** (browser or desktop). From the **browser URL**: `…/client/T…/C01234ABCDE/…` — the segment starting with **`C`** is the channel ID. | The bot must be **in** the channel: run `/invite @YourAppName` there. |
| **App ID / Client ID / Client Secret / Signing Secret** | **Settings → Basic Information** → *App Credentials* | **Not used** by `post_session.py` today (webhook + bot file upload). Keep them private anyway; you’d need them for a full OAuth redirect flow on your own server. |

After you change **OAuth Scopes** (e.g. add `files:write`), open **Install App** and **Reinstall** so the `xoxb-` token picks up new permissions.

## Usage

After `atlas_session.py start` (or equivalent), pipe or pass the JSON:

```bash
export SLACK_WEBHOOK_URL="https://hooks.example.invalid/services/..."
python3 skills/atlas-bridge-slack/scripts/post_session.py < session.json
# or
python3 skills/atlas-bridge-slack/scripts/post_session.py --file session.json
```

**Install deps:** `pip install -r skills/atlas-bridge-slack/requirements.txt`

## What gets posted

- **Default (`SLACK_MESSAGE_STYLE=minimal` or unset):** only `bridge_note` / `slack_intro` from the JSON (your caption), plus an offline **link** on webhook posts if `result_url` / `video_url` is set. No `session_id` bullets unless you switch style.
- **`SLACK_MESSAGE_STYLE=full`:** verbose template (`session_id`, `room`, `mode`, pricing, LiveKit reminder) for debugging.

## Offline / generated video

**Incoming Webhooks cannot upload MP4 file bytes** and usually **do not** unfurl a playable inline video for arbitrary presigned storage URLs — you get a long link; open it in a browser to play.

**Option A — link only (webhook):** add **`video_url`** or **`result_url`** to the JSON, or pass **`--video-url https://…`**.

**Option B — upload MP4 like Discord (bot token):** set **`BOT_OAUTH_TOKEN`** (or **`SLACK_BOT_TOKEN`**) with scopes **`files:write`** + **`chat:write`**, **`SLACK_CHANNEL_ID`** (starts with `C`), `/invite` the app bot to that channel, then:

```bash
python3 skills/atlas-bridge-slack/scripts/post_session.py -f session.json --video ./render.mp4
```

Update the app manifest (`slack-app-manifest.yaml`) after adding scopes, **reinstall** the app to workspace, then copy the **Bot User OAuth Token** (`xoxb-…`) into `.env`.

**One-shot:** `./scripts/bridges/atlas-offline-to-slack.sh "Intro"` — bot MP4 upload when **`BOT_OAUTH_TOKEN`** + **`SLACK_CHANNEL_ID`** are set; otherwise webhook + link only.

**Audio:** default is a **1 s fixture tone**. For speech set **`ATLAS_OFFLINE_SPEAK_TEXT`** (uses **`ELEVENLABS_API_KEY`** + **`scripts/elevenlabs_to_wav.py`**), or **`ATLAS_OFFLINE_AUDIO`**, or use **`scripts/bridges/atlas-narrated-avatar-to-discord.sh`** for the full Discord pipeline.

**Public Slack App Directory:** this skill is **not** a listed Slack Marketplace product — each workspace installs **its own** app from the manifest here. See the root **README.md** section *Distribution: Slack App Directory vs this repo*.

## Test the webhook (no Atlas session required)

From repo root, with `SLACK_WEBHOOK_URL` in `.env` or exported:

```bash
./scripts/bridges/test-slack-webhook.sh
```

Link + text smoke (optional URL argument, else placeholder):

```bash
./scripts/bridges/test-slack-video-link.sh 'https://YOUR-PRESIGNED-MP4-URL'
```

You should see one message in the Slack channel tied to that webhook (fake `session_id` `atlas-bridge-smoke`).

## Security

- Treat `SLACK_WEBHOOK_URL` as a secret (same power as posting to the channel).
- Do not paste LiveKit JWTs into public channels if your policy forbids it.
