---
name: atlas_bridge_discord
description: "Post an Atlas realtime session summary to Discord via channel Webhook URL. Use when the user wants Discord notification or to share avatar session info after atlas-avatar start."
version: "0.1.0"
tags: ["atlas", "discord", "webhook", "bridge", "openclaw"]
author: "northmodellabs"
metadata:
  openclaw:
    requires:
      env: [DISCORD_WEBHOOK_URL]
      bins: [python3]
---

# Atlas → Discord (webhook bridge)

This skill does **not** join Discord voice channels or stream avatar video into Discord. It **posts a message** via a [Discord Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

## Prerequisites

1. Channel Settings → Integrations → Webhooks → New Webhook → copy URL.
2. `export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."`

## Usage

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python3 skills/atlas-bridge-discord/scripts/post_session.py < session.json
python3 skills/atlas-bridge-discord/scripts/post_session.py --file session.json
```

**Deps:** `pip install -r skills/atlas-bridge-discord/requirements.txt`

## Voice / video in Discord

That requires a **Discord bot** with the Gateway voice stack, media forwarding, and usually a **custom service** to bridge audio to/from Atlas LiveKit — out of scope for this webhook skill.

## Security

- Webhook URL is a secret; anyone with it can post to the channel.
