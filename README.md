# Atlas Avatar skills (OpenClaw & agents)

Open-source **skills** and **CLI tools** for AI coding agents ([OpenClaw](https://docs.openclaw.ai), terminal coding agents, etc.) that call the **[North Model Labs](https://www.northmodellabs.com/) Atlas API** — realtime **WebRTC (LiveKit-shaped join info from Atlas)** sessions and **offline** lip-sync video jobs (GPU warping, TTS integrations).

**Where to start**

| You want… | Go to |
|-----------|--------|
| OpenClaw / skill install | **Getting started** below + `skills/atlas-avatar/SKILL.md` |
| A terminal coding agent driving shell | `claude-code-avatar/README.md` + root `CLAUDE.md` |
| Raw HTTP / curl | `skills/atlas-avatar/references/api-reference.md`, `core/atlas_cli.py --help` |
| Slack / Discord webhooks + offline MP4 delivery | `skills/CONNECTORS.md`, `scripts/README.md`, `scripts/bridges/` |
| Slack “marketplace” / public listing | **Not from this repo** — see [Distribution](#distribution-slack-app-directory-vs-this-repo) below |
| Local browser viewer (planned) | `viewer/README.md` |

This pack is **API-first**: you get `livekit_url`, `token`, and `room` from Atlas, then connect a **browser or app** you control. It is **not** a drop-in “synthetic participant joins Zoom/Meet/Teams” product (see [Scope](#scope-realtime-vs-meeting-products) below).

---

## What is Atlas?

**Atlas** is North Model Labs’ developer API for AI avatars:

- **Realtime** — `POST /v1/realtime/session` returns LiveKit credentials; **`conversation`** mode uses Atlas STT → LLM → TTS → avatar, or **`passthrough`** for your own audio pipeline.
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
| **`skills/atlas-avatar/`** | Dashboard + API `pricing` / `GET /v1/me` | Core Atlas API: realtime sessions, offline jobs, jobs poll, face-swap — `SKILL.md` + **`atlas_session.py`** verb CLI + **`run_atlas_cli.py`**. |
| **`skills/atlas-bridge-slack/`** | Webhook + your Slack app (provider billing is yours) | **Incoming webhook** text/link + optional **bot token** MP4 upload (`post_session.py`, `scripts/bridges/atlas-offline-to-slack.sh`). |
| **`skills/atlas-bridge-discord/`** | Webhook only | Post summary + optional **`viewer_url`** embed + optional **MP4** attach (size limits apply). |

Overview table and copy commands: **`skills/CONNECTORS.md`**.

---

## Distribution: Slack App Directory vs this repo

**Slack App Directory / “Marketplace”** listings are for **public, installable apps** Slack reviews end-to-end: support URL, privacy policy, OAuth install flow to **your** servers, multi-workspace distribution, etc. That is a **product** launch, not something this git repo replaces.

**What this repo is:** **BYO (bring-your-own) integration** — each team creates a Slack app from the manifest under **`skills/atlas-bridge-slack/`**, installs it to **their** workspace, and puts webhook URL + bot token + channel id in **`.env`**. Others follow **`skills/atlas-bridge-slack/SKILL.md`**, **`skills/CONNECTORS.md`**, and **`.env.example`**; there is no single “install from Slack for everyone” button unless North Model Labs ships a hosted Slack product.

**OpenClaw / agents:** the **atlas-avatar** skill can be copied or published via **ClawHub** (see [Publish to ClawHub](#publish-to-clawhub-atlas-avatar-skill) below) — that is separate from Slack’s store.

---

## Scope: realtime vs meeting products

Some vendors ship a **synthetic participant** that joins **Zoom / Meet / Teams** as a tile. **This repository does not include that** — Atlas exposes HTTP + LiveKit join info; joining someone else’s meeting product needs their SDKs, certification, and usually a separate service.

**What we do ship:** Slack + Discord **incoming webhooks** to post session summaries and short **MP4** renders, and CLIs under **`scripts/bridges/`**. For **you + avatar on one machine**, a **local viewer** URL is the intended next step — see **`viewer/README.md`**.

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

### 4. Install skills into OpenClaw (example)

```bash
mkdir -p ~/.openclaw/workspace/skills
cp -R skills/atlas-avatar ~/.openclaw/workspace/skills/atlas-avatar
# optional bridges (Slack / Discord webhooks):
cp -R skills/atlas-bridge-discord ~/.openclaw/workspace/skills/
cp -R skills/atlas-bridge-slack ~/.openclaw/workspace/skills/
```

### 5. Use it

Start an OpenClaw session and ask for a realtime avatar or offline render — the agent should follow `skills/atlas-avatar/SKILL.md`.

**CLI (from monorepo root):**

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py health
python3 skills/atlas-avatar/scripts/atlas_session.py start --mode conversation --face-url "https://example.com/face.jpg"
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

---

## Publish to ClawHub (atlas-avatar skill)

```bash
npm i -g clawhub
clawhub login
clawhub skill publish ./skills/atlas-avatar \
  --slug atlas-avatar \
  --name "Atlas Avatar" \
  --version 1.0.3 \
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
| `scripts/bridges/test-slack-webhook.sh` | Posts a **fake** session line to Slack when `SLACK_WEBHOOK_URL` is set |
| `scripts/bridges/test-slack-video-link.sh` | Slack: text + **render URL** |
| `scripts/bridges/test-discord-webhook.sh` | Discord smoke (text + embed) |
| `scripts/bridges/test-discord-with-mp4.sh` | Discord: **tiny synthetic MP4** (needs `ffmpeg`) |
| `scripts/bridges/atlas-offline-to-discord.sh` | **Atlas `/v1/generate` → wait → download → Discord** attach |
| `scripts/bridges/atlas-offline-to-slack.sh` | **Atlas offline → Slack** (MP4 via bot token + `SLACK_CHANNEL_ID`, else webhook link only) |
| `scripts/bridges/atlas-narrated-avatar-to-discord.sh` | **Claude + ElevenLabs + S3 face → Atlas offline → Discord** |
| `scripts/avatar_discord_narrator.py` | Narrator implementation (called by the shell wrapper above) |
| `scripts/requirements-narrator.txt` | `boto3`, `requests` for narrator + S3 face pull |

---

## Security

- Never commit API keys or webhook URLs. Use `.env` / CI secrets.
- Do not paste LiveKit **`token`** into public webhooks or chat; use **`viewer_url`** patterns that mint tokens server-side.

---

## Contributing

Add a new skill folder with `SKILL.md`, scripts, and `requirements.txt`; update this README, `CONNECTORS.md`, and `scripts/README.md` if you add shell entrypoints.

---

## Support

- **Atlas:** dashboard and your Atlas support channel.  
- **Agent stack:** follow the documentation shipped with your agent / OpenClaw install.
