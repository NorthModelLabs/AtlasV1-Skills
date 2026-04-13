# Claude Code × Atlas Avatar

Use this folder to run **Claude Code** (or any terminal agent) against the **Atlas** CLIs in this monorepo — same idea as “natural language → agent runs a vendor CLI,” except the tools are **`atlas_session.py`** / **`atlas_cli.py`**.

## 1. Prereqs

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and signed in.
- This **full repo** cloned (`core/` + `skills/` + optional `meeting-bot/`, `google-meet/`).
- Python 3.10+ and:

  ```bash
  pip install -r core/requirements.txt
  ```

## 2. API key

```bash
export ATLAS_API_KEY="ak_…"   # Atlas dashboard
# optional:
export ATLAS_API_BASE="https://api.atlasv1.com"
```

## 3. Open the repo in Claude Code

From the **monorepo root**:

```bash
cd /path/to/atlas-avatar-openclaw
claude
```

In the first message, **attach context** so the agent knows Atlas rules:

- `@claude-code-avatar/CLAUDE.md`
- or `@skills/atlas-avatar/SKILL.md`

**Fastest terminal-agent pairing:** open **`PROMPTS.md`** and copy the block under **“Terminal agent pairing (copy this whole block into Claude Code)”** — it tells Claude Code to run Goal A / B / C against this repo.

## 4. Practical test (terminal)

```bash
./claude-code-avatar/scripts/demo.sh
```

- **Without** `ATLAS_API_KEY`: runs **health** + **index** only (no cost).
- **With** `ATLAS_API_KEY`: starts a short **passthrough** session, writes `claude-code-avatar/.demo-session.json`, **deletes** the session, removes the file.

## 5. Natural language via the agent

See **`PROMPTS.md`** for copy-paste prompts. Claude Code should translate them into the Python commands above (or `curl` from `SKILL.md`).

### Do you need a separate “Claude skill”?

**No.** Claude Code uses **this repo + `@` files** (`CLAUDE.md`, `SKILL.md`) and **Bash**. There is no extra install step beyond `pip install -r core/requirements.txt` and `ATLAS_API_KEY`.

**OpenClaw** is different: it loads folders under `skills/` as **OpenClaw skills**. For Claude Code, the parallel is **`claude-code-avatar/`** docs + prompts — not the same packaging as `skills/atlas-avatar/` for OpenClaw.

## 6. Limits (honest)

- No bundled **Google Meet bot tile** — Meet is screen-share / separate bridge; see repo `meeting-bot/` and `google-meet/`.
- **Offline** needs real **audio + image files** on disk.
- **Conversation** realtime needs a reachable **`--face-url`** (HTTPS image).

## Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Short agent instructions + paths |
| `PROMPTS.md` | Example user prompts |
| `scripts/demo.sh` | Runnable smoke / optional paid smoke |
