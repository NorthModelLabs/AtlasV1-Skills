# Local viewer (planned)

**Goal:** a small **default UI** you run on your machine (e.g. `http://127.0.0.1:…`) that:

1. Reads **`livekit_url`**, **`token`**, and **`room`** from `POST /v1/realtime/session` (same JSON as today).
2. Lets **you join with mic** and talk to the avatar — no Google Meet tab.

**How to get there:** host a static or Next.js page that uses **[@northmodellabs/atlas-react](https://www.npmjs.com/package/@northmodellabs/atlas-react)** (or your own LiveKit client) and mints or receives the session payload from a tiny local API you control.

This folder is reserved for that app. Until it lands, use **`python3 skills/atlas-avatar/scripts/atlas_session.py start …`** and any HTTPS viewer you already deploy.
