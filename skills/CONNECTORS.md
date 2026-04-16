# Connector skills (Slack, Discord, Telegram)

| Skill folder | What it does |
|--------------|----------------|
| `atlas-bridge-slack` | **Working:** post session summary via **incoming webhook** (`SLACK_WEBHOOK_URL`). |
| `atlas-bridge-discord` | **Working:** incoming **webhook** + optional **bot** (`DISCORD_BOT_TOKEN`): **`/ask`**, **@mention**, **reply to bot** (Claude + MP4), **`/generate`** (verbatim MP4), **`/talk`** (realtime avatar viewer link), **`/endtalk`** (close session). |
| `atlas-bridge-telegram` | **Working:** **bot** (`TELEGRAM_BOT_TOKEN`): **`/ask`** (Claude + **auto-playing** MP4), **`/generate`** (verbatim MP4), **`/talk`** (realtime avatar via **Web App button** inside Telegram), **plain text** = `/ask`. |

Slack is **per-workspace** (manifest + `.env`); it is **not** distributed as a global Slack App Directory listing from this repo — see root **README.md** (*Distribution: Slack App Directory vs this repo*).

Copy any folder into your OpenClaw `skills/` directory alongside `atlas-avatar`:

```bash
cp -R skills/atlas-bridge-telegram ~/.openclaw/workspace/skills/
```

**Smoke-test webhooks:** `./scripts/bridges/test-slack-webhook.sh` / `./scripts/bridges/test-discord-webhook.sh` (loads `.env`; no Atlas call). **Video:** `./scripts/bridges/test-slack-video-link.sh` (URL in text), `./scripts/bridges/test-discord-with-mp4.sh` (MP4 attach, needs `ffmpeg`). **Atlas offline → Discord:** `./scripts/bridges/atlas-offline-to-discord.sh` (needs `ATLAS_API_KEY` + `DISCORD_WEBHOOK_URL`). **Discord bot (interactive):** `./scripts/bridges/run-discord-avatar-bot.sh` — needs **`DISCORD_BOT_TOKEN`** + **`ATLAS_API_KEY`**; see `skills/atlas-bridge-discord/SKILL.md`. **Telegram bot:** `./scripts/bridges/run-telegram-avatar-bot.sh` — needs **`TELEGRAM_BOT_TOKEN`** + **`ATLAS_API_KEY`**; optional **`ATLAS_VIEWER_BASE_URL`** for realtime `/talk` button; see `skills/atlas-bridge-telegram/SKILL.md`. **Atlas offline → Slack:** `./scripts/bridges/atlas-offline-to-slack.sh` — MP4 attachment needs **`BOT_OAUTH_TOKEN`** + **`SLACK_CHANNEL_ID`** + bot scopes `files:write` and `chat:write`; otherwise only a **link** is posted (Slack webhooks cannot attach video).

**Realtime viewer:** Deploy **[atlas-avatar-viewer](https://github.com/NorthModelLabs/atlas-avatar-viewer)** (single static HTML, free on Vercel/Cloudflare) and set **`ATLAS_VIEWER_BASE_URL`** in `.env`. Both the Discord and Telegram bots use this for `/talk`. For a full-featured local viewer with UI controls, see **[atlas-realtime-example](https://github.com/NorthModelLabs/atlas-realtime-example)**.

**Flow:** create session with `atlas_session.py start … > session.json`, then `post_session.py` for webhook bridges.

Synthetic participants inside Zoom/Meet/Teams require **vendor SDKs or a separate bot product** — not shipped here; Atlas stays **HTTP + LiveKit** from your own viewer or app.
