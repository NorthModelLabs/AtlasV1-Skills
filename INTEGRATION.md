# Integrating Atlas Avatar with OpenClaw

Part of the **[avatarclaw](https://github.com/NorthModelLabs/avatarclaw)** repository. This document is for **developers** wiring OpenClaw (or any OpenAI Chat Completions–compatible client) together with Atlas GPU avatars.

## 1. Roles

| System | Role |
|--------|------|
| **OpenClaw** | Agent orchestration, tools, optional chat/completions to your LLM |
| **Atlas API** | Realtime LiveKit sessions, offline render jobs, credits, API keys |
| **Your client** | Browser or desktop app that connects to LiveKit for video |

Atlas does **not** replace OpenClaw. They compose: OpenClaw decides *when* to create a session; Atlas *runs* the avatar infrastructure.

## 2. Install the skill (teach the agent)

Copy `skill/atlas-avatar` into an OpenClaw skills path (see [Creating skills](https://docs.openclaw.ai/tools/creating-skills)):

```bash
mkdir -p ~/.openclaw/workspace/skills
cp -R /path/to/atlas-avatar-openclaw/skill/atlas-avatar ~/.openclaw/workspace/skills/
```

Set environment variables in the shell that launches OpenClaw (or in `~/.openclaw/.env` if you use one):

```bash
export ATLAS_API_KEY="ak_..."
export ATLAS_API_BASE="https://api.atlasv1.com"
```

Restart OpenClaw or start a `/new` session so skills reload.

## 3. Optional: OpenClaw as the LLM backend

If your OpenClaw install exposes an OpenAI-compatible API:

- Configure the **chat model** in OpenClaw to your provider (Anthropic, OpenAI, etc.).
- For tools that only need Atlas, the skill’s `curl` flows are enough.

If you run a **separate** app that uses `openai` Python SDK:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://YOUR_OPENCLAW_GATEWAY/.../openai",  # per OpenClaw docs
    api_key="YOUR_OPENCLAW_OR_ROUTE_KEY",
)
```

Atlas remains called over HTTPS with `ATLAS_API_KEY` — different credential.

## 4. Realtime UX flow

1. User asks the agent to “start an avatar session.”
2. Agent (via skill) calls `POST /v1/realtime/session`.
3. Agent returns `livekit_url`, `token`, `room` to the user (or your UI).
4. Your frontend uses [LiveKit client SDKs](https://docs.livekit.io/) to connect and subscribe to remote video/audio.
5. When done, agent or UI calls `DELETE /v1/realtime/session/{session_id}`.

**Conversation mode:** Atlas agent worker does STT → LLM → TTS → avatar. User speaks in the LiveKit room.

**Passthrough mode:** You send audio to the avatar track (or data path) per your integration; no Atlas-hosted LLM for that path.

## 5. Offline / batch flow

1. `POST /v1/generate` with `audio` + `image` files.
2. Poll `GET /v1/jobs/{job_id}` until terminal state.
3. `GET /v1/jobs/{job_id}/result` for download URL.

Good for OpenClaw batch jobs, CLI automation, or nightly renders.

## 6. Publishing this skill to ClawHub

```bash
npm i -g clawhub
clawhub auth
clawhub skill publish ./skill/atlas-avatar \
  --slug atlas-avatar \
  --name "Atlas Avatar" \
  --version 1.0.0 \
  --tags latest
```

Validate locally if your OpenClaw CLI supports it:

```bash
openclaw skills validate ./skill/atlas-avatar
```

*(Command availability depends on OpenClaw version.)*

## 7. When to upgrade to an OpenClaw plugin

Use a **plugin** (TypeScript, `openclaw.plugin.json`) if you need:

- Typed tools instead of `curl`
- Streaming responses
- Centralized secret handling without shell

The skill is the fastest path; the plugin is the production-hardening path.

## 8. Support

- **Atlas API / keys / billing:** Atlas dashboard and support channels.
- **OpenClaw:** [docs.openclaw.ai](https://docs.openclaw.ai) and ClawHub.
