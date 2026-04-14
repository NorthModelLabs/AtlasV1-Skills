# Terminal coding agents × Atlas Avatar

Use this folder to run a **terminal coding agent** (any vendor) against the **Atlas** CLIs in this monorepo — natural language → the agent runs **`atlas_session.py`** / **`atlas_cli.py`** in Bash.

## 1. Prereqs

- Your terminal coding agent installed and signed in (follow **its** official documentation).
- This **full repo** cloned (`core/` + `skills/` + `scripts/`).
- Python 3.10+ and `requests` (Atlas CLI). On **macOS Homebrew Python**, use a venv (PEP 668 blocks global `pip install`):

  ```bash
  python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
  pip install -r core/requirements.txt
  ```

## 2. API key

```bash
export ATLAS_API_KEY="ak_…"   # Atlas dashboard
# optional:
export ATLAS_API_BASE="https://api.atlasv1.com"
```

## 3. Open the repo in your agent

From the **monorepo root**:

```bash
cd /path/to/atlas-avatar-openclaw
# then start your terminal coding agent the way its docs say
```

In the first message, **attach context** so the agent knows Atlas rules:

- `@claude-code-avatar/CLAUDE.md`
- or `@skills/atlas-avatar/SKILL.md`

**Fastest pairing:** open **`PROMPTS.md`** and copy the block under **“Terminal agent pairing”** — it tells the agent to run Goal A / B / C against this repo.

## 4. Practical test (terminal)

With your venv **activated** (see §1):

```bash
./claude-code-avatar/scripts/demo.sh
```

- **Without** `ATLAS_API_KEY`: runs **health** + **index** only (no cost).
- **With** `ATLAS_API_KEY`: starts a short **passthrough** session, writes `claude-code-avatar/.demo-session.json`, **deletes** the session, removes the file.

**CI / sanity:** run everything the README promises except opening the interactive agent:

```bash
./claude-code-avatar/scripts/verify-readme.sh
```

## 5. Natural language via the agent

See **`PROMPTS.md`** for copy-paste prompts. The agent should translate them into the Python commands above (or `curl` from `SKILL.md`).

### Do you need a separate vendor “skill pack” for the agent?

**No.** Terminal agents use **this repo + `@` files** (`CLAUDE.md`, `SKILL.md`) and **Bash**. There is no extra install step beyond `pip install -r core/requirements.txt` and `ATLAS_API_KEY`.

**OpenClaw** is different: it loads folders under `skills/` as **OpenClaw skills**. For terminal coding agents, the parallel is **`claude-code-avatar/`** docs + prompts — not the same packaging as `skills/atlas-avatar/` for OpenClaw.

## 6. Limits (honest)

- No bundled **synthetic meeting-tile bot** — Atlas returns LiveKit join info; use your **viewer** (see `viewer/README.md`) or Slack/Discord bridges (`skills/CONNECTORS.md`).
- **Offline** needs real **audio + image files** on disk.
- **Conversation** realtime needs a reachable **`--face-url`** (HTTPS image).

## Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Short agent instructions + paths (this folder) |
| `../CLAUDE.md` | Same intent at **monorepo root** for agents that load it automatically |
| `PROMPTS.md` | Example user prompts |
| `scripts/demo.sh` | Runnable smoke / optional paid smoke |
