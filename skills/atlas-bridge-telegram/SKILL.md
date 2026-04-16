---
name: atlas_bridge_telegram
description: "Telegram bot for Atlas avatar: /ask (Claude answer + auto-playing lip-sync MP4), /generate (verbatim MP4), /talk (realtime avatar via Web App button — opens a live viewer inside Telegram). Videos auto-play inline."
version: "0.1.0"
tags: ["atlas", "telegram", "bot", "bridge", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [TELEGRAM_BOT_TOKEN, ATLAS_API_KEY]
      bins: [python3]
---

# Atlas → Telegram (bot with auto-playing video + realtime Web App)

A Telegram bot that sends **auto-playing lip-sync videos** and opens a **realtime avatar viewer** inside Telegram via Web App buttons.

## Why Telegram?

- **Auto-playing video:** Telegram plays MP4 inline automatically — no click needed. The avatar video just appears and plays in the chat.
- **Web App (Mini App):** `/talk` sends an inline button that opens a full WebRTC viewer **inside Telegram** (or in browser). The user taps one button and they're talking to the avatar in real time.
- **Simple bot API:** No OAuth dance, no privileged intents, no invite URL ceremony — just a BotFather token.

## Features

| Command | What happens |
|---------|-------------|
| `/ask <question>` | **Claude** answers → offline lip-sync **MP4 auto-plays** in chat |
| `/generate <script>` | Verbatim script → offline lip-sync **MP4 auto-plays** |
| `/talk` | Creates a **realtime** Atlas session → sends a **"Talk to Avatar" Web App button** (opens inline viewer with mic + video) |
| **Plain text** | Same as `/ask` — any message triggers Claude + video |

## Prerequisites

1. **BotFather** — open [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow prompts, copy the **token**.
2. **Atlas API key** — [dashboard.northmodellabs.com/dashboard/keys](https://dashboard.northmodellabs.com/dashboard/keys).
3. **For `/talk` (realtime):** deploy [atlas-avatar-viewer](https://github.com/NorthModelLabs/atlas-avatar-viewer) (single static HTML, free on Vercel/Cloudflare) and set `ATLAS_VIEWER_BASE_URL`.

## Setup

```bash
pip install -r skills/atlas-bridge-telegram/requirements.txt
```

In `.env` (never commit):

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
ATLAS_API_KEY=ak_...

# For /ask — LLM (pick one):
HELICONE_API_KEY=sk-helicone-...       # Helicone AI Gateway (default)
# ANTHROPIC_API_KEY=sk-ant-...          # direct Anthropic
# HELICONE_ANTHROPIC_PROXY=1            # legacy proxy (both keys)

# For /talk — realtime viewer:
ATLAS_VIEWER_BASE_URL=https://your-avatar-app.vercel.app

# Optional — real speech instead of test tone:
# ELEVENLABS_API_KEY=...
# ELEVENLABS_VOICE_ID=...
# ATLAS_OFFLINE_IMAGE=/path/to/face.jpg
```

## Run

```bash
./scripts/bridges/run-telegram-avatar-bot.sh
```

Or directly:

```bash
python3 skills/atlas-bridge-telegram/scripts/telegram_avatar_bot.py
```

The bot uses **long polling** — keep the process running. Stdout shows status on startup.

## How `/talk` works (realtime Web App)

1. User sends `/talk`
2. Bot calls `atlas_session.py start` → gets `session_id`, `livekit_url`, `token`, `room`
3. Bot sends a message with two buttons:
   - **"Talk to Avatar"** — Telegram Web App button (opens `ATLAS_VIEWER_BASE_URL/watch/<session_id>` inline in Telegram)
   - **"Open in Browser"** — fallback URL button
4. User taps the button → WebRTC viewer loads → mic access → they're talking to the avatar live
5. When done, the session should be ended (`leave`) to stop billing

Without `ATLAS_VIEWER_BASE_URL`, the bot still creates the session but returns raw LiveKit credentials (useful for debugging).

## How video auto-play works

Telegram auto-plays short videos (< 50 MB) inline in the chat — no tap required. The bot sends videos using `reply_video` with `supports_streaming=True`, which enables progressive playback. The avatar just starts talking in the chat thread.

## Security

- **`TELEGRAM_BOT_TOKEN`** is a secret — treat like a password.
- Do not send raw LiveKit `token` values in chat; the bot redacts them when no viewer URL is set.
- Rate-limit access to the bot if renders cost money (Telegram bots can restrict to specific chat IDs via middleware).

## What this is not

- **Not a voice-channel bot** — does not join Telegram voice chats or group calls. Videos are offline-rendered MP4s; realtime uses a Web App viewer.
- **Not a webhook bot** — uses long polling (simpler setup, no HTTPS endpoint needed for the bot itself).
