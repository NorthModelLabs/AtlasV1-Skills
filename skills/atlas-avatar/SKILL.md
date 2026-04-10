---
name: atlas_avatar
description: "Create realtime AI avatar sessions (LiveKit WebRTC) and offline lip-sync avatar videos using the Atlas API by North Model Labs. Use when the user asks for Atlas avatar, talking head, realtime avatar, face animation, video from audio+image, lip sync, BYOB TTS + /v1/generate, or GPU avatar rendering."
version: "1.0.3"
tags: ["avatar", "video", "realtime", "livekit", "lip-sync", "atlas", "gpu", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [ATLAS_API_KEY]
      bins: [python3]
---

# Atlas Avatar (OpenClaw skill) — API v8

Atlas provides **realtime** sessions (LiveKit) and **async** offline jobs (`POST /v1/generate` → poll → result). API keys: [North Model Labs dashboard](https://dashboard.northmodellabs.com/dashboard/keys).

## Configuration

| Variable | Required | Default |
|----------|----------|---------|
| `ATLAS_API_KEY` | Yes | Bearer token |
| `ATLAS_API_BASE` | No | `https://api.atlasv1.com` |
| `ATLAS_AGENT_REPO` | No | Only if you copied **only** `skills/atlas-avatar/` elsewhere — set to the **monorepo root** that contains `core/atlas_cli.py` |

**Python deps:** `pip install -r core/requirements.txt` or `pip install -r skills/atlas-avatar/requirements.txt` (same pins). Prefer a **venv**.

---

## Preferred for agents: `scripts/atlas_session.py` (Pika-style verbs)

One entrypoint with **`start` / `leave` / `face-swap`** style commands. This only calls the **Atlas HTTP API** — it does **not** join Google Meet or other apps. After **`start`**, use `livekit_url`, `token`, and `room` in a LiveKit client ([sample apps](https://github.com/NorthModelLabs/atlas-realtime-example), [`@northmodellabs/atlas-react`](https://www.npmjs.com/package/@northmodellabs/atlas-react)).

From the **monorepo root**:

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py health
python3 skills/atlas-avatar/scripts/atlas_session.py start --mode conversation --face-url "https://example.com/face.jpg"
python3 skills/atlas-avatar/scripts/atlas_session.py start --mode passthrough --face /path/to/face.jpg
python3 skills/atlas-avatar/scripts/atlas_session.py status --session-id SESSION_ID
python3 skills/atlas-avatar/scripts/atlas_session.py face-swap --session-id SESSION_ID --face /path/to/new.jpg
python3 skills/atlas-avatar/scripts/atlas_session.py leave --session-id SESSION_ID
python3 skills/atlas-avatar/scripts/atlas_session.py offline --audio speech.mp3 --image face.jpg
python3 skills/atlas-avatar/scripts/atlas_session.py jobs-wait JOB_ID
python3 skills/atlas-avatar/scripts/atlas_session.py jobs-result JOB_ID
```

If the skill lives without `core/` nearby, set **`ATLAS_AGENT_REPO=/absolute/path/to/monorepo`**.

---

## Also: unified REST CLI (`core/atlas_cli.py`)

From the **repository root** (full clone with `core/` + `skills/`):

```bash
python3 core/atlas_cli.py health
python3 core/atlas_cli.py me
python3 core/atlas_cli.py realtime create --mode conversation --face-url "https://example.com/face.jpg"
python3 core/atlas_cli.py realtime create --mode passthrough --face /path/to/face.jpg
python3 core/atlas_cli.py realtime get SESSION_ID
python3 core/atlas_cli.py realtime patch SESSION_ID --face /path/to/new_face.jpg
python3 core/atlas_cli.py realtime delete SESSION_ID
python3 core/atlas_cli.py generate --audio speech.mp3 --image face.jpg
python3 core/atlas_cli.py jobs list --limit 20
python3 core/atlas_cli.py jobs get JOB_ID
python3 core/atlas_cli.py jobs wait JOB_ID
python3 core/atlas_cli.py jobs result JOB_ID
python3 core/atlas_cli.py avatar-session --livekit-url "wss://..." --livekit-token "..." --room-name "room"
```

Or from anywhere, via the skill wrapper (resolves repo root automatically **or** uses `ATLAS_AGENT_REPO`):

```bash
python3 skills/atlas-avatar/scripts/run_atlas_cli.py me
```

**Exit codes:** `0` success, `2` bad args / missing key, `3` HTTP error from API.

---

## Fallback: `curl` (no Python deps)

Use `$ATLAS_API_BASE` and `$ATLAS_API_KEY` in every command.

### Discoverability

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/"
```

### Health & capacity

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/health"
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/status" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

### Account

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/me" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

### Offline video — BYOB TTS

```bash
curl -sS -X POST "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/generate" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -F "audio=@speech.mp3" \
  -F "image=@face.jpg"
```

**202** → `job_id`, `status: pending`. **Max ~50 MB** combined. **Billing:** **$5/hour** of output video duration (passthrough rate), prorated.

**Webhook:** header `X-Callback-URL: https://...` on the same POST.

### Poll job + list jobs

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/jobs/JOB_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/jobs?limit=20&offset=0" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

### Result URL

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/jobs/JOB_ID/result" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

**409 `not_ready`** if still processing.

### Realtime — create (JSON)

```bash
curl -sS -X POST "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"conversation","face_url":"https://example.com/face.jpg"}'
```

### Realtime — create (multipart)

```bash
curl -sS -X POST "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -F "mode=passthrough" \
  -F "face=@/path/to/face.jpg"
```

**200:** `session_id`, `livekit_url`, `token`, `room`, `pricing` (`$4/hour, prorated per second` for both modes).

### Session lifecycle

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session/SESSION_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

### PATCH — face swap (multipart `face` only)

```bash
curl -sS -X PATCH "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session/SESSION_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -F "face=@/path/to/new_face.jpg"
```

### DELETE — end session

```bash
curl -sS -X DELETE "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session/SESSION_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

### Plugin — BYO LiveKit

`POST /v1/avatar/session` — see `references/api-reference.md`.

---

## Errors (short)

JSON uses **`error`** + **`message`**. Full table: Atlas website → API docs → Error Responses.

## OpenClaw as LLM

Point your chat client at OpenClaw’s OpenAI-compatible base URL; use this skill for Atlas. **Conversation** mode uses Atlas STT/LLM/TTS unless you use **passthrough** and your own audio.
