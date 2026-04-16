#!/usr/bin/env python3
"""Telegram bot: /ask, /generate, /talk → Atlas avatar (offline MP4 + realtime Web App).

- **/ask** — Claude answers; offline lip-sync MP4 auto-plays in chat.
- **/generate** — verbatim script → offline lip-sync MP4.
- **/talk** — creates a realtime Atlas session and sends a Web App button so the user
  can talk to the avatar live inside Telegram (or browser).
- **Plain text** — same as /ask (Claude answer + MP4).

MP4 videos auto-play inline in Telegram (no click required) — better UX than Discord.

Env
---
**Required:** ``TELEGRAM_BOT_TOKEN``, ``ATLAS_API_KEY``

**For /ask + plain text:** ``HELICONE_API_KEY`` (Helicone AI Gateway — default) or ``ANTHROPIC_API_KEY``
(direct Anthropic). ``HELICONE_ANTHROPIC_PROXY=1`` with both keys → legacy proxy.
``LLM_MODEL`` optional.

**For /talk (realtime):** ``ATLAS_VIEWER_BASE_URL`` — your deployed atlas-realtime-example
(e.g. ``https://your-avatar.vercel.app``). Without it, /talk returns raw LiveKit credentials.

**Optional:** ``ELEVENLABS_API_KEY`` (+ ``ELEVENLABS_VOICE_ID``) for real speech;
else test tone WAV. ``ATLAS_OFFLINE_IMAGE`` — face image path.

Usage::

  cd /path/to/repo && pip install -r skills/atlas-bridge-telegram/requirements.txt
  python3 skills/atlas-bridge-telegram/scripts/telegram_avatar_bot.py
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

import requests
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

_MAX_SCRIPT_CHARS = 1800
_MAX_TELEGRAM_VIDEO_BYTES = 50 * 1024 * 1024
_REPO = Path(__file__).resolve().parents[3]


def _load_dotenv() -> None:
    env = _REPO / ".env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _run_json(cmd: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    r = subprocess.run(
        cmd,
        cwd=cwd or _REPO,
        capture_output=True,
        text=True,
        timeout=720,
        check=False,
        env=os.environ.copy(),
    )
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "command failed").strip()[:2000])
    out = (r.stdout or "").strip()
    if not out:
        raise RuntimeError("empty command output")
    return json.loads(out)


# ---------------------------------------------------------------------------
# LLM (same routing as Discord bot: Helicone gateway → Anthropic native)
# ---------------------------------------------------------------------------

def _helicone_gateway_completion(prompt: str) -> str:
    key = os.environ.get("HELICONE_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip() or "claude-sonnet-4"
    url = "https://ai-gateway.helicone.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "max_tokens": 600,
        "temperature": 0.7,
        "user": f"telegram-avatar-{uuid.uuid4()}",
        "messages": [{"role": "user", "content": prompt.strip()[:8000]}],
    }
    r = requests.post(url, headers=headers, json=body, timeout=120)
    if not r.ok:
        raise RuntimeError((r.text or r.reason)[:1500])
    data = r.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"LLM returned no choices: {data!r}"[:1500])
    msg = choices[0].get("message") or {}
    text = (msg.get("content") or "").strip()
    if not text:
        raise RuntimeError("LLM returned empty text.")
    return text[:_MAX_SCRIPT_CHARS]


def _anthropic_native_completion(prompt: str, *, use_helicone_proxy: bool) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing ANTHROPIC_API_KEY for native Anthropic / legacy proxy path.")
    model = os.environ.get("LLM_MODEL", "").strip() or "claude-sonnet-4-20250514"
    helicone = os.environ.get("HELICONE_API_KEY", "").strip()
    if use_helicone_proxy:
        if not helicone:
            raise RuntimeError("HELICONE_ANTHROPIC_PROXY=1 requires HELICONE_API_KEY as well.")
        url = "https://anthropic.helicone.ai/v1/messages"
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
            "Helicone-Auth": f"Bearer {helicone}",
        }
    else:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
    body = {
        "model": model,
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt.strip()[:8000]}],
    }
    r = requests.post(url, headers=headers, json=body, timeout=120)
    if not r.ok:
        raise RuntimeError((r.text or r.reason)[:1500])
    data = r.json()
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    text = text.strip()
    if not text:
        raise RuntimeError("LLM returned empty text.")
    return text[:_MAX_SCRIPT_CHARS]


def _anthropic_completion(prompt: str) -> str:
    helicone = os.environ.get("HELICONE_API_KEY", "").strip()
    anthropic = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    legacy_proxy = _truthy_env("HELICONE_ANTHROPIC_PROXY")

    if legacy_proxy and anthropic and helicone:
        return _anthropic_native_completion(prompt, use_helicone_proxy=True)
    if helicone and not legacy_proxy:
        return _helicone_gateway_completion(prompt)
    if anthropic:
        return _anthropic_native_completion(prompt, use_helicone_proxy=False)
    raise RuntimeError(
        "Set HELICONE_API_KEY for /ask (Helicone AI Gateway — default), or ANTHROPIC_API_KEY "
        "for direct Anthropic. /generate needs no LLM."
    )


def _llm_spoken_answer(question: str) -> str:
    q = question.strip()[:4000]
    prompt = (
        "The user asked a question. Write a SHORT spoken answer (under 120 words) for a talking-head "
        "AI avatar to lip-sync. Plain words only — no bullet points, no markdown, no stage directions, "
        "no preamble like 'Here is the answer'. Only the words the avatar should speak.\n\n"
        f"Question:\n{q}"
    )
    return _anthropic_completion(prompt)


# ---------------------------------------------------------------------------
# Atlas offline render → MP4
# ---------------------------------------------------------------------------

def _render_offline_video(script: str) -> tuple[Path | None, str | None, str | None]:
    """Return (mp4_path_or_none, presigned_url, error_message)."""
    script = script.strip()[:_MAX_SCRIPT_CHARS]
    if not script:
        return None, None, "Empty script."

    work = Path(tempfile.mkdtemp(prefix="telegram-avatar-bot-"))
    try:
        subprocess.run(
            [str(_REPO / "claude-code-avatar/scripts/make-test-assets.sh")],
            cwd=_REPO,
            capture_output=True,
            timeout=120,
            check=False,
        )

        eleven = os.environ.get("ELEVENLABS_API_KEY", "").strip()
        if eleven:
            wav = work / "speech.wav"
            r = subprocess.run(
                [
                    sys.executable,
                    str(_REPO / "scripts/elevenlabs_to_wav.py"),
                    script,
                    str(wav),
                ],
                cwd=_REPO,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
                env=os.environ.copy(),
            )
            if r.returncode != 0 or not wav.is_file():
                shutil.rmtree(work, ignore_errors=True)
                return None, None, (r.stderr or r.stdout or "ElevenLabs WAV failed")[:1500]
            audio = wav
        else:
            audio = _REPO / "claude-code-avatar/test-fixtures/speech.wav"
            if not audio.is_file():
                shutil.rmtree(work, ignore_errors=True)
                return None, None, f"Missing fixture WAV: {audio}"

        img = Path(os.environ.get("ATLAS_OFFLINE_IMAGE", "").strip() or "")
        if not img.is_file():
            img = _REPO / "claude-code-avatar/test-fixtures/face.jpg"
        if not img.is_file():
            shutil.rmtree(work, ignore_errors=True)
            return None, None, f"Missing face image: {img}"

        atlas = sys.executable
        session_py = str(_REPO / "skills/atlas-avatar/scripts/atlas_session.py")

        try:
            offline = _run_json([atlas, session_py, "offline", "--audio", str(audio), "--image", str(img)])
        except Exception as e:
            shutil.rmtree(work, ignore_errors=True)
            return None, None, str(e)[:1500]
        job = offline.get("job_id") or offline.get("id") or ""
        if not job:
            shutil.rmtree(work, ignore_errors=True)
            return None, None, f"No job_id in offline response: {offline!r}"[:1500]

        w = subprocess.run(
            [atlas, session_py, "jobs-wait", str(job), "--interval", "3", "--timeout", "600"],
            cwd=_REPO,
            capture_output=True,
            text=True,
            timeout=720,
            check=False,
            env=os.environ.copy(),
        )
        if w.returncode != 0:
            shutil.rmtree(work, ignore_errors=True)
            return None, None, (w.stderr or w.stdout or "jobs-wait failed")[:1500]

        try:
            result = _run_json([atlas, session_py, "jobs-result", str(job)])
        except Exception as e:
            shutil.rmtree(work, ignore_errors=True)
            return None, None, str(e)[:1500]
        url = (result.get("url") or "").strip()
        if not url:
            shutil.rmtree(work, ignore_errors=True)
            return None, None, f"No url in jobs-result: {result!r}"[:800]

        mp4 = work / "atlas-render.mp4"
        try:
            rr = requests.get(url, timeout=300)
            rr.raise_for_status()
            mp4.write_bytes(rr.content)
        except Exception as e:
            shutil.rmtree(work, ignore_errors=True)
            return None, None, str(e)[:1500]

        if mp4.stat().st_size > _MAX_TELEGRAM_VIDEO_BYTES:
            shutil.rmtree(work, ignore_errors=True)
            return None, url, None
        return mp4, url, None
    except Exception as e:
        shutil.rmtree(work, ignore_errors=True)
        return None, None, str(e)[:1500]


_render_lock = asyncio.Lock()

# Per-user active realtime session: user_id → {"session_id": ..., "creating": bool}
_active_talk: dict[int, dict[str, Any]] = {}
_talk_locks: dict[int, asyncio.Lock] = {}


def _talk_lock_for(user_id: int) -> asyncio.Lock:
    if user_id not in _talk_locks:
        _talk_locks[user_id] = asyncio.Lock()
    return _talk_locks[user_id]


# ---------------------------------------------------------------------------
# Realtime session → viewer link / Web App button
# ---------------------------------------------------------------------------

def _create_realtime_session(face_url: str | None = None) -> dict[str, Any]:
    atlas = sys.executable
    session_py = str(_REPO / "skills/atlas-avatar/scripts/atlas_session.py")
    cmd = [atlas, session_py, "start"]
    if face_url:
        cmd += ["--face-url", face_url]
    return _run_json(cmd)


def _leave_session(session_id: str) -> None:
    atlas = sys.executable
    session_py = str(_REPO / "skills/atlas-avatar/scripts/atlas_session.py")
    subprocess.run(
        [atlas, session_py, "leave", "--session-id", session_id],
        cwd=_REPO, capture_output=True, timeout=30, check=False,
        env=os.environ.copy(),
    )


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! I'm an Atlas avatar bot.\n\n"
        "/ask <question> — I answer with a lip-sync video (auto-plays)\n"
        "/generate <script> — avatar speaks your exact words\n"
        "/talk — open a live realtime avatar session\n"
        "/endtalk — close your active session (stops billing)\n\n"
        "Or just send me any message and I'll answer with a video."
    )


async def _cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(context.args or []).strip()
    if not question:
        await update.message.reply_text("Usage: /ask <your question>")
        return
    await _handle_ask(update, question)


async def _cmd_generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    script = " ".join(context.args or []).strip()
    if not script:
        await update.message.reply_text("Usage: /generate <script for avatar to speak>")
        return
    msg = await update.message.reply_text("Rendering lip-sync video...")
    async with _render_lock:
        path, url, err = await asyncio.to_thread(_render_offline_video, script)
    if err:
        await msg.edit_text(f"Could not render: {err}")
        return
    if path is not None:
        await msg.delete()
        with open(path, "rb") as f:
            await update.message.reply_video(
                video=f,
                caption="Here is your lip-sync clip (verbatim).",
                supports_streaming=True,
            )
        shutil.rmtree(path.parent, ignore_errors=True)
        return
    if url:
        await msg.edit_text(f"Video is too large for Telegram upload.\n\nDownload: {url}")
        return
    await msg.edit_text("Unknown render error.")


async def _cmd_talk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a realtime session — at most one per user at a time."""
    user_id = update.effective_user.id
    lock = _talk_lock_for(user_id)

    if lock.locked():
        await update.message.reply_text(
            "Already creating a session for you — hang on!"
        )
        return

    async with lock:
        existing = _active_talk.get(user_id)
        if existing:
            sid = existing.get("session_id", "")
            await update.message.reply_text(
                f"You already have an active session ({sid[:12]}…).\n"
                f"Send /endtalk to close it first, then /talk again."
            )
            return

        msg = await update.message.reply_text("Creating realtime avatar session...")
        try:
            session = await asyncio.to_thread(_create_realtime_session)
        except Exception as e:
            await msg.edit_text(f"Could not create session: {e!s}"[:1500])
            return

        session_id = session.get("session_id") or session.get("id") or ""
        if session_id:
            _active_talk[user_id] = {"session_id": session_id}

        viewer_base = os.environ.get("ATLAS_VIEWER_BASE_URL", "").strip().rstrip("/")

        lk_token = session.get("token", "")
        lk_url = session.get("livekit_url", "")
        lk_room = session.get("room", "")

        if viewer_base and lk_token and lk_url:
            from urllib.parse import urlencode
            qs = urlencode({"token": lk_token, "url": lk_url, "room": lk_room})
            viewer_url = f"{viewer_base}/?{qs}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Talk to Avatar",
                    web_app=WebAppInfo(url=viewer_url),
                )],
                [InlineKeyboardButton(
                    text="Open in Browser",
                    url=viewer_url,
                )],
            ])
            await msg.edit_text(
                "Your avatar session is ready!\n\n"
                "Tap the button below to open the live avatar — "
                "you can talk with your mic and see it respond in real time.\n\n"
                "Send /endtalk when you're done (stops billing).",
                reply_markup=keyboard,
            )
        elif viewer_base:
            await msg.edit_text(
                f"Session created but no session_id returned.\n\n"
                f"Raw response:\n{json.dumps(session, indent=2)[:1200]}",
            )
        else:
            if session_id:
                _active_talk.pop(user_id, None)
                try:
                    await asyncio.to_thread(_leave_session, session_id)
                except Exception:
                    pass
            await msg.edit_text(
                "Realtime sessions require a viewer.\n\n"
                "1. Deploy atlas-avatar-viewer (single HTML file):\n"
                "   github.com/NorthModelLabs/atlas-avatar-viewer\n\n"
                "2. Add to your .env:\n"
                "   ATLAS_VIEWER_BASE_URL=https://your-viewer.vercel.app\n\n"
                "3. Restart the bot — /talk will show a \"Talk to Avatar\" "
                "button that works on any device.",
            )


