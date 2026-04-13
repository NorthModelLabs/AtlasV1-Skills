# Example prompts (Claude Code / terminal agents)

Paste into Claude Code after opening the **monorepo root** and setting `ATLAS_API_KEY`. The agent should run the shell commands shown in `skills/atlas-avatar/SKILL.md` or below.

---

## Smoke (no key required)

> Run Atlas public health from this repo and show JSON.

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py health
python3 skills/atlas-avatar/scripts/atlas_session.py index | head -30
```

---

## Realtime conversation (needs key + HTTPS face)

> Start a **conversation** realtime session with this face URL, print JSON, then tell me the `session_id` and remind me to run `leave` when finished.

```bash
export ATLAS_API_KEY="…"
python3 skills/atlas-avatar/scripts/atlas_session.py start --mode conversation --face-url "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=256&h=256&fit=crop"
```

Then leave:

```bash
python3 skills/atlas-avatar/scripts/atlas_session.py leave --session-id SESSION_ID_HERE
```

---

## Offline lip-sync job

> Submit offline `/v1/generate` with `./speech.mp3` and `./face.jpg`, poll until done, fetch result URL.

(Paths must exist; agent runs `offline` then `jobs-wait` then `jobs-result` — see `SKILL.md`.)

---

## HeyGen-style “one sentence” (agent composes steps)

> I have `./assets/headshot.jpg` and `./assets/voice.mp3`. Create an offline Atlas avatar video job, wait for completion, and print the download URL.

Agent sequence: `offline --audio … --image …` → `jobs-wait` → `jobs-result`.

---

## Local viewer + Meet (screen share)

> Run the local conversation demo opening Meet `https://meet.google.com/…` with this face URL, and tell me to screen-share the localhost tab.

```bash
python3 meeting-bot/local_conversation_demo.py --meet-url "https://meet.google.com/xxx" --face-url "https://…"
```
