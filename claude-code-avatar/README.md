# Claude Code × Atlas Avatar

Use this folder to run **Claude Code** (or any terminal agent) against the **Atlas** CLIs in this monorepo — similar in spirit to vendor demos that run `heygen …` from the agent, but here the tools are **`atlas_session.py`** / **`atlas_cli.py`**.

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

## 4. Practical test (terminal)

```bash
./claude-code-avatar/scripts/demo.sh
```

- **Without** `ATLAS_API_KEY`: runs **health** + **index** only (no cost).
- **With** `ATLAS_API_KEY`: starts a short **passthrough** session, writes `claude-code-avatar/.demo-session.json`, **deletes** the session, removes the file.

## 5. “HeyGen-style” natural language

See **`PROMPTS.md`** for copy-paste prompts. Claude Code should translate them into the Python commands above (or `curl` from `SKILL.md`).

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
