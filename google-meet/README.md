# Google Meet × Atlas (workflow agent)

Small **orchestration CLI** next to the main monorepo: start an **Atlas** realtime session, save JSON, and run **`meet_assist`** (checklist, open browser, draft Meet chat text).

## What this is **not**

It does **not** implement a **synthetic Meet participant** (no bot that joins `meet.google.com` on its own). That requires a separate **meeting-bot / media bridge** product or service. This folder only **chains** existing repo scripts so an **OpenClaw agent** (or a human) can run one command from the monorepo root.

## Requirements

- This directory lives **inside** the [avatarclaw / AtlasV1-Skills](https://github.com/NorthModelLabs/avatarclaw) clone (so `skills/atlas-avatar/...` exists), **or** set **`ATLAS_AGENT_REPO`** to that monorepo root.
- `ATLAS_API_KEY` for `session start`.
- Python 3.10+ (stdlib + subprocess; same deps as core once `atlas_session` runs — install `pip install -r core/requirements.txt` from repo root).

## Commands

**Important:** the CLI prints a **draft message in your terminal**. Nothing is sent into Google Meet automatically — you must **open Meet → Chat → paste** (⌘V / Ctrl+V). Meet’s own “join” / invite UI is only for **Meet participants**; Atlas does not register a Meet user.

From **monorepo root** (recommended):

```bash
export ATLAS_API_KEY="ak_..."
pip install -r core/requirements.txt

# One shot: create session JSON + print Meet chat paste (optional: open Meet in browser)
python3 google-meet/meet_workflow.py up \
  --meet-url "https://meet.google.com/xxx-xxxx-xxx" \
  --output ./session.json \
  --mode conversation \
  --face-url "https://example.com/face.jpg" \
  --viewer-url "https://yourapp.com/avatar/..." \
  --open-meet \
  --copy
```

`--copy` (macOS only) runs `pbcopy` so you can paste the block straight into Meet chat.

**Pieces only:**

```bash
python3 google-meet/meet_workflow.py checklist --meet-url "https://meet.google.com/..."
python3 google-meet/meet_workflow.py open-meet --meet-url "https://meet.google.com/..."
python3 google-meet/meet_workflow.py paste --meet-url "..." --session-file session.json --viewer-url "https://..."
```

## How to test “join Meet” today (human path)

There is **no** automated Meet join in this repo. You test by **you** joining the call like any participant, then attaching the avatar **outside** Meet (side tab or screen share).

1. **Create or open a Meet** and copy the `https://meet.google.com/...` link.
2. From the monorepo root, run `meet_workflow.py up` with `--open-meet` so the Meet tab opens (you click **Ask to join** / **Join now** as yourself).
3. After the command prints the chat block, use **`--copy`** on macOS, then in Meet click **Chat** and **paste** — that tells others how to open your **viewer** link (you still need a real HTTPS viewer that uses the LiveKit token from `session.json` server-side).
4. **You** “bring the avatar” by either:
   - opening your viewer in **Chrome** and **presenting that tab** in Meet, or  
   - having guests open the **viewer URL** from chat (same as a normal link).

5. When finished: `python3 skills/atlas-avatar/scripts/atlas_session.py leave --session-id …` (or `core/atlas_cli.py realtime delete …`) so the realtime session stops billing.

**If you need a bot tile inside Meet** (no human presenter): that is a **different product** (e.g. hosted meeting skills such as [Pika-Skills](https://github.com/Pika-Labs/Pika-Skills), or your own bot service) plus usually Atlas **passthrough** — not something `meet_workflow.py` can turn on by itself.

## OpenClaw

Copy or symlink `google-meet/` into the agent workspace if you want the agent to run `meet_workflow.py`, or teach the agent to invoke it by absolute path from a full clone. The agent still needs **`viewer_url`** from **your** hosted viewer (LiveKit token minted server-side).

## Related

- `skills/atlas-bridge-google-meet/` — `meet_assist.py`, `integration_guide.py`, `SKILL.md`
- `skills/atlas-avatar/` — Atlas API skill + `atlas_session.py`
