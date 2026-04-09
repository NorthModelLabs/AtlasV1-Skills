# avatarclaw

**avatarclaw** is the official **[North Model Labs](https://northmodellabs.com) Atlas** integration pack for **[OpenClaw](https://docs.openclaw.ai)** agents: realtime GPU avatars over **LiveKit**, offline lip-sync video, and **live face swap** during a call without reconnecting.

| | |
|--|--|
| **API** | [Atlas API v8](https://api.atlasv1.com) · `https://api.atlasv1.com` |
| **Keys** | [Dashboard — API keys](https://dashboard.northmodellabs.com/dashboard/keys) |
| **Agents** | Drop-in OpenClaw skill (`SKILL.md` + curl recipes) |

---

## Features

- **Realtime avatar** — `POST /v1/realtime/session` → LiveKit `livekit_url`, `token`, `room`. Modes: **`conversation`** (full interactive stack) or **`passthrough`** (you bring audio; Atlas renders the face).
- **Face swap (mid-session)** — `PATCH /v1/realtime/session/{session_id}` updates the avatar’s face **while the session stays live** (same room, no full reconnect). Think of it as **hot-swapping the face** the model drives.
- **Offline video** — `POST /v1/generate` (audio + reference image) → poll `GET /v1/jobs/{id}` → `GET /v1/jobs/{id}/result` for a presigned MP4. Optional **`X-Callback-URL`** webhooks instead of polling.
- **BYOB TTS** — Use any TTS provider, then pass the audio file into `/v1/generate`.

Full endpoint detail, error codes, and limits: **Atlas website → API docs** and `skill/atlas-avatar/references/api-reference.md`.

---

## Quick start (OpenClaw)

1. **Install the skill** ([Creating skills](https://docs.openclaw.ai/tools/creating-skills)):

   ```bash
   mkdir -p ~/.openclaw/workspace/skills
   cp -R skill/atlas-avatar ~/.openclaw/workspace/skills/
   ```

2. **Environment** (shell that runs OpenClaw, or your workspace `.env`):

   ```bash
   export ATLAS_API_KEY="your_key"   # from the dashboard
   # optional — staging or custom gateway
   export ATLAS_API_BASE="https://api.atlasv1.com"
   ```

3. **Smoke check** (optional):

   ```bash
   ./scripts/verify-env.sh
   ```

4. Start a new OpenClaw session and ask for a realtime session, **face swap**, or offline render — the agent follows **`skill/atlas-avatar/SKILL.md`**.

---

## Face swap in one line

After you have a live `session_id`, swap the face with **`PATCH`** (multipart **`face`** file — see `SKILL.md` for the exact `curl`). The avatar transitions to the new face in-session; rate limits apply so the feature isn’t abused.

---

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

Installers: `clawhub install atlas-avatar` (CLI flags may vary — `clawhub --help`).

---

## Architecture

```
 OpenClaw (tools + optional LLM) 
        │
        │  SKILL.md → Atlas REST (curl)
        ▼
 Atlas API ──► GPU avatars + LiveKit (realtime)
            └──► Job queue + storage (offline)
```

OpenClaw does not replace Atlas; they compose. Use OpenClaw for **when** to call the API; Atlas runs **WebRTC + rendering**.

---

## Repository layout

| Path | Purpose |
|------|---------|
| `skill/atlas-avatar/SKILL.md` | Agent instructions + copy-paste `curl` |
| `skill/atlas-avatar/references/api-reference.md` | Dense API reference for agents |
| `INTEGRATION.md` | Deeper integration notes for developers |
| `skill.yaml.example` | Optional manifest for some publish flows |
| `.env.example` | Variable names for local setup |
| `scripts/verify-env.sh` | `GET /v1/health` + `GET /v1/me` check |

---

## Security

- Never commit real API keys (`.env` is gitignored).
- Do not log Bearer tokens or LiveKit JWTs. Sanitize user-provided paths in shell snippets.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Support

- **Atlas API / billing / keys:** [North Model Labs](https://northmodellabs.com) dashboard and support.
- **OpenClaw / ClawHub:** [docs.openclaw.ai](https://docs.openclaw.ai).
