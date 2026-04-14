# Local viewer (planned)

**Goal:** a small **default UI** you run on your machine (e.g. `http://127.0.0.1:…`) that:

1. Reads **`livekit_url`**, **`token`**, and **`room`** from `POST /v1/realtime/session` (same JSON as today).
2. Lets **you join with mic** and talk to the avatar — no Google Meet tab.

**How to get there:** host a static or Next.js page that uses **[@northmodellabs/atlas-react](https://www.npmjs.com/package/@northmodellabs/atlas-react)** (or your own LiveKit client) and mints or receives the session payload from a tiny local API you control.

This folder is reserved for that app. Until it lands, use **`python3 skills/atlas-avatar/scripts/atlas_session.py start …`** and any HTTPS viewer you already deploy.

## Passthrough mode — persistent audio track

If your viewer uses **passthrough** mode (you bring your own LLM + TTS), use the **persistent audio track pattern** for freeze-free lip-sync:

1. On connect, publish a single `MediaStreamDestination` track to the LiveKit room
2. When idle: the destination outputs silence → GPU renders idle animation (avatar stays alive)
3. When TTS plays: connect a `BufferSource` to the same destination → audio flows → avatar lip-syncs
4. When TTS ends: `BufferSource` disconnects → back to silence → avatar returns to idle

**Do not** call `session.publishAudio()` directly — it tears down the track after each call, causing the avatar to freeze between messages.

Full copy-paste code with React/Next.js: **[atlas-realtime-example](https://github.com/NorthModelLabs/atlas-realtime-example)** README and **[API docs](https://www.northmodellabs.com/api)**.