async def _cmd_endtalk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close the user's active realtime session."""
    user_id = update.effective_user.id
    existing = _active_talk.pop(user_id, None)
    if not existing:
        await update.message.reply_text("No active session to close.")
        return
    sid = existing.get("session_id", "")
    msg = await update.message.reply_text(f"Closing session {sid[:12]}…")
    try:
        await asyncio.to_thread(_leave_session, sid)
        await msg.edit_text(f"Session {sid[:12]}… closed. Send /talk to start a new one.")
    except Exception as e:
        await msg.edit_text(f"Tried to close session but got: {e!s}"[:1500])


async def _handle_ask(update: Update, question: str) -> None:
    msg = await update.message.reply_text("Thinking...")
    try:
        answer = await asyncio.to_thread(_llm_spoken_answer, question)
    except Exception as e:
        await msg.edit_text(f"LLM error: {e!s}"[:1500])
        return

    await msg.edit_text("Rendering video...")

    async with _render_lock:
        path, url, err = await asyncio.to_thread(_render_offline_video, answer)
    if err:
        await msg.edit_text(f"Could not render video: {err}")
        return
    if path is not None:
        await msg.delete()
        preview = answer if len(answer) <= 900 else (answer[:897] + "...")
        with open(path, "rb") as f:
            await update.message.reply_video(
                video=f,
                caption=preview,
                supports_streaming=True,
            )
        shutil.rmtree(path.parent, ignore_errors=True)
        return
    if url:
        await msg.edit_text(f"Video too large for Telegram.\nDownload: {url}")
        return
    await msg.edit_text("Render failed — try again.")


