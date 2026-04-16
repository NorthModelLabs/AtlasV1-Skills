# Atlas avatar monorepo — terminal coding agents

When driving **North Model Labs Atlas** from this repo, read the full skill and path notes:

- **`skills/atlas-avatar/SKILL.md`** — commands, env (`ATLAS_API_KEY`), offline/realtime/jobs, **`viewer-token`** (multi-viewer), curl fallbacks, billing (`leave` after realtime); **`references/api-reference.md`** + [northmodellabs.com/api](https://www.northmodellabs.com/api).
- **`claude-code-avatar/CLAUDE.md`** — cwd vs `../` paths, safety habits.

**Quick commands** (from repo root; needs venv + `pip install -r core/requirements.txt`):

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py health
python3 skills/atlas-avatar/scripts/atlas_session.py offline --audio PATH --image PATH
python3 skills/atlas-avatar/scripts/atlas_session.py jobs-wait JOB_ID
python3 skills/atlas-avatar/scripts/atlas_session.py jobs-result JOB_ID
```

**Offline fixtures:** `./claude-code-avatar/scripts/make-test-assets.sh` then paths under `claude-code-avatar/test-fixtures/`. **E2E smoke:** `./claude-code-avatar/scripts/test-offline-e2e.sh` (sources `.env` if present).

**Offline MP4 → Discord:** `./scripts/bridges/atlas-offline-to-discord.sh "Intro shown in Discord"` — needs `ATLAS_API_KEY` + `DISCORD_WEBHOOK_URL` in `.env` (see `skills/atlas-avatar/SKILL.md`).

**Discord bot:** `./scripts/bridges/run-discord-avatar-bot.sh` — `DISCORD_BOT_TOKEN` + `ATLAS_API_KEY`; **`/ask`**, **@mention**, and **reply-to-bot** need `HELICONE_API_KEY` (Helicone AI Gateway, default) or `ANTHROPIC_API_KEY` (direct); optional `HELICONE_ANTHROPIC_PROXY=1` with both keys for legacy proxy; **Message Content** for replies and @mentions. **`/generate`** = verbatim → MP4. **`/talk`** = realtime avatar session link, **`/endtalk`** = close session (set `ATLAS_VIEWER_BASE_URL`). `pip install -r skills/atlas-bridge-discord/requirements.txt` (see `skills/atlas-bridge-discord/SKILL.md`).

**Telegram bot (auto-playing video + realtime):** `./scripts/bridges/run-telegram-avatar-bot.sh` — `TELEGRAM_BOT_TOKEN` + `ATLAS_API_KEY`; **`/ask`** = Claude + auto-playing MP4, **`/generate`** = verbatim MP4, **`/talk`** = realtime Web App button (set `ATLAS_VIEWER_BASE_URL`). `pip install -r skills/atlas-bridge-telegram/requirements.txt` (see `skills/atlas-bridge-telegram/SKILL.md`).

**LLM + ElevenLabs + S3 face → Atlas → Discord:** `./scripts/bridges/atlas-narrated-avatar-to-discord.sh "Topic"` — see `.env.example` and `pip install -r scripts/requirements-narrator.txt`.

**PR → walkthrough MP4** is not a single Atlas endpoint: use `gh` (or `git`) for the diff, produce **narration audio** (your TTS/tool), pick a **face image**, then run **`offline` → `jobs-wait` → `jobs-result`** and download the presigned URL if needed.

Copy-paste prompts: **`claude-code-avatar/PROMPTS.md`**. Multi-agent context: **`AGENTS.md`**.
