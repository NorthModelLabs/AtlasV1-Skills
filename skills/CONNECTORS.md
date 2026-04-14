# Connector skills (Slack, Discord)

| Skill folder | What it does |
|--------------|----------------|
| `atlas-bridge-slack` | **Working:** post session summary via **incoming webhook** (`SLACK_WEBHOOK_URL`). |
| `atlas-bridge-discord` | **Working:** post session summary + optional **embed** (`viewer_url`) + optional **MP4 attach** via **incoming webhook** (`DISCORD_WEBHOOK_URL`). |

Slack is **per-workspace** (manifest + `.env`); it is **not** distributed as a global Slack App Directory listing from this repo — see root **README.md** (*Distribution: Slack App Directory vs this repo*).

Copy any folder into your OpenClaw `skills/` directory alongside `atlas-avatar`:

```bash
cp -R skills/atlas-bridge-slack ~/.openclaw/workspace/skills/
```

**Smoke-test webhooks:** `./scripts/bridges/test-slack-webhook.sh` / `./scripts/bridges/test-discord-webhook.sh` (loads `.env`; no Atlas call). **Video:** `./scripts/bridges/test-slack-video-link.sh` (URL in text), `./scripts/bridges/test-discord-with-mp4.sh` (MP4 attach, needs `ffmpeg`). **Atlas offline → Discord:** `./scripts/bridges/atlas-offline-to-discord.sh` (needs `ATLAS_API_KEY` + `DISCORD_WEBHOOK_URL`). **Atlas offline → Slack:** `./scripts/bridges/atlas-offline-to-slack.sh` — MP4 attachment needs **`BOT_OAUTH_TOKEN`** + **`SLACK_CHANNEL_ID`** + bot scopes `files:write` and `chat:write`; otherwise only a **link** is posted (Slack webhooks cannot attach video).

**Flow:** create session with `atlas_session.py start … > session.json`, then `post_session.py` for webhook bridges. For a **local browser viewer** (mic + avatar on your machine), see **`viewer/README.md`** (planned default UI in this repo).

Synthetic participants inside Zoom/Meet/Teams require **vendor SDKs or a separate bot product** — not shipped here; Atlas stays **HTTP + LiveKit** from your own viewer or app.
