# avatarclaw

**Atlas Avatar × OpenClaw** — official skill pack for **[North Model Labs Atlas](https://northmodellabs.com)** (realtime LiveKit avatars + offline lip-sync video) with **[OpenClaw](https://docs.openclaw.ai)** agents.

| | |
|:--|:--|
| **Repository** | [NorthModelLabs/avatarclaw](https://github.com/NorthModelLabs/avatarclaw) |
| **API base** | `https://api.atlasv1.com` ([Atlas API v8](https://api.atlasv1.com)) |
| **Dashboard** | [northmodellabs.com](https://northmodellabs.com) → sign in → **API keys** |

---

## Dashboard: get an API key

1. Open the **[API keys](https://dashboard.northmodellabs.com/dashboard/keys)** page (North Model Labs dashboard).
2. Add a **payment method** if prompted (required to create keys on standard plans).
3. **Create a key** and copy it once — store it as `ATLAS_API_KEY` (treat it like a secret; never commit it).
4. Use the key as: `Authorization: Bearer <your_key>` on every Atlas request (except unauthenticated routes like `GET /` and `GET /v1/health`).

**Optional check** after exporting `ATLAS_API_KEY`:

```bash
cp .env.example .env   # then edit .env — do not commit .env
source .env 2>/dev/null || true
./scripts/verify-env.sh   # GET /v1/health + GET /v1/me
```

---

## Sample apps & SDK

Use these to see the same API the skill documents, end to end:

| Resource | What it is |
|:--|:--|
| **[atlas-offline-example](https://github.com/NorthModelLabs/atlas-offline-example)** | Next.js — text/audio → offline avatar video (`POST /v1/generate`, jobs, download). |
| **[atlas-realtime-example](https://github.com/NorthModelLabs/atlas-realtime-example)** | Next.js — live avatar + LLM (`POST /v1/realtime/session`, LiveKit). |
| **[@northmodellabs/atlas-react](https://www.npmjs.com/package/@northmodellabs/atlas-react)** | React hook `useAtlasSession()` — LiveKit wiring, mic, transcripts, passthrough audio helpers. |

Full field-level API detail, error codes, and limits live on the **Atlas website → API docs** (same contract as `skill/atlas-avatar/references/api-reference.md`).

---

## What’s in this repo

- **`skill/atlas-avatar/`** — OpenClaw skill (`SKILL.md` + `references/api-reference.md`). Copy into your OpenClaw skills path or publish via ClawHub (optional).
- **`INTEGRATION.md`** — developer notes: OpenClaw + custom LLM, realtime vs offline flows, when to use a plugin instead of raw `curl`.

---

## Quick start (OpenClaw)

1. Install the skill ([Creating skills](https://docs.openclaw.ai/tools/creating-skills)):

   ```bash
   mkdir -p ~/.openclaw/workspace/skills
   cp -R skill/atlas-avatar ~/.openclaw/workspace/skills/
   ```

2. Export your key (from the dashboard step above):

   ```bash
   export ATLAS_API_KEY="your_key_here"
   ```

3. Optional — staging or custom gateway:

   ```bash
   export ATLAS_API_BASE="https://api.atlasv1.com"
   ```

4. Start a new OpenClaw session (`/new`) and ask for a **realtime session**, **offline video** (`/v1/generate`), or **face swap** (`PATCH` realtime session). The agent follows `skill/atlas-avatar/SKILL.md`.

---

## Architecture

```
┌─────────────────┐     OpenAI-compatible      ┌──────────────────┐
│  OpenClaw       │ ─────────────────────────► │  LLM provider    │
│  (agent brain)  │                            │  (optional swap) │
└────────┬────────┘                            └──────────────────┘
         │
         │  SKILL.md → Atlas REST (curl)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Atlas API (https://api.atlasv1.com)                            │
│  • POST /v1/realtime/session  → LiveKit URL + token + room      │
│  • POST /v1/generate          → async avatar video job          │
│  • Jobs, webhooks, session lifecycle (see api-reference.md)     │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
   GPU avatars + LiveKit (WebRTC)
```

Realtime **`conversation`** mode uses Atlas-hosted STT → LLM → TTS → avatar. **`passthrough`** mode: you send audio (e.g. your own TTS); Atlas renders the face.

**Billing (API):** **$5/hour** prorated for realtime **passthrough** and for **offline** `/v1/generate` output duration; **$10/hour** prorated for realtime **conversation** (interactive).

---

## Repo layout

| Path | Purpose |
|------|---------|
| `skill/atlas-avatar/SKILL.md` | Agent instructions + copy-paste `curl` |
| `skill/atlas-avatar/references/api-reference.md` | Dense endpoint reference for agents |
| `INTEGRATION.md` | Deeper integration guide for developers |
| `skill.yaml.example` | Optional manifest for some publish flows |
| `.env.example` | Variable names for local use with `verify-env.sh` |
| `scripts/verify-env.sh` | Optional `GET /v1/health` + `GET /v1/me` smoke check |

---

## Publish to ClawHub (optional)

Registry install is optional; copying this repo’s `skill/` is enough for most setups.

```bash
npm i -g clawhub
clawhub login    # or: clawhub login --token "$CLAWHUB_TOKEN"
clawhub skill publish ./skill/atlas-avatar \
  --slug atlas-avatar \
  --name "Atlas Avatar" \
  --version 1.0.1 \
  --changelog "your release notes" \
  --tags latest
```

Consumers: `openclaw skills install atlas-avatar` or `clawhub install atlas-avatar` (see [ClawHub](https://docs.openclaw.ai/tools/clawdhub); CLI flags may vary — `clawhub --help`).

---

## Security

- Never commit real API keys. `.env` is gitignored; use CI secrets in automation.
- Do not log Bearer tokens or LiveKit JWTs. Sanitize user-provided paths in any shell snippets.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Support

- **Atlas API, billing, keys:** [North Model Labs](https://northmodellabs.com) dashboard and support.
- **OpenClaw / ClawHub:** [docs.openclaw.ai](https://docs.openclaw.ai).
