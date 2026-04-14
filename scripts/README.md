# Scripts

| Path | Purpose |
|------|---------|
| **`bridges/`** | Slack / Discord webhooks, `atlas-offline-to-{slack,discord}.sh`, smoke tests. Run from repo root. |
| **`avatar_discord_narrator.py`** | Claude (optional) + ElevenLabs + S3/local face → Atlas offline → Discord. |
| **`elevenlabs_to_wav.py`** | ElevenLabs line → WAV for Atlas offline (used by `atlas-offline-to-slack.sh` when `ATLAS_OFFLINE_SPEAK_TEXT` is set). |
| **`pull_atlas_demo_face.py`** | *(Optional, gitignored.)* If you add this script locally, `make-test-assets.sh` can pull a face from your S3 demo prefixes before falling back to URL. |
| **`requirements-narrator.txt`** | `pip install -r scripts/requirements-narrator.txt` for the narrator. |

Core Atlas HTTP helpers live in **`../core/`**; the agent-facing verb CLI is **`../skills/atlas-avatar/scripts/atlas_session.py`**.
