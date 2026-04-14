# Atlas Avatar — terminal agent notes

Use this file when the agent should drive **North Model Labs Atlas** from this monorepo.

## Repo layout (paths)

- If your **cwd is the monorepo root** (contains `skills/` and `core/`):

  ```bash
  python3 skills/atlas-avatar/scripts/atlas_session.py health
  python3 skills/atlas-avatar/scripts/atlas_session.py start --mode conversation --face-url "https://…"
  python3 core/atlas_cli.py realtime create --mode passthrough
  ```

- If your **cwd is `claude-code-avatar/`**, prefix with `../`:

  ```bash
  python3 ../skills/atlas-avatar/scripts/atlas_session.py health
  ```

## Environment

- `ATLAS_API_KEY` — required for `start`, `offline`, `me`, etc.
- `ATLAS_API_BASE` — optional (default `https://api.atlasv1.com`).

## Safe habits

- Never print or commit real keys. Redact `token` in logs.
- After `start`, always `leave --session-id …` when done (billing).
- Atlas does **not** join Meet/Zoom/Teams as a bot. After `start`, open your **viewer** with `livekit_url` + `token` + `room` (planned default: `viewer/README.md`) or post `viewer_url` to Discord/Slack.

## Docs in this repo

- `skills/atlas-avatar/SKILL.md` — full OpenClaw-style skill.
- `skills/atlas-avatar/references/api-reference.md` — HTTP reference.
