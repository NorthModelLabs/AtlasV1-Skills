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

- **Billing:** see live `pricing` strings and [dashboard](https://dashboard.northmodellabs.com/dashboard/keys); do not hardcode rates in agents.
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

**200:** `session_id`, `livekit_url`, `token`, `room`, `mode`, `max_duration_seconds`, **`pricing`** (API-defined string; varies by `mode`).

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

## Plugin (often omitted from `GET /` index)

### `POST /v1/avatar/session`

Production `GET /` currently lists generate, jobs, realtime, TTS, health, me, status — **not** this path. Treat it as **deployment- or product-specific** (e.g. **livekit-plugins-atlas** when the customer hosts the LiveKit room); confirm it exists on your base URL before relying on `atlas_cli.py avatar-session`.

Multipart: `livekit_url`, `livekit_token`, `room_name` (strings); optional `avatar_image` file.

**200:** `{ "session_id", "status": "ok" }` (shape per your deployment).

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

## OpenClaw / agents

Prefer **`python3 core/atlas_cli.py …`** from the monorepo root (see `skills/atlas-avatar/SKILL.md`) for a single maintained client; **`curl`** remains valid for minimal environments. For production, a typed OpenClaw **plugin** avoids shell entirely.
