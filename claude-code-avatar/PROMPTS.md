# Example prompts (terminal coding agents)

Paste into your terminal coding agent after opening the **monorepo root** and setting `ATLAS_API_KEY`. The agent should run the shell commands shown in `skills/atlas-avatar/SKILL.md` or below.

---

## Terminal agent pairing (copy this whole block into the agent)

Open the repo root, start your terminal coding agent, then paste **once**:

```text
@claude-code-avatar/CLAUDE.md @skills/atlas-avatar/SKILL.md

You are my terminal agent: I describe a goal, you run the exact bash commands in this repo and paste stdout/stderr back.

Goal A — free smoke (no billing): run health + first 25 lines of index.
Goal B — paid smoke (uses a few cents): run ./claude-code-avatar/scripts/demo.sh (needs ATLAS_API_KEY in the shell).
Goal C — “make a realtime session” (paid): run atlas_session start --face-url "https://example.com/face.jpg", show JSON with token redacted, remind me to leave with session_id.

Start with Goal A, then ask which letter I want next.
```

That’s the **pairing**: the agent has repo context + permission to run shell → **Atlas** is the CLI underneath.

---

## Smoke (no key required)

> Run Atlas public health from this repo and show JSON.

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py health
python3 skills/atlas-avatar/scripts/atlas_session.py index | head -30
```

---

## Realtime passthrough (needs key + HTTPS face)

> Start a **passthrough** realtime session with this face URL, print JSON, then tell me the `session_id` and remind me to run `leave` when finished.

```bash
export ATLAS_API_KEY="…"
python3 skills/atlas-avatar/scripts/atlas_session.py start --face-url "https://example.com/face.jpg"
```

Then leave:

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py leave --session-id SESSION_ID_HERE
```

---

## Offline lip-sync job

> Submit offline `/v1/generate` with `./speech.mp3` and `./face.jpg`, poll until done, fetch result URL.

(Paths must exist; agent runs `offline` then `jobs-wait` then `jobs-result` — see `SKILL.md`.)

## Offline render → Discord (full pipeline)

> With `ATLAS_API_KEY` and `DISCORD_WEBHOOK_URL` in `.env`, run `./scripts/bridges/atlas-offline-to-discord.sh "Short intro for the channel"` and confirm the **Atlas-generated MP4** appears as an attachment in Discord.

---

## One sentence → agent composes steps

> I have `./assets/headshot.jpg` and `./assets/voice.mp3`. Create an offline Atlas avatar video job, wait for completion, and print the download URL.

Agent sequence: `atlas_session.py offline --audio … --image …` → `atlas_session.py jobs-wait` → `atlas_session.py jobs-result`.

---

## Local viewer (mic + avatar on your machine)

> Read `viewer/README.md` and outline how we would host a small page on `http://127.0.0.1` that connects to Atlas `livekit_url` + `token` + `room` after `atlas_session.py start`, so I can talk to the avatar without opening Google Meet.