async def _handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        return
    await _handle_ask(update, text)


def main() -> int:
    _load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Set TELEGRAM_BOT_TOKEN (BotFather → /newbot → token).", file=sys.stderr)
        return 2
    if not os.environ.get("ATLAS_API_KEY", "").strip():
        print("Set ATLAS_API_KEY.", file=sys.stderr)
        return 2

    viewer = os.environ.get("ATLAS_VIEWER_BASE_URL", "").strip()
    llm = os.environ.get("HELICONE_API_KEY", "").strip() or os.environ.get("ANTHROPIC_API_KEY", "").strip()

    print("telegram_avatar_bot: starting", flush=True)
    print(f"  /ask + text = {'LLM + MP4' if llm else 'NO LLM KEY — /ask will fail; use /generate'}", flush=True)
    print(f"  /generate = verbatim MP4", flush=True)
    print(f"  /talk = {'Web App → ' + viewer if viewer else 'raw LiveKit JSON (set ATLAS_VIEWER_BASE_URL for button)'}", flush=True)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(CommandHandler("help", _cmd_start))
    app.add_handler(CommandHandler("ask", _cmd_ask))
    app.add_handler(CommandHandler("generate", _cmd_generate))
    app.add_handler(CommandHandler("talk", _cmd_talk))
    app.add_handler(CommandHandler("endtalk", _cmd_endtalk))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_text))

    print("telegram_avatar_bot: polling for messages...", flush=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling(drop_pending_updates=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
