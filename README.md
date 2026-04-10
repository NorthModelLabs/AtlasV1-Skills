# Atlas Avatar × OpenClaw

Official integration pack for using **North Model Labs Atlas** (realtime + offline GPU avatars) from **[OpenClaw](https://docs.openclaw.ai)** agents.

This repo contains:

- **`skill/`** — OpenClaw skill (`SKILL.md` + reference docs) you can install locally or publish to [ClawHub](https://docs.openclaw.ai/tools/clawhub).
- **Integration guides** — how to wire Atlas as the avatar layer while OpenClaw (or any OpenAI-compatible provider) handles reasoning.

## Quick start (OpenClaw users)

1. Copy the skill into your OpenClaw skills directory (see [OpenClaw: Creating skills](https://docs.openclaw.ai/tools/creating-skills)):

   ```bash
   mkdir -p ~/.openclaw/workspace/skills
   cp -R skill/atlas-avatar ~/.openclaw/workspace/skills/
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

## Publish to ClawHub

```bash
npm i -g clawhub
clawhub auth
clawhub skill publish ./skill/atlas-avatar \
  --slug atlas-avatar \
  --name "Atlas Avatar" \
  --version 1.0.0 \
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
| `skill/atlas-avatar/SKILL.md` | OpenClaw skill — instructions + curl examples |
| `skill/atlas-avatar/references/api-reference.md` | Detailed endpoint reference |
| `.env.example` | Environment variables for scripts / docs |
| `scripts/verify-env.sh` | Optional: checks `ATLAS_API_KEY` and hits `GET /v1/health` |

## Get an API key

Create keys from the Atlas dashboard (see your product URL, e.g. `dashboard.atlasv1.com`). Keys look like `ak_` + hex.

## Security

- Never commit real API keys. Use `.env` locally and CI secrets in automation.
- The skill uses `curl` with `Authorization: Bearer`. Ensure untrusted input is not passed into shell commands without sanitization (OpenClaw agents should substitute values safely; for production plugins prefer a typed OpenClaw plugin instead of raw shell).

## License

MIT — see [LICENSE](LICENSE).

## Support

- Atlas API issues: your Atlas support / dashboard.
- OpenClaw: [docs.openclaw.ai](https://docs.openclaw.ai).
