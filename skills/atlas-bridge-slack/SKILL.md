---
name: atlas_bridge_slack
description: "Post an Atlas realtime session summary (LiveKit join hints) to a Slack channel via Incoming Webhook. Use when the user wants Slack notification, share avatar session to Slack, or bridge Atlas session info to Slack after creating a session with atlas-avatar."
version: "0.1.0"
tags: ["atlas", "slack", "webhook", "bridge", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [SLACK_WEBHOOK_URL]
      bins: [python3]
---

# Atlas → Slack (webhook bridge)

This skill does **not** join Slack Huddles or inject video into calls. It **posts a message** to a channel using a [Slack Incoming Webhook](https://api.slack.com/messaging/webhooks).

## Prerequisites

1. Create an Incoming Webhook for your workspace → copy the URL.
2. `export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."`

## Usage

After `atlas_session.py start` (or equivalent), pipe or pass the JSON:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python3 skills/atlas-bridge-slack/scripts/post_session.py < session.json
# or
python3 skills/atlas-bridge-slack/scripts/post_session.py --file session.json
```

**Install deps:** `pip install -r skills/atlas-bridge-slack/requirements.txt`

## What gets posted

- `session_id`, `room`, `mode`, `pricing` (if present)
- Instructions to open your **Atlas / LiveKit web client** (this repo does not host that UI)

## Security

- Treat `SLACK_WEBHOOK_URL` as a secret (same power as posting to the channel).
- Do not paste LiveKit JWTs into public channels if your policy forbids it.
