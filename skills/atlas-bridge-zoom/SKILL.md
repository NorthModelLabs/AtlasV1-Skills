---
name: atlas_bridge_zoom
description: "Guidance for combining Atlas avatars with Zoom. Use when the user asks to join Zoom, put avatar in Zoom, or integrate Atlas with Zoom meetings."
version: "0.1.0"
tags: ["atlas", "zoom", "bridge", "openclaw", "integration"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      bins: [python3]
---

# Atlas + Zoom (integration guide)

## What this skill is **not**

There is **no script here that joins a Zoom meeting as a bot** or streams Atlas into Zoom directly. That typically needs the **Zoom SDK**, **Meeting SDK / apps**, or a **third-party meeting-bot** product — plus legal and account review.

## What **Atlas** gives you

- LiveKit session credentials from `POST /v1/realtime/session`.

## Practical patterns

1. **Side-by-side** — Participants open your **Atlas web client** in a browser while on Zoom audio (or paste link in Zoom chat).
2. **Screen share** — Present the tab that shows the avatar.
3. **Enterprise integration** — Use Zoom’s developer programs to build an official app or media pipeline; connect Atlas **passthrough** on your backend if you implement audio bridging.

## Machine-readable summary

```bash
python3 skills/atlas-bridge-zoom/scripts/integration_guide.py
```
