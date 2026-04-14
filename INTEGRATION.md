# Integrating Atlas Avatar with OpenClaw

Part of the **[avatarclaw](https://github.com/NorthModelLabs/avatarclaw)** monorepo (`core/` + `skills/`). For developers wiring OpenClaw (or any chat-completions–shaped HTTP client) with Atlas GPU avatars.

## 1. Roles

| System | Role |
|--------|------|
| **OpenClaw** | Agent orchestration, tools, optional chat/completions to your LLM |
| **Atlas API** | Realtime LiveKit sessions, offline render jobs, credits, API keys |
| **Your client** | Browser or desktop app that connects to LiveKit for video |

## 2. Install the skill

Copy **`skills/atlas-avatar`** into an OpenClaw skills path ([Creating skills](https://docs.openclaw.ai/tools/creating-skills)):

```bash
mkdir -p ~/.openclaw/workspace/skills
cp -R /path/to/avatarclaw/skills/atlas-avatar ~/.openclaw/workspace/skills/
```

**Recommended:** keep a **full clone** of the repo so `core/atlas_cli.py` exists. If the skill lives alone, set **`ATLAS_AGENT_REPO`** to the monorepo root and call `skills/atlas-avatar/scripts/run_atlas_cli.py`.

```bash
export ATLAS_API_KEY="ak_..."
export ATLAS_API_BASE="https://api.atlasv1.com"
# optional if skill copied without core/:
# export ATLAS_AGENT_REPO="/path/to/avatarclaw"
```

## 3. Python CLI vs curl

- **`python3 core/atlas_cli.py`** — preferred from the repo root after `pip install -r core/requirements.txt`.
- **`curl`** — still documented in `SKILL.md` for zero-dependency environments.

## 4. Optional: OpenClaw as the LLM backend

Same as before: configure chat in OpenClaw; Atlas calls use `ATLAS_API_KEY` separately.

## 5. Realtime / offline flows

Unchanged: create session → LiveKit client → `DELETE` when done; offline `POST /v1/generate` → poll → result.

## 6. ClawHub

Publish the **skill folder** only:

```bash
clawhub login
clawhub skill publish ./skills/atlas-avatar --slug atlas-avatar --name "Atlas Avatar" --version 1.0.3 --tags latest
```

## 7. Plugins

Use an OpenClaw **plugin** when you need typed tools, streaming, or no shell — the **core** CLI is the middle ground between raw curl and a full plugin.

## 8. Support

- **Atlas:** dashboard and support.  
- **OpenClaw:** [docs.openclaw.ai](https://docs.openclaw.ai).
