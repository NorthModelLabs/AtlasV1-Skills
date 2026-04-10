---
name: atlas_bridge_google_meet
description: "Guidance for combining Atlas avatars with Google Meet. Use when the user asks to join Meet, put avatar in Meet, or integrate Atlas with Google Meet — explains what is and is not possible from this repo alone."
version: "0.1.0"
tags: ["atlas", "google-meet", "bridge", "openclaw", "integration"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      bins: [python3]
---

# Atlas + Google Meet (integration guide)

## What this skill is **not**

There is **no script here that joins Meet as a bot** or injects Atlas video into Meet. That requires **Google Workspace / Meet APIs**, **certified integrations**, or a **hosted meeting-bot service** — similar in scope to how other vendors ship a cloud `meeting-session` API.

## What **Atlas** gives you

- `POST /v1/realtime/session` → `livekit_url`, `token`, `room` for a **LiveKit** client (web or app).

## Practical patterns

1. **Link in chat** — Paste your **web client URL** (your app that connects to LiveKit) into Meet chat so participants open the avatar in a side tab.
2. **Presenter workflow** — Share browser tab that shows your Atlas/LiveKit client (screen share).
3. **Build or buy a bot** — Use a **Meet bot platform** or internal gateway that joins Meet and bridges media to your pipeline, then Atlas **passthrough** if you feed audio correctly (major engineering + policy review).

## Machine-readable summary

```bash
python3 skills/atlas-bridge-google-meet/scripts/integration_guide.py
```

Returns JSON with official doc hints and recommended next steps for engineers.
