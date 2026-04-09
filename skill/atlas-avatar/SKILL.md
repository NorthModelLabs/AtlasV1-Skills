---
name: atlas_avatar
description: "Create realtime AI avatar sessions (LiveKit WebRTC), mid-session face swap (PATCH realtime session), and offline lip-sync avatar videos using the Atlas API by North Model Labs. Use when the user asks for Atlas avatar, face swap, hot-swap face, talking head, realtime avatar, lip sync, BYOB TTS + /v1/generate, or GPU avatar rendering."
version: "1.0.1"
tags: ["avatar", "video", "realtime", "livekit", "lip-sync", "atlas", "gpu", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [ATLAS_API_KEY]
      bins: [curl]
---

# Atlas Avatar (OpenClaw skill) — API v8

Atlas provides **realtime** sessions (LiveKit) and **async** offline jobs (`POST /v1/generate` → poll → result). API keys: [North Model Labs dashboard](https://dashboard.northmodellabs.com/dashboard/keys).

## Configuration

| Variable | Required | Default |
|----------|----------|---------|
| `ATLAS_API_KEY` | Yes | Bearer token (`ak_...`) |
| `ATLAS_API_BASE` | No | `https://api.atlasv1.com` |

Use `$ATLAS_API_BASE` and `$ATLAS_API_KEY` in every curl.

## Discoverability

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/"
```

Returns `version`, `endpoints`, and flow hints (no auth).

## Health & capacity

```bash
# Deep check (GPU / TTS / DB) — no auth
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/health"

# Busy vs available — requires auth
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/status" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

## Account

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/me" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

## Offline video (async) — BYOB TTS

Use **any** TTS to produce audio, then:

```bash
curl -sS -X POST "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/generate" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -F "audio=@speech.mp3" \
  -F "image=@face.jpg"
```

**202** → `job_id`, `status: pending`. **Max ~50 MB** combined upload (see live docs for exact limits).

### Webhook instead of polling (multipart)

```bash
curl -sS -X POST "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/generate" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -H "X-Callback-URL: https://yourapp.com/webhook/atlas" \
  -F "audio=@speech.mp3" \
  -F "image=@face.jpg"
```

HTTPS callback only; server validates URL. Verify deliveries with `X-Atlas-Signature` / `X-Atlas-Timestamp` (see website API docs).

### Poll job + list jobs

```bash
# Single job
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/jobs/JOB_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"

# Recent history (paginated)
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/jobs?limit=20&offset=0" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

### Result URL

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/jobs/JOB_ID/result" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

**409 `not_ready`** if job is still `pending` or `processing`. When `completed`, completed-job poll may already include a presigned `url`; `/result` returns `{ url, content_type, expires_in }`.

## Realtime session

### Create — JSON (`face_url` optional)

```bash
curl -sS -X POST "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"conversation","face_url":"https://example.com/face.jpg"}'
```

### Create — multipart (`face` file optional)

```bash
curl -sS -X POST "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -F "mode=passthrough" \
  -F "face=@/path/to/face.jpg"
```

`mode`: `conversation` (default, higher $/hr) or `passthrough` (you supply audio).

### Response 200

Includes `session_id`, `livekit_url`, `token`, `room`, `mode`, `max_duration_seconds`, and **`pricing`** (string, e.g. `"$10/hour, prorated per second"` or passthrough rate).

### Session lifecycle

```bash
curl -sS "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session/SESSION_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

Response includes `max_duration_seconds` among other fields.

### PATCH — **face swap** (change avatar face mid-call, no disconnect)

This endpoint **is face swap**: replace the reference face **while the LiveKit session stays connected** — the avatar transitions to the new look in real time (rate limited).

Server accepts **`face`** as multipart **file** (HTTPS `face_url` is for **POST create**, not PATCH on this deployment).

```bash
curl -sS -X PATCH "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session/SESSION_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}" \
  -F "face=@/path/to/new_face.jpg"
```

**200** body includes `face_updated`, `metadata_pushed`, `message`. **409 `session_not_active`** if session already ended.

### DELETE — end session

```bash
curl -sS -X DELETE "${ATLAS_API_BASE:-https://api.atlasv1.com}/v1/realtime/session/SESSION_ID" \
  -H "Authorization: Bearer ${ATLAS_API_KEY}"
```

**200** includes `duration_seconds`, `estimated_cost`, `credits_deducted_cents`. **409 `already_ended`** if already closed.

## Plugin flow (not listed on `GET /`)

`POST /v1/avatar/session` — multipart `livekit_url`, `livekit_token`, `room_name`, optional `avatar_image`. For **livekit-plugins-atlas** / BYO LiveKit. See `references/api-reference.md`.

## Errors (short)

Responses use **`error`** + **`message`** string fields (and optional extras).

| HTTP | Typical `error` |
|------|------------------|
| 401 | `unauthorized` |
| 402 | insufficient credits |
| 403 | `forbidden` |
| 404 | `not_found` |
| 409 | `not_ready` (job result too early), `already_ended` (DELETE session), `session_not_active` (PATCH face) |
| 429 | rate limit |
| 503 | `no_capacity` (GPUs busy), etc. |

Full code table: **Atlas website → API docs → Error Responses**.

## OpenClaw as LLM

Point your agent’s chat client at OpenClaw’s OpenAI-compatible base URL; keep using this skill for Atlas HTTP calls. Realtime **conversation** mode still uses Atlas-hosted STT/LLM/TTS unless you use **passthrough** and your own audio pipeline.
