# Atlas Avatar skills (OpenClaw & agents)

Open-source **skills** and **CLI tools** for AI coding agents ([OpenClaw](https://docs.openclaw.ai), terminal coding agents, etc.) that call the **[North Model Labs](https://www.northmodellabs.com/) Atlas API** — realtime **WebRTC (LiveKit-shaped join info from Atlas)** sessions and **offline** lip-sync video jobs (GPU warping, TTS integrations).

**Where to start**

| You want… | Go to |
|-----------|--------|
| OpenClaw / skill install | **Getting started** below + `skills/atlas-avatar/SKILL.md` |
| A terminal coding agent driving shell | `claude-code-avatar/README.md` + root `CLAUDE.md` |
| Raw HTTP / curl | `skills/atlas-avatar/references/api-reference.md`, `core/atlas_cli.py --help` |
| Slack / Discord webhooks, **optional Discord bot** (`/ask` + @mention = LLM answer + video; `/generate` = verbatim), offline MP4 | This README ([Discord bot setup](#discord-webhook-vs-interactive-bot)), `skills/CONNECTORS.md`, `skills/atlas-bridge-discord/SKILL.md`, `scripts/bridges/` |
| Slack “marketplace” / public listing | **Not from this repo** — see [Distribution](#distribution-slack-app-directory-vs-this-repo) below |
| Local browser viewer (planned) | `viewer/README.md` |

This pack is **API-first**: you get `livekit_url`, `token`, and `room` from Atlas, then connect a **browser or app** you control. It is **not** a drop-in “synthetic participant joins Zoom/Meet/Teams” product (see [Scope](#scope-realtime-vs-meeting-products) below).

---

## What is Atlas?

**Atlas** is North Model Labs’ developer API for AI avatars:

- **Realtime (passthrough)** — `POST /v1/realtime/session` with **`mode: passthrough`** returns LiveKit credentials; you bring **STT / LLM / TTS** and publish audio; Atlas provides **GPU lip-sync** video.
- **Offline** — `POST /v1/generate` queues lip-sync video from your audio + image; poll jobs and fetch a presigned result URL.
- **Face swap mid-session** — `PATCH /v1/realtime/session/{id}` with a new face image.

**Base URL (default):** `https://api.atlasv1.com` — override with `ATLAS_API_BASE` if your deployment differs.

**Who built this repo?** Maintained by **[North Model Labs](https://www.northmodellabs.com/)** (`northmodellabs` on GitHub) for OpenClaw/agent workflows. **License:** MIT — see [LICENSE](LICENSE).

---

## Pricing & dashboard

| What | Where |
|------|--------|
| **API keys** | Create and rotate keys in the Atlas dashboard — e.g. [dashboard.northmodellabs.com/dashboard/keys](https://dashboard.northmodellabs.com/dashboard/keys) (your org may use a host like `dashboard.atlasv1.com`). Keys look like `ak_` + hex. |
| **Rates** | Do **not** hardcode prices in agents. Use the **`pricing`** string on realtime responses and billing info from **`GET /v1/me`** / your dashboard — tiers depend on `mode` and product. |
| **Usage** | Monitor consumption in the same dashboard as your API keys. |

---

## What are skills?

**Skills** are self-contained folders an agent can load. Each skill typically has:

| Piece | Role |
|--------|------|
| **`SKILL.md`** | When to use the skill, safety notes, and step-by-step flows (OpenClaw reads this). |
| **`scripts/`** | Small CLIs (`atlas_session.py`), webhook smoke tests, offline→Discord wrappers — see `scripts/README.md`. |
| **`requirements.txt`** | Python deps (usually `requests`). |

Copy a skill into your agent workspace (e.g. `~/.openclaw/workspace/skills/`) or publish/install via [ClawHub](https://docs.openclaw.ai/tools/clawhub).

---

## Available skills (this repo)

| Skill | Pricing (source of truth) | What it does |
|-------|---------------------------|--------------|
| **`skills/atlas-avatar/`** | Dashboard + API `pricing` / `GET /v1/me` | Core Atlas API: realtime sessions, **`POST …/viewer`** watch tokens, offline jobs, jobs poll, face-swap — `SKILL.md` + **`atlas_session.py`** verb CLI + **`run_atlas_cli.py`**. |
| **`skills/atlas-bridge-slack/`** | Webhook + your Slack app (provider billing is yours) | **Incoming webhook** text/link + optional **bot token** MP4 upload (`post_session.py`, `scripts/bridges/atlas-offline-to-slack.sh`). |
| **`skills/atlas-bridge-discord/`** | Webhook only | Post summary + optional **`viewer_url`** embed + optional **MP4** attach; optional **bot**: **`/ask`** + **@mention** (Claude answer → lip-sync), **`/generate`** (verbatim script). |

Overview table and copy commands: **`skills/CONNECTORS.md`**.

---

## Distribution: Slack App Directory vs this repo

**Slack App Directory / “Marketplace”** listings are for **public, installable apps** Slack reviews end-to-end: support URL, privacy policy, OAuth install flow to **your** servers, multi-workspace distribution, etc. That is a **product** launch, not something this git repo replaces.

**What this repo is:** **BYO (bring-your-own) integration** — each team creates a Slack app from the manifest under **`skills/atlas-bridge-slack/`**, installs it to **their** workspace, and puts webhook URL + bot token + channel id in **`.env`**. Others follow **`skills/atlas-bridge-slack/SKILL.md`**, **`skills/CONNECTORS.md`**, and **`.env.example`**; there is no single “install from Slack for everyone” button unless North Model Labs ships a hosted Slack product.

**OpenClaw / agents:** the **atlas-avatar** skill can be copied or published via **ClawHub** (see [Publish to ClawHub](#publish-to-clawhub-atlas-avatar-skill) below) — that is separate from Slack’s store.

---

## Scope: realtime vs meeting products

Some vendors ship a **synthetic participant** that joins **Zoom / Meet / Teams** as a tile. **This repository does not include that** — Atlas exposes HTTP + LiveKit join info; joining someone else’s meeting product needs their SDKs, certification, and usually a separate service.

**What we do ship:** Slack + Discord **incoming webhooks** to post session summaries and short **MP4** renders, an **optional Discord bot** you run locally (`./scripts/bridges/run-discord-avatar-bot.sh`) that replies with offline lip-sync clips, and CLIs under **`scripts/bridges/`**. For **you + avatar on one machine**, a **local viewer** URL is the intended next step — see **`viewer/README.md`**.

---

## Getting started

### 1. Get an Atlas API key

Create a key in the [dashboard](https://dashboard.northmodellabs.com/dashboard/keys) (or your org’s Atlas dashboard URL).

### 2. Set environment variables

```bash
export ATLAS_API_KEY="ak_..."
# optional:
export ATLAS_API_BASE="https://api.atlasv1.com"
```

### 3. Install Python dependencies

```bash
pip install -r core/requirements.txt
```

### 4. Install OpenClaw (the agent host)

Use **[OpenClaw’s official install documentation](https://docs.openclaw.ai/install)** only (install, update, uninstall, verify). This repo does not pin or document OpenClaw versions.

### 5. Install skills into OpenClaw (example)

```bash
mkdir -p ~/.openclaw/workspace/skills
cp -R skills/atlas-avatar ~/.openclaw/workspace/skills/atlas-avatar
# optional bridges (Slack / Discord webhooks):
cp -R skills/atlas-bridge-discord ~/.openclaw/workspace/skills/
cp -R skills/atlas-bridge-slack ~/.openclaw/workspace/skills/
```

### 6. Use it

Start an OpenClaw session and ask for a realtime avatar or offline render — the agent should follow `skills/atlas-avatar/SKILL.md`.

**CLI (from monorepo root):**

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py health
python3 skills/atlas-avatar/scripts/atlas_session.py start --face-url "https://example.com/face.jpg"
python3 skills/atlas-avatar/scripts/atlas_session.py leave --session-id SESSION_ID
```

Full REST surface: **`python3 core/atlas_cli.py --help`**.

### After `start` → `session.json` (Slack / Discord)

Post the session (and optional **MP4** on Discord) using **`skills/atlas-bridge-*/scripts/post_session.py`** — see **`skills/CONNECTORS.md`** and smoke scripts under **`scripts/bridges/`**.

### Slack: where tokens live (quick map)

Full step-by-step (webhook URL, `xoxb-` bot token, channel ID `C…`, what Basic Information is for): **`skills/atlas-bridge-slack/SKILL.md`** → section **“Where each value lives”**.

- **Webhook URL** → *Incoming Webhooks* in the Slack app settings.  
- **Bot token (`xoxb-`)** → *OAuth & Permissions* (not *Basic Information*).  
- **Channel ID** → from the Slack client URL: the `C…` segment when the channel is open.

### Discord: webhook vs interactive bot

These are **different credentials** and **different use cases**. Put secrets in **`.env`** (never commit `.env`); names are in **`.env.example`**.

| Mode | What it is | Env vars | How you use it |
|------|------------|----------|----------------|
| **Webhook** | One-way “post a message” URL | `DISCORD_WEBHOOK_URL` | `post_session.py`, `./scripts/bridges/test-discord-webhook.sh`, `./scripts/bridges/atlas-offline-to-discord.sh` |
| **Interactive bot** | **`/ask`**, **@mention**, or **reply to bot** → **Claude** + **Answer:** + MP4; **`/generate`** → verbatim MP4 | `DISCORD_BOT_TOKEN` + `ATLAS_API_KEY` + **`HELICONE_API_KEY`** (default: Helicone AI Gateway) **or** `ANTHROPIC_API_KEY` (direct); `LLM_MODEL` optional; optional `HELICONE_ANTHROPIC_PROXY=1` with both keys for legacy proxy; **Message Content** for replies + @mentions | `./scripts/bridges/run-discord-avatar-bot.sh` (after Portal setup below) |

#### A) Webhook (optional, for scripts)

1. Server → **Channel settings** → **Integrations** → **Webhooks** → **New Webhook** → copy URL.  
2. In `.env`: `DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...`

#### B) Interactive bot (optional, for “@bot say this” → video)

**1. Discord Developer Portal** — [Applications](https://discord.com/developers/applications) → **New Application** (or open your app, e.g. **bob**) → left sidebar **Bot**.

**2. Create / reset token** — On the **Bot** page, under **TOKEN**, click **Reset Token** (or **Copy**).  
In **`.env`** add at least:

```env
DISCORD_BOT_TOKEN=paste_token_here
ATLAS_API_KEY=your_atlas_key_here
```

For **`/ask`** / **reply-to-bot** (Claude answers; the **video lip-syncs that answer**), add **`HELICONE_API_KEY`** to use [Helicone AI Gateway](https://docs.helicone.ai/getting-started/quick-start) (Helicone credits; OpenAI-compatible **`/v1/chat/completions`**). Alternatively use **`ANTHROPIC_API_KEY`** only for direct **`api.anthropic.com`**. If you have **both** keys and want the older **`anthropic.helicone.ai`** Anthropic proxy instead of the gateway, set **`HELICONE_ANTHROPIC_PROXY=1`**. **`LLM_MODEL`** is optional; defaults are **`claude-sonnet-4`** (gateway) and **`claude-sonnet-4-20250514`** (native Anthropic).

```env
HELICONE_API_KEY=sk-helicone-...
# LLM_MODEL=claude-sonnet-4            # optional override (gateway)
# ANTHROPIC_API_KEY=sk-ant-...         # optional: direct Anthropic when Helicone is unset
# HELICONE_ANTHROPIC_PROXY=1          # optional: both keys → legacy Helicone Anthropic proxy
```

Optional (spoken audio instead of the built-in test tone WAV):

```env
ELEVENLABS_API_KEY=your_key_here
# ELEVENLABS_VOICE_ID=...
# ATLAS_OFFLINE_IMAGE=/absolute/path/to/face.jpg
```

You do **not** need the **Application ID** in `.env` for this repo’s bot script.

**3. Privileged Gateway Intents** (same **Bot** page, lower section)

- For **`@YourBot some text`**: turn **ON** **Message Content Intent** in the Portal **and** add **`DISCORD_MESSAGE_CONTENT_INTENT=1`** to `.env` (the bot disables this intent by default so it can log in without that toggle).  
- For **`/ask` only**, you can leave Message Content **off** in the Portal and omit that env line.

**4. Bot permissions** (same **Bot** page → **Bot Permissions** grid — or use **OAuth2 → URL Generator** in step 5)

For **text channel + MP4 attachment + slash commands**, enable at least under **Text Permissions**:

- **Send Messages**  
- **Attach Files**  
- **Read Message History**  
- **Use Slash Commands**

**Voice permissions** (Connect, Speak, Video, etc.) are **not required** for this bot: it does **not** join voice; it posts **offline-rendered video** in chat.

##### Add the **bot user** to the server (required — easy to get wrong)

Discord may show your app under **Server settings → Integrations → Bots and Apps** and still say **“This application does not have a bot in this server.”** That means only the **application / slash commands** were wired up — there is **no bot member**. Then you cannot **`@mention`** the bot, **reply-to-bot** and **@mention** lines will not run, and when you start this repo’s script you will see **`discord_avatar_bot: in 0 server(s)`** in the terminal (the bot user is in no guilds).

**Do not rely on** the short **Installation** link alone (`https://discord.com/oauth2/authorize?client_id=…` with **no** `scope=bot`). That path often **does not** add the **bot** account to the guild.

**Do this instead:** **OAuth2** (left sidebar) → **URL Generator**:

1. **Scopes:** enable **`bot`** and **`applications.commands`** (both are required for this project).  
2. If the page shows **Integration type**, choose **Guild install** (install into a server, not only “user install”).  
3. **Bot permissions:** enable at least the four from step 4 (**Send Messages**, **Attach Files**, **Read Message History**, **Use Slash Commands**) plus **View Channel** / **Read messages** if your UI lists it (the bot must see the channel).  
4. Copy the **Generated URL** at the bottom. It must be a **long** URL that includes **`scope=bot`** and **`applications.commands`** (often `scope=bot%20applications.commands`) and a **`permissions=`** number — e.g.  
   `https://discord.com/oauth2/authorize?client_id=YOUR_APP_ID&permissions=…&integration_type=0&scope=bot%20applications.commands`  
5. Open that URL in a browser, select your server, and **Authorize**.  
6. Confirm in **Server settings → Integrations →** your app: the **Bot** section should **not** say the app has no bot. After you run `./scripts/bridges/run-discord-avatar-bot.sh`, stderr should list **`in 1 server(s): …`** (or more), not **`in 0 server(s)`**.

**5. Invite the bot to your server** — follow the **URL Generator** steps in the box above (this is the supported invite path for `discord_avatar_bot.py`).

**6. Install Python deps and run** (from **monorepo root**):

```bash
pip install -r skills/atlas-bridge-discord/requirements.txt
./scripts/bridges/run-discord-avatar-bot.sh
```

Leave that terminal open while you test. In Discord: **`/ask`** or **`@BotName how are you?`** = prompt → **Claude** → **Answer:** + MP4 of that answer; **`/generate`** = verbatim script → MP4; **reply to any of the bot’s messages** with text = same LLM + **Answer:** + MP4 with the bot’s prior message as context (needs **Message Content** intent for replies and @mentions).

**If Discord says “This command is outdated”** for `/ask` or `/generate`: your client cached an old slash definition. **Ctrl+R** (reload Discord), wait a minute, then type **`/`** and pick the command again from the menu (don’t reuse a stale chip). For **instant** updates while developing, set **`DISCORD_GUILD_ID`** in `.env` to your server’s numeric id (Developer Mode → right‑click server → **Copy Server ID**) and restart the bot — commands register **only** in that server but sync immediately.

**If `/ask` still posts only “Here is a lip-sync clip.” and the video matches your typed line verbatim:** the **Python bot process** is still an **old build**. Re‑adding the app in Discord does **not** deploy new code. Pull the latest repo, run `pkill -f discord_avatar_bot.py`, then `./scripts/bridges/run-discord-avatar-bot.sh` on the machine that stays online. On startup the terminal should print a line starting with `discord_avatar_bot:` describing `/ask=Claude` — if that line is missing, you’re not running this version. `/ask` needs **`HELICONE_API_KEY`** (gateway default) or **`ANTHROPIC_API_KEY`** (direct), plus optional `LLM_MODEL`.

**More detail** (troubleshooting, `DISCORD_MESSAGE_STYLE` for webhooks, file size limits): **`skills/atlas-bridge-discord/SKILL.md`**.

---

## Publish to ClawHub (atlas-avatar skill)

```bash
npm i -g clawhub
clawhub login
clawhub publish ./skills/atlas-avatar \
  --slug atlas-avatar \
  --name "Atlas Avatar" \
  --version 1.0.9 \
  --tags latest
```

Install: `clawhub install atlas-avatar` (flags may vary — `clawhub --help`).

---

## Architecture

```
┌─────────────────┐   Chat-style HTTP gateway   ┌──────────────────┐
│  Agent /        │ ─────────────────────────► │  LLM (optional)  │
│  OpenClaw       │                            └──────────────────┘
└────────┬────────┘
         │  SKILL.md + scripts → Atlas HTTP
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Atlas API (ATLAS_API_BASE)                                     │
│  • POST /v1/realtime/session  → LiveKit URL + token + room      │
│  • POST /v1/generate          → async avatar video job           │
│  • jobs / TTS / face-swap — see skills/atlas-avatar/references/ │
└─────────────────────────────────────────────────────────────────┘
         ▼
   GPU avatars + WebRTC viewer (**your** app; Atlas returns LiveKit join fields)
```

---

## Repo layout

| Path | Purpose |
|------|---------|
| `viewer/` | **Planned** local browser UI — open a URL on your machine to join the LiveKit room (see `viewer/README.md`). |
| `claude-code-avatar/` | **Terminal coding agents** — `CLAUDE.md`, `PROMPTS.md`, `scripts/demo.sh`; see `claude-code-avatar/README.md` |
| `core/atlas_api.py` | Shared Atlas HTTP client |
| `core/atlas_cli.py` | REST CLI |
| `core/requirements.txt` | `requests` |
| `skills/atlas-avatar/` | Main skill + `atlas_session.py`, `api-reference.md` |
| `skills/atlas-bridge-{slack,discord}/` | Webhooks (Slack, Discord) — see `CONNECTORS.md` |
| `skills/CONNECTORS.md` | Connector index |
| `INTEGRATION.md` | OpenClaw / custom LLM notes |
| `.env.example` | Env var names |
| `scripts/README.md` | Index of Python CLIs vs `scripts/bridges/*.sh` |
| `scripts/bridges/verify-env.sh` | Health + `/v1/me` |
| `scripts/bridges/smoke-atlas.sh` | Smoke tests (optional realtime if `ATLAS_API_KEY` set) |
| `scripts/bridges/test-atlas-api-harness.py` | Full **`atlas_api.py`** surface: status, me, jobs, realtime create→get→viewer→delete (use `--no-realtime` to skip billing); optional offline + `--probe-avatar-session` |
| `scripts/bridges/test-slack-webhook.sh` | Posts a **fake** session line to Slack when `SLACK_WEBHOOK_URL` is set |
| `scripts/bridges/test-slack-video-link.sh` | Slack: text + **render URL** |
| `scripts/bridges/test-discord-webhook.sh` | Discord smoke (text + embed) |
| `scripts/bridges/test-discord-with-mp4.sh` | Discord: **tiny synthetic MP4** (needs `ffmpeg`) |
| `scripts/bridges/atlas-offline-to-discord.sh` | **Atlas `/v1/generate` → wait → download → Discord** attach |
| `scripts/bridges/run-discord-avatar-bot.sh` | **Discord bot**: `/ask` + @mention (LLM + video), `/generate` (verbatim video) |
| `scripts/bridges/atlas-offline-to-slack.sh` | **Atlas offline → Slack** (MP4 via bot token + `SLACK_CHANNEL_ID`, else webhook link only) |
| `scripts/bridges/atlas-narrated-avatar-to-discord.sh` | **Claude + ElevenLabs + S3 face → Atlas offline → Discord** |
| `scripts/avatar_discord_narrator.py` | Narrator implementation (called by the shell wrapper above) |
| `scripts/requirements-narrator.txt` | `boto3`, `requests` for narrator + S3 face pull |

---

## Security

- Never commit API keys, **Discord webhook URLs**, or **`DISCORD_BOT_TOKEN`**. Use `.env` / CI secrets.
- Do not paste LiveKit **`token`** into public webhooks or chat; use **`viewer_url`** patterns that mint tokens server-side.

---

## Contributing

Add a new skill folder with `SKILL.md`, scripts, and `requirements.txt`; update this README, `CONNECTORS.md`, and `scripts/README.md` if you add shell entrypoints.

---

## Support

- **Atlas:** dashboard and your Atlas support channel.  
- **Agent stack:** follow the documentation shipped with your agent / OpenClaw install.
