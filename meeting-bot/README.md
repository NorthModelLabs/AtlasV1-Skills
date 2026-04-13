# OSS meeting helpers (local / self-hosted)

Experimental **open-source** utilities you can run **on your own machine** (or later on a VM). They do **not** replace Google Meet or Workspace support, and they are **not** an official Meet API integration.

| Script | What it does |
|--------|----------------|
| **`playwright_meet.py`** | Opens **headed Chromium** with a **persistent profile** at your Meet URL. **You** sign in and click **Join** like a normal user. |
| **`livekit_publish_tone.py`** | Uses Atlas **`session.json`** to join the **LiveKit** room as another participant and publish a **quiet 440 Hz tone** (proves second-participant audio path for **passthrough** experiments). |

This is **not** the same as a commercial “Meet bot tile” product: Meet still sees **one browser** you control; LiveKit sees **your Atlas session + optional Python publisher**.

---

## Legal / policy

- Read [Google Meet acceptable use](https://support.google.com/meet/answer/9852160) and your **Workspace admin** policies before automating browsers.
- Headed automation can still be treated as suspicious; prefer official Meet APIs / certified integrations for production.

---

## Install (local)

From **repo root**:

```bash
python3 -m venv .venv-meeting && source .venv-meeting/bin/activate  # Windows: .venv-meeting\Scripts\activate
pip install -r meeting-bot/requirements.txt
playwright install chromium
```

---

## Typical local test

**Terminal A — Atlas session**

```bash
export ATLAS_API_KEY="ak_..."
pip install -r core/requirements.txt
python3 skills/atlas-avatar/scripts/atlas_session.py start --mode passthrough > meeting-bot/session.json
```

**Terminal B — Meet in browser (you join manually)**

```bash
python3 meeting-bot/playwright_meet.py --meet-url "https://meet.google.com/your-code"
```

**Terminal C — LiveKit tone (optional)**

```bash
python3 meeting-bot/livekit_publish_tone.py -f meeting-bot/session.json --duration 30
```

In Meet, **present** the Chromium window or your separate avatar viewer tab if you use one. Routing **Meet audio → Atlas** requires OS virtual cables (e.g. BlackHole on macOS) or a custom capture pipeline — not included here.

---

## Hosted later

The same scripts run on a Linux VM with Xvfb + `playwright install-deps` (more fragile). For production Meet bots, plan for compliance, scaling, and usually **Meet partner / media APIs** rather than only browser automation.

---

## Related

- `google-meet/meet_workflow.py` — chains Atlas `start` + Meet chat paste text.
- `skills/atlas-bridge-google-meet/` — docs + `meet_assist.py`.
