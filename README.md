# Atlas Avatar × OpenClaw

Official integration pack for using **North Model Labs Atlas** (realtime + offline GPU avatars) from **[OpenClaw](https://docs.openclaw.ai)** agents.

This repo contains:

- **`core/`** — shared **`atlas_api.py`** + **`atlas_cli.py`** (full REST CLI).
- **`skills/atlas-avatar/`** — Core Atlas API skill + `atlas_session.py`.
- **`skills/atlas-bridge-slack`** / **`atlas-bridge-discord`** — post session summaries via **webhooks** (working).
- **`skills/atlas-bridge-google-meet`** / **`atlas-bridge-zoom`** — **honest integration guides** (no Meet/Zoom join from this repo).
- See **`skills/CONNECTORS.md`** for the table and copy instructions.
- **`INTEGRATION.md`** — wiring Atlas with OpenClaw or a custom LLM.

**Python:** `pip install -r core/requirements.txt` (or `skills/atlas-avatar/requirements.txt`). Scripts call **Atlas HTTP only** — they do not join Google Meet; connect **LiveKit** in your app after `start`.

## Quick start (OpenClaw users)

1. Copy the skill into your OpenClaw skills directory (see [OpenClaw: Creating skills](https://docs.openclaw.ai/tools/creating-skills)):

   ```bash
   mkdir -p ~/.openclaw/workspace/skills
   cp -R skills/atlas-avatar ~/.openclaw/workspace/skills/atlas-avatar
   ```

2. Set your API key:

   ```bash
   export ATLAS_API_KEY="ak_..."   # from Atlas dashboard
   ```

3. Optionally set a custom API base (staging / self-hosted):

   ```bash
   export ATLAS_API_BASE="https://api.atlasv1.com"
   ```

4. Start a new OpenClaw session (`/new`) and ask for a realtime avatar session or offline video generation. The agent will follow `SKILL.md`.

**Agent-style CLI (from repo root):**

```bash
pip install -r core/requirements.txt
python3 skills/atlas-avatar/scripts/atlas_session.py start --mode conversation --face-url "https://example.com/face.jpg"
python3 skills/atlas-avatar/scripts/atlas_session.py leave --session-id SESSION_ID
```

## Publish to ClawHub

```bash
npm i -g clawhub
clawhub auth
clawhub skill publish ./skills/atlas-avatar \
  --slug atlas-avatar \
  --name "Atlas Avatar" \
  --version 1.0.3 \
  --tags latest
```

Users install with:

```bash
clawhub install atlas-avatar
```

(Exact `clawhub` flags may vary by CLI version — run `clawhub --help`.)

## Architecture

```
┌─────────────────┐     OpenAI-compatible      ┌──────────────────┐
│  OpenClaw       │ ─────────────────────────► │  LLM provider    │
│  (agent brain)  │                            │  (optional swap) │
└────────┬────────┘                            └──────────────────┘
         │
         │  SKILL.md teaches the agent to call Atlas REST API
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Atlas API (https://api.atlasv1.com)                            │
│  • POST /v1/realtime/session  → LiveKit URL + token + room      │
│  • POST /v1/generate          → async avatar video job          │
│  • TTS / jobs / session lifecycle (see references/api-reference) │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
   GPU pods (warping model) + LiveKit Cloud (WebRTC)
```

Atlas **realtime** sessions use **LiveKit**: your client (or demo app) connects with the returned `livekit_url`, `token`, and `room`. The Atlas agent worker handles STT → LLM → TTS → avatar on the hosted side in `conversation` mode, or you stream audio in `passthrough` mode.

**Billing (API):** **$4/hour** prorated to the second for realtime (**conversation** and **passthrough**) and for **offline** `/v1/generate` output duration (same cents-per-second rate).

## Repo layout

| Path | Purpose |
|------|---------|
| `core/atlas_api.py` | Shared Atlas HTTP client |
| `core/atlas_cli.py` | REST CLI (`realtime create`, `jobs wait`, …) |
| `core/requirements.txt` | `requests` |
| `skills/atlas-avatar/SKILL.md` | Skill — Python + `curl` |
| `skills/atlas-avatar/scripts/atlas_session.py` | Pika-style verbs for agents |
| `skills/atlas-avatar/requirements.txt` | Same deps as `core/` |
| `skills/atlas-avatar/references/api-reference.md` | Endpoint reference |
| `skills/atlas-bridge-*` | Slack/Discord webhooks + Meet/Zoom guides |
| `skills/CONNECTORS.md` | Connector overview |
| `INTEGRATION.md` | Developer integration |
| `.env.example` | Env var names |
| `scripts/verify-env.sh` | Optional health + `/v1/me` |

## Get an API key

Create keys from the Atlas dashboard (see your product URL, e.g. `dashboard.atlasv1.com`). Keys look like `ak_` + hex.

## Security

- Never commit real API keys. Use `.env` locally and CI secrets in automation.
- Prefer `atlas_session.py` / `atlas_cli.py` over hand-built shell strings. If using `curl`, sanitize user-provided paths. For production, consider a typed OpenClaw plugin instead of raw shell.

## License

MIT — see [LICENSE](LICENSE).

## Support

- Atlas API issues: your Atlas support / dashboard.
- OpenClaw: [docs.openclaw.ai](https://docs.openclaw.ai).
