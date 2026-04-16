# AGENTS.md — Atlas Avatar skills monorepo

Multi-agent context file for Claude Code, Codex, Cursor, and other AI coding agents.

## Entry points

| File | When to read |
|------|-------------|
| `skills/atlas-avatar/SKILL.md` | Commands, env (`ATLAS_API_KEY`), offline/realtime/jobs, viewer tokens, curl fallbacks, billing |
| `skills/atlas-avatar/references/api-reference.md` | Full HTTP reference |
| `claude-code-avatar/CLAUDE.md` | cwd vs `../` paths, safety habits |
| `claude-code-avatar/PROMPTS.md` | Copy-paste prompts for terminal agents |
| `skills/atlas-bridge-discord/SKILL.md` | Discord webhook + optional interactive bot |
| `skills/atlas-bridge-slack/SKILL.md` | Slack webhook + optional bot MP4 upload |
| `skills/atlas-bridge-telegram/SKILL.md` | Telegram bot: auto-playing video + realtime Web App |
| `skills/CONNECTORS.md` | Connector index (Slack, Discord, Telegram) |
| `INTEGRATION.md` | OpenClaw integration, ClawHub publish |

## Quick commands (from repo root)

```bash
pip install -r core/requirements.txt

python3 skills/atlas-avatar/scripts/atlas_session.py health
python3 skills/atlas-avatar/scripts/atlas_session.py offline --audio PATH --image PATH
python3 skills/atlas-avatar/scripts/atlas_session.py jobs-wait JOB_ID
python3 skills/atlas-avatar/scripts/atlas_session.py jobs-result JOB_ID
```

## Environment

- `ATLAS_API_KEY` — required for most commands
- `ATLAS_API_BASE` — optional (default `https://api.atlasv1.com`)
- `ATLAS_AGENT_REPO` — set only if `core/` is not next to `skills/`

## Safety

- Never print or commit real keys. Redact `token` in logs.
- After `start`, always `leave --session-id …` when done (billing).
- Atlas does **not** join Meet/Zoom/Teams as a bot.

## Testing

- **Offline fixtures:** `./claude-code-avatar/scripts/make-test-assets.sh`
- **E2E smoke:** `./claude-code-avatar/scripts/test-offline-e2e.sh` (sources `.env`)
- **Webhook smoke:** `./scripts/bridges/test-discord-webhook.sh`, `./scripts/bridges/test-slack-webhook.sh`
- **API harness:** `python3 scripts/bridges/test-atlas-api-harness.py --help`

## Bridges

- **Discord:** `./scripts/bridges/atlas-offline-to-discord.sh "intro"`
- **Discord bot:** `./scripts/bridges/run-discord-avatar-bot.sh` (`/ask`, `/generate`, `/talk` realtime, `/endtalk`)
- **Telegram bot:** `./scripts/bridges/run-telegram-avatar-bot.sh` (auto-playing video + `/talk` realtime, `/endtalk`)
- **Slack:** `./scripts/bridges/atlas-offline-to-slack.sh "intro"`
- **Narrated:** `./scripts/bridges/atlas-narrated-avatar-to-discord.sh "topic"`

## Viewer

Deploy [atlas-avatar-viewer](https://github.com/NorthModelLabs/atlas-avatar-viewer) (single static HTML) and set `ATLAS_VIEWER_BASE_URL` in `.env`. The `/talk` command in Discord and Telegram bots will send a clickable link that opens the realtime avatar viewer on any device. For a full-featured local viewer, see [atlas-realtime-example](https://github.com/NorthModelLabs/atlas-realtime-example).
