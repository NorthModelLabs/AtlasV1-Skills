---
name: atlas_bridge_discord
description: "Post Atlas avatar session info via incoming webhook, or run an optional Discord bot: /ask, @mention, reply-to-bot (Claude + lip-sync MP4); /generate (verbatim); /talk (realtime avatar viewer); /endtalk. Not a voice-channel bot."
version: "0.3.0"
tags: ["atlas", "discord", "webhook", "bridge", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [DISCORD_WEBHOOK_URL]
      bins: [python3]
---

# Atlas → team chat (webhook + optional bot)

**Webhook** — post to a channel via **incoming webhook** URL (one-way): session summary, links, optional MP4 attach.

**Optional bot** (`skills/atlas-bridge-discord/scripts/discord_avatar_bot.py`) — **24/7 process you host** (e.g. `./scripts/bridges/run-discord-avatar-bot.sh`). Slash **`/ask`** or **`@BotName …`**: **Claude** → **Answer:** + MP4 (avatar speaks the answer). **Reply** to any bot message with text: same with prior message as context. Slash **`/generate`**: **verbatim** script → MP4. **`/talk`**: start a **realtime** avatar session and get a viewer link (set **`ATLAS_VIEWER_BASE_URL`** to your deployed [atlas-avatar-viewer](https://github.com/NorthModelLabs/atlas-avatar-viewer)). **`/endtalk`**: close the session (stops billing). LLM paths need **`HELICONE_API_KEY`** (default: Helicone AI Gateway) or **`ANTHROPIC_API_KEY`** (direct); optional **`HELICONE_ANTHROPIC_PROXY=1`** with both keys for legacy **`anthropic.helicone.ai`**. **`DISCORD_MESSAGE_CONTENT_INTENT=1`** + Portal toggle for replies and @mentions.

### What gets posted (`DISCORD_MESSAGE_STYLE`)

- **Default (`DISCORD_MESSAGE_STYLE=minimal` or unset):** `bridge_note` / `discord_intro` from the JSON, plus plain Discord links for **Viewer** and **Render** when set. With `--video`, the render link is omitted (the file is the render). No `session_id` bullet list unless you switch style.
- **`DISCORD_MESSAGE_STYLE=full`:** verbose template (`session_id`, `room`, `mode`, optional `pricing`) and **rich embeds** for viewer / video URLs (same shape as before).

## What it still is **not**

- Does **not** join **voice** channels or stream realtime WebRTC into calls (needs a full bot + media gateway + bridge to LiveKit — separate product).
- Does **not** host the **browser viewer** — deploy **[atlas-avatar-viewer](https://github.com/NorthModelLabs/atlas-avatar-viewer)** and set `ATLAS_VIEWER_BASE_URL` for `/talk`.

## Prerequisites (webhook)

1. Channel → Integrations → Webhooks → copy URL.
2. `export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."`  # your real webhook URL

## Interactive bot (optional)

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application** → **Bot** → copy **Token** → `DISCORD_BOT_TOKEN` in `.env` (never commit).
2. **Privileged Gateway Intents** → enable **Message Content Intent** in the Portal **only if** you want **@mention** text; in `.env` also set **`DISCORD_MESSAGE_CONTENT_INTENT=1`** (the bot keeps this intent off by default so login works before you toggle the Portal). **`/ask`** works without Message Content.
3. **OAuth2 → URL Generator** (not the short **Installation** link alone): scopes **`bot`** + **`applications.commands`**; if shown, **Integration type → Guild install**; bot permissions at least **Send Messages**, **Attach Files**, **Read Message History**, **Use Slash Commands**, and **View channel**. The **Generated URL** must include `scope=bot` and `applications.commands` — otherwise the app can appear under Integrations with **“no bot in this server”**, `@mention` will not work, and the Python bot logs **`in 0 server(s)`**. Open the long URL, authorize into your server.
4. `pip install -r skills/atlas-bridge-discord/requirements.txt` (includes `discord.py`).
5. `./scripts/bridges/run-discord-avatar-bot.sh` from repo root (loads `.env`, optional venv).

**Slash commands:** Global registration can lag; Discord may show **“This command is outdated”** until the client refreshes — **reload Discord (Ctrl+R)** and re-pick the command from `/`. Set **`DISCORD_GUILD_ID`** in `.env` (your server’s numeric id) to register **`/ask`** and **`/generate`** only in that server — **sync is immediate** (see root README). **@mentions** work once the bot is online if **Message Content Intent** is enabled.

**Env:** `DISCORD_BOT_TOKEN`, `ATLAS_API_KEY`; for **`/ask`** / **reply-to-bot**: `HELICONE_API_KEY` (gateway default) or `ANTHROPIC_API_KEY` (direct). `LLM_MODEL` defaults to `claude-sonnet-4` (gateway) or `claude-sonnet-4-20250514` (native). `HELICONE_ANTHROPIC_PROXY=1` + both keys → legacy proxy. Optional `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID`, `ATLAS_OFFLINE_IMAGE`. For **`/talk`**: `ATLAS_VIEWER_BASE_URL` (deployed [atlas-avatar-viewer](https://github.com/NorthModelLabs/atlas-avatar-viewer)).

## Usage (webhook)

```bash
pip install -r skills/atlas-bridge-discord/requirements.txt
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
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
  "mode": "passthrough",
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

Webhook URL and **bot token** are secrets — do not commit them. Do not post LiveKit `token` values into public channels. Rate-limit or restrict the bot to trusted channels if renders cost money.
