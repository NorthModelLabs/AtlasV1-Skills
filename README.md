# Atlas Avatar skills (OpenClaw & agents)

Open-source **skills** and **CLI tools** for AI coding agents ([OpenClaw](https://docs.openclaw.ai), Claude Code, etc.) that call the **[North Model Labs](https://www.northmodellabs.com/) Atlas API** — realtime **LiveKit** avatar sessions and **offline** lip-sync video jobs (GPU warping, TTS integrations).

This pack is **API-first**: you get `livekit_url`, `token`, and `room` from Atlas, then connect a **browser or app** you control. It is **not** a drop-in clone of hosted meeting-bot products (see [Google Meet](#google-meet-vs-hosted-meeting-bots) below).

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
| **`scripts/`** | Small CLIs (`atlas_session.py`, webhooks, Meet *assist* helpers, …). |
| **`requirements.txt`** | Python deps (usually `requests`). |

Copy a skill into your agent workspace (e.g. `~/.openclaw/workspace/skills/`) or publish/install via [ClawHub](https://docs.openclaw.ai/tools/clawhub).

---

## Available skills (this repo)

| Skill | Pricing (source of truth) | What it does |
|-------|---------------------------|--------------|
| **`skills/atlas-avatar/`** | Dashboard + API `pricing` / `GET /v1/me` | Core Atlas API: realtime sessions, offline jobs, jobs poll, face-swap — `SKILL.md` + **`atlas_session.py`** verb CLI + **`run_atlas_cli.py`**. |
| **`skills/atlas-bridge-slack/`** | Webhook only (Slack side is free tier / your plan) | Post session summary to Slack Incoming Webhook. |
| **`skills/atlas-bridge-discord/`** | Webhook only | Post summary + optional **`viewer_url`** embed + optional **MP4** attach (size limits apply). |
| **`skills/atlas-bridge-google-meet/`** | N/A (no Atlas minutes by itself) | **Guide** + **`meet_assist.py`**: checklist, open Meet in browser, draft **chat paste** — you still join Meet as a human and run a **viewer** for the avatar. |
| **`skills/atlas-bridge-zoom/`** | N/A | **Guide** only — same architectural limits as Meet. |

Overview table and copy commands: **`skills/CONNECTORS.md`**.

---

## Google Meet vs hosted meeting bots

Some **other** skill packs (for example [Pika-Labs/Pika-Skills](https://github.com/Pika-Labs/Pika-Skills)) ship a **hosted** “join Google Meet as an avatar” flow backed by **their** cloud API and billing (e.g. per-minute pricing on their README).

**This repository does not include a Meet bot binary or Atlas Meet-join API calls** — joining Meet as a synthetic participant requires a **separate** meeting-bot fleet, Workspace/partner integrations, or a vendor; that is outside the scope of these HTTP+skill scripts.

**What we *do* ship for Meet:** `meet_assist.py` to streamline the honest workflow: you in Meet + avatar in a **browser viewer** (link in chat or screen share). See **`skills/atlas-bridge-google-meet/SKILL.md`**.

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
# optional bridges:
cp -R skills/atlas-bridge-discord ~/.openclaw/workspace/skills/
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

### Google Meet assist (after `start` → `session.json`)

```bash
python3 skills/atlas-bridge-google-meet/scripts/meet_assist.py checklist --meet-url "https://meet.google.com/xxx-xxxx-xxx"
python3 skills/atlas-bridge-google-meet/scripts/meet_assist.py open-meet --meet-url "https://meet.google.com/xxx-xxxx-xxx"
python3 skills/atlas-bridge-google-meet/scripts/meet_assist.py paste-message \
  --meet-url "https://meet.google.com/xxx-xxxx-xxx" \
  -f session.json \
  --viewer-url "https://yourapp.com/avatar/room-token-route"
```

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
┌─────────────────┐     OpenAI-compatible      ┌──────────────────┐
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
   GPU avatars + LiveKit (WebRTC in **your** viewer app)
```

---

## Repo layout

| Path | Purpose |
|------|---------|
| `google-meet/` | **Meet workflow CLI** — chains `atlas_session start` + `meet_assist` (not a Meet bot); see `google-meet/README.md` |
| `meeting-bot/` | **OSS local helpers** — Playwright headed Meet + optional LiveKit tone publisher; see `meeting-bot/README.md` |
| `core/atlas_api.py` | Shared Atlas HTTP client |
| `core/atlas_cli.py` | REST CLI |
| `core/requirements.txt` | `requests` |
| `skills/atlas-avatar/` | Main skill + `atlas_session.py`, `api-reference.md` |
| `skills/atlas-bridge-*` | Slack, Discord, Meet assist, Zoom guide |
| `skills/CONNECTORS.md` | Connector index |
| `INTEGRATION.md` | OpenClaw / custom LLM notes |
| `.env.example` | Env var names |
| `scripts/verify-env.sh` | Health + `/v1/me` |
| `scripts/smoke-atlas.sh` | Smoke tests (optional realtime if `ATLAS_API_KEY` set) |

---

## Security

- Never commit API keys or webhook URLs. Use `.env` / CI secrets.
- Do not paste LiveKit **`token`** into public Slack/Discord; use **`viewer_url`** patterns that mint tokens server-side.

---

## Contributing

Add a new skill folder with `SKILL.md`, scripts, and `requirements.txt`; update this README and `CONNECTORS.md`.

---

## Support

- **Atlas:** dashboard and your Atlas support channel.  
- **OpenClaw:** [docs.openclaw.ai](https://docs.openclaw.ai).
