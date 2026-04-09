# Atlas API reference (OpenClaw / agents)

**Base:** `ATLAS_API_BASE` (default `https://api.atlasv1.com`)  
**Auth:** `Authorization: Bearer <ATLAS_API_KEY>`

---

## Index & health

| Method | Path | Auth |
|--------|------|------|
| GET | `/` | No — API info, `version`, `endpoints` map |
| GET | `/v1/health` | No — deep health (GPU/TTS/DB signals) |
| GET | `/v1/status` | Yes — `avatar_generation` / `voice_synthesis` busy vs available |
| GET | `/v1/me` | Yes — key prefix, tier, rate limit window, billing hint |

---

## Offline generation & jobs

### `POST /v1/generate`

Multipart: **`audio`**, **`image`** (required). Returns **202** with `job_id`, `pending`.

- **Billing:** **$5/hour** of **output** video duration (same cents/sec as realtime passthrough), prorated.
- Combined upload limit ~**50 MB** (see live docs).
- **BYOB TTS:** generate speech with any provider; pass the audio file here.

**Webhook:** header **`X-Callback-URL`** (HTTPS, validated; no localhost). Body fields may also support `callback_url` on some JSON TTS endpoints — prefer header for multipart `/v1/generate`.

### `GET /v1/jobs`

Query: `limit` (default 20, max 100), `offset`. Newest first.

### `GET /v1/jobs/{job_id}`

Statuses: `pending`, `processing`, `completed`, `failed`. May include presigned `url` when completed.

### `GET /v1/jobs/{job_id}/result`

Presigned download JSON: `url`, `content_type`, `expires_in`.

- **409 `not_ready`** if job not `completed` yet.

---

## Realtime

### `POST /v1/realtime/session`

**JSON:** `{ "mode": "conversation"|"passthrough", "face_url": "https://..." }`  
**Multipart:** `mode`, optional `face` file.

**200:** `session_id`, `livekit_url`, `token`, `room`, `mode`, `max_duration_seconds`, **`pricing`** (`"$10/hour..."` for conversation, `"$5/hour..."` for passthrough).

### `GET /v1/realtime/session/{id}`

`status`, `room`, `started_at`, `ended_at`, `duration_seconds`, `max_duration_seconds`.

### `PATCH /v1/realtime/session/{id}`

**Multipart only:** field **`face`** (file). No `face_url` on PATCH (security). Use POST create for HTTPS URLs.

**200:** `face_updated`, `metadata_pushed`, `message`.

**409:** `session_not_active` if not `active`.

### `DELETE /v1/realtime/session/{id}`

**200:** `status`, `duration_seconds`, `estimated_cost`, `credits_deducted_cents`.

**409:** `already_ended` if session already ended.

---

## Plugin (omitted from `GET /` index)

### `POST /v1/avatar/session`

Multipart: `livekit_url`, `livekit_token`, `room_name` (strings); optional `avatar_image` file.

**200:** `{ "session_id", "status": "ok" }`.

For **livekit-plugins-atlas** when the customer hosts the LiveKit room.

---

## TTS job endpoints

`POST /v1/tts/generate`, `/v1/tts/generate-wav`, `/v1/tts/generate-video` — async jobs; same poll/result pattern. See website for multipart vs JSON.

---

## Errors

Standard shape:

```json
{ "error": "code", "message": "Human-readable text" }
```

Full enum table lives on the **website** API docs. This file stays short for token budget.

---

## OpenClaw note

Skills teach curl; for production, prefer a typed OpenClaw **plugin** if you need non-shell secret handling or streaming.
