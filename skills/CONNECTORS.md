# Connector skills (Slack, Discord, Meet, Zoom)

| Skill folder | What it does |
|--------------|----------------|
| `atlas-bridge-slack` | **Working:** post session summary via **Slack Incoming Webhook** (`SLACK_WEBHOOK_URL`). |
| `atlas-bridge-discord` | **Working:** post session summary via **Discord webhook** (`DISCORD_WEBHOOK_URL`). |
| `atlas-bridge-google-meet` | **Guide only:** JSON + docs — Atlas does not join Meet from this repo. |
| `atlas-bridge-zoom` | **Guide only:** JSON + docs — Atlas does not join Zoom from this repo. |

Copy any folder into your OpenClaw `skills/` directory alongside `atlas-avatar`:

```bash
cp -R skills/atlas-bridge-slack ~/.openclaw/workspace/skills/
```

**Flow:** create session with `atlas_session.py start … > session.json`, then `post_session.py` for Slack/Discord.

Real **meeting-bot** behavior (synthetic participant inside Meet/Zoom) requires separate infrastructure or vendors — see each skill’s `SKILL.md`.
