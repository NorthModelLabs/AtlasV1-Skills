#!/usr/bin/env python3
"""Discord **bot** (not webhook): slash commands, **reply-to-bot** thread, optional @mentions → MP4.

- **``/ask``** — **Claude** answers; the **video** lip-syncs that **answer**. Default path: **Helicone AI Gateway**
  with ``HELICONE_API_KEY`` only (``https://ai-gateway.helicone.ai`` OpenAI-compatible chat). Optional
  ``ANTHROPIC_API_KEY`` for **direct** ``api.anthropic.com`` when Helicone is unset. Legacy proxy
  ``anthropic.helicone.ai`` + BYOK: set ``HELICONE_ANTHROPIC_PROXY=1`` with **both** keys.
  ``LLM_MODEL`` defaults to ``claude-sonnet-4`` (gateway) or ``claude-sonnet-4-20250514`` (native Anthropic).
- **Reply to any of the bot's messages** with text — same LLM + lip-sync as ``/ask``, but the model sees
  your **previous bot message** as context (thread-style, like replying in Grok).
- **``/generate``** — lip-sync **exactly** the ``script`` you type (verbatim).
- **``/talk``** — start a **realtime** avatar session and get a viewer link (mic + video, LiveKit).
- **``/endtalk``** — close your active realtime session (stops billing).
- **@mention** — same as **``/ask``**: natural **Claude** reply + **Answer:** + MP4 (text after the mention is the prompt).

**Message Content** intent must be on in the Portal and ``DISCORD_MESSAGE_CONTENT_INTENT=1`` for any
**normal message** handling (replies and @mentions). Slash commands work without it.

**``DISCORD_GUILD_ID``** (numeric server id) — if set, ``/ask`` and ``/generate`` register **only** in that
guild and sync in seconds (avoids Discord’s “command outdated” / global propagation delay). Omit for
global commands (all servers, slower to update).

Run from repo root with a venv that has ``discord.py`` + ``requests`` (see skill ``requirements.txt``).

Env
---
**Required:** ``DISCORD_BOT_TOKEN``, ``ATLAS_API_KEY``

**For ``/ask``:** ``HELICONE_API_KEY`` (default gateway) **or** ``ANTHROPIC_API_KEY`` (direct); ``LLM_MODEL``

**Optional:** ``HELICONE_ANTHROPIC_PROXY=1`` with both keys for legacy Helicone Anthropic proxy. ``ELEVENLABS_API_KEY``
(+ ``ELEVENLABS_VOICE_ID``) for speech; else test tone WAV.
``ATLAS_OFFLINE_IMAGE`` — face image (default: claude-code-avatar test fixture).
``ATLAS_VIEWER_BASE_URL`` — deployed viewer (e.g. ``https://atlas-avatar-viewer.vercel.app``) for ``/talk`` button.
``DISCORD_MESSAGE_CONTENT_INTENT=1`` — request **Message Content** intent for @mention text; must also
be enabled in the Developer Portal (Bot → Privileged Gateway Intents). Omit if you only use slash commands.
``DISCORD_AVATAR_DEBUG=1`` — log reply-to-bot / reference resolution to stderr (no message bodies).
``DISCORD_GUILD_MEMBERS_INTENT=1`` — optional **Server Members** intent (must match Portal); can help @mentions in large servers.

Discord Developer Portal
------------------------
Create an application → Bot → copy token. Invite with **Send Messages**, **Attach Files**,
**Read Message History**, **Use Slash Commands**.

Usage::

  cd /path/to/repo && pip install -r skills/atlas-bridge-discord/requirements.txt
  python3 skills/atlas-bridge-discord/scripts/discord_avatar_bot.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import discord
import requests
from discord import app_commands
from discord.ext import commands

_MAX_SCRIPT_CHARS = 1800
_MAX_DISCORD_BYTES = 25 * 1024 * 1024
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


def _render_offline_video(script: str) -> tuple[Path | None, str | None, str | None]:
    """Return (mp4_path_or_none_if_too_large, presigned_url, error_message)."""
    script = script.strip()[:_MAX_SCRIPT_CHARS]
    if not script:
        return None, None, "Empty question."

    work = Path(tempfile.mkdtemp(prefix="discord-avatar-bot-"))
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
        n = mp4.stat().st_size
        if n > _MAX_DISCORD_BYTES:
            shutil.rmtree(work, ignore_errors=True)
            return None, url, None
        return mp4, url, None
    except Exception as e:
        shutil.rmtree(work, ignore_errors=True)
        return None, None, str(e)[:1500]


_render_lock = asyncio.Lock()

# Per-user active realtime session: user_id → {"session_id": ...}
_active_talk: dict[int, dict[str, Any]] = {}
_talk_locks: dict[int, asyncio.Lock] = {}


def _talk_lock_for(user_id: int) -> asyncio.Lock:
    if user_id not in _talk_locks:
        _talk_locks[user_id] = asyncio.Lock()
    return _talk_locks[user_id]


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


def _strip_mentions(content: str) -> str:
    return re.sub(r"<@!?\d+>", "", content).strip()


def _content_mentions_user(content: str | None, user_id: int) -> bool:
    """True if message text includes a user mention for ``user_id``.

    Discord sometimes leaves ``message.mentions`` empty (e.g. some channel types / payloads) while
    ``content`` still contains ``<@id>`` / ``<@!id>`` — then ``bot.user in message.mentions`` is false
    and the bot would ignore the line unless we check here.
    """
    if not content:
        return False
    sid = str(user_id)
    return f"<@{sid}>" in content or f"<@!{sid}>" in content


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _debug_avatar(msg: str) -> None:
    if _truthy_env("DISCORD_AVATAR_DEBUG"):
        print(msg, file=sys.stderr, flush=True)


async def _fetch_referenced_message(message: discord.Message) -> discord.Message | None:
    """Load the message the user replied to (correct channel when ref.channel_id != current channel)."""
    ref = message.reference
    if not ref or not ref.message_id:
        return None
    resolved = ref.resolved
    if isinstance(resolved, discord.Message):
        return resolved

    ref_cid = ref.channel_id
    ch: discord.abc.Messageable = message.channel
    if message.channel.id != ref_cid:
        resolved_ch: discord.abc.GuildChannel | discord.Thread | None = None
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id == ref_cid:
            resolved_ch = message.channel.parent
        elif message.guild is not None:
            raw = message.guild.get_channel(ref_cid)
            if raw is not None and hasattr(raw, "fetch_message"):
                resolved_ch = raw  # type: ignore[assignment]
        if resolved_ch is not None:
            ch = resolved_ch  # type: ignore[assignment]

    try:
        return await ch.fetch_message(ref.message_id)  # type: ignore[union-attr]
    except (discord.NotFound, discord.HTTPException) as e:
        print(
            f"discord_avatar_bot: could not load replied-to message "
            f"(fetch_ch={getattr(ch, 'id', None)} ref_ch={ref_cid} ref_msg={ref.message_id}): {e!s}"[:500],
            file=sys.stderr,
            flush=True,
        )
        return None


def _helicone_gateway_completion(prompt: str) -> str:
    """Helicone AI Gateway: OpenAI-compatible chat; only HELICONE_API_KEY required."""
    key = os.environ.get("HELICONE_API_KEY", "").strip()
    model = os.environ.get("LLM_MODEL", "").strip() or "claude-sonnet-4"
    url = "https://ai-gateway.helicone.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "max_tokens": 600,
        "temperature": 0.7,
        "user": f"discord-avatar-{uuid.uuid4()}",
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
    """Anthropic Messages API (direct or legacy anthropic.helicone.ai + Helicone-Auth)."""
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
    """Route: Helicone gateway (default if HELICONE_API_KEY), else Anthropic native; legacy proxy is opt-in."""
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
        "Set HELICONE_API_KEY for /ask (Helicone AI Gateway — default), or ANTHROPIC_API_KEY for direct "
        "Anthropic. Use HELICONE_ANTHROPIC_PROXY=1 with both keys for the legacy anthropic.helicone.ai proxy. "
        "/generate needs no LLM."
    )


def _llm_spoken_answer(question: str) -> str:
    """Turn a user question into short plain text for TTS / lip-sync."""
    q = question.strip()[:4000]
    prompt = (
        "The user asked a question. Write a SHORT spoken answer (under 120 words) for a talking-head "
        "AI avatar to lip-sync. Plain words only — no bullet points, no markdown, no stage directions, "
        "no preamble like 'Here is the answer'. Only the words the avatar should speak.\n\n"
        f"Question:\n{q}"
    )
    return _anthropic_completion(prompt)


def _llm_spoken_followup(parent_bot_message: str, user_message: str) -> str:
    """User replied to the bot's message — continue the thread in spoken form."""
    parent = (parent_bot_message or "").strip()[:2500]
    user = user_message.strip()[:2000]
    prompt = (
        "You are a talking-head AI avatar on Discord. The user replied to your previous message.\n\n"
        "Your previous message (text only; they may also see a video you sent) was:\n"
        f"{parent or '(no text in that message)'}\n\n"
        "The user's new message is:\n"
        f"{user}\n\n"
        "Write a SHORT spoken reply (under 120 words) for the avatar to lip-sync. "
        "You MUST answer what they just said in the user's new message above — do not repeat, "
        "rephrase, or continue your previous answer unless they explicitly ask for that. "
        "Be direct and conversational. Plain words only — no markdown, no bullet lists, no stage directions, "
        "no phrases like 'As an AI model'. Only the words the avatar should speak."
    )
    return _anthropic_completion(prompt)


async def _do_reply(
    *,
    send: Any,
    script: str,
    content_with_file: str | None = None,
) -> None:
    """Send MP4; ``content_with_file`` is the Discord message body (text + attachment)."""
    async with _render_lock:
        path, url, err = await asyncio.to_thread(_render_offline_video, script)
    if err:
        await send(content=f"Could not render: {err}")
        return
    if path is not None:
        body = (content_with_file or "Here is a lip-sync clip.").strip() or "Here is a lip-sync clip."
        await send(content=body[:1900], file=discord.File(path))
        shutil.rmtree(path.parent, ignore_errors=True)
        return
    if url:
        base = content_with_file or "Clip is larger than Discord's upload limit (~25 MB)."
        await send(content=(base + f"\n\nDownload: {url}")[:1900])
        return
    await send(content="Unknown render error.")


def main() -> int:
    _load_dotenv()
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print("Set DISCORD_BOT_TOKEN (Discord application → Bot → token).", file=sys.stderr)
        return 2
    if not os.environ.get("ATLAS_API_KEY", "").strip():
        print("Set ATLAS_API_KEY.", file=sys.stderr)
        return 2

    intents = discord.Intents.default()
    intents.guilds = True
    intents.guild_messages = True
    # Server Members is privileged; optional — helps @mention resolution in large guilds / member lists.
    if _truthy_env("DISCORD_GUILD_MEMBERS_INTENT"):
        intents.members = True
    # Message Content is privileged; Portal must enable it or login fails. Opt-in for @mentions.
    mc = os.environ.get("DISCORD_MESSAGE_CONTENT_INTENT", "").strip().lower()
    intents.message_content = mc in ("1", "true", "yes", "on")

    if not intents.message_content:
        print(
            "DISCORD_MESSAGE_CONTENT_INTENT not enabled: reply-to-bot and @mention disabled; "
            "use /ask or /generate. Set DISCORD_MESSAGE_CONTENT_INTENT=1 + Portal toggle for those.",
            flush=True,
        )

    bot = commands.Bot(command_prefix="\ufffe", intents=intents, help_command=None)

    # Guild-scoped slash = instant updates (avoids "This command is outdated" from global lag).
    guild_raw = os.environ.get("DISCORD_GUILD_ID", "").strip()
    guild_sync: discord.Object | None = None
    if guild_raw.isdigit():
        guild_sync = discord.Object(id=int(guild_raw))
    _guild_decorator = (
        app_commands.guilds(guild_sync) if guild_sync is not None else (lambda fn: fn)
    )

    @bot.tree.command(
        name="ask",
        description="LLM answers your question; avatar lip-syncs the answer (not your raw text).",
    )
    @app_commands.describe(question="Question for the model (video speaks the answer).")
    @_guild_decorator
    async def ask_cmd(interaction: discord.Interaction, question: str) -> None:
        if not question.strip():
            await interaction.response.send_message("Please enter a non-empty question.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)

        async def send(**kwargs: Any) -> None:
            await interaction.followup.send(**kwargs)

        try:
            answer = await asyncio.to_thread(_llm_spoken_answer, question)
        except Exception as e:
            await send(content=f"{e!s}"[:1900])
            return
        preview = answer if len(answer) <= 1700 else (answer[:1697] + "…")
        caption = f"**Answer:**\n{preview}"
        try:
            await _do_reply(send=send, script=answer, content_with_file=caption)
        except discord.HTTPException as e:
            await send(content=f"Discord error: {e}")
        except Exception as e:
            await send(content=f"Error: {e!s}"[:1900])

    @bot.tree.command(
        name="generate",
        description="Lip-sync video: avatar speaks this script exactly (verbatim).",
    )
    @app_commands.describe(script="Exact words for the avatar to speak.")
    @_guild_decorator
    async def generate_cmd(interaction: discord.Interaction, script: str) -> None:
        if not script.strip():
            await interaction.response.send_message("Please enter a non-empty script.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)

        async def send(**kwargs: Any) -> None:
            await interaction.followup.send(**kwargs)

        try:
            await _do_reply(
                send=send,
                script=script,
                content_with_file="Here is a lip-sync clip (verbatim script).",
            )
        except discord.HTTPException as e:
            await send(content=f"Discord error: {e}")
        except Exception as e:
            await send(content=f"Error: {e!s}"[:1900])

    @bot.tree.command(
        name="talk",
        description="Start a realtime avatar session — talk to the avatar live with your mic.",
    )
    @_guild_decorator
    async def talk_cmd(interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        lock = _talk_lock_for(user_id)

        if lock.locked():
            await interaction.response.send_message(
                "Already creating a session for you — hang on!", ephemeral=True,
            )
            return

        async with lock:
            existing = _active_talk.get(user_id)
            if existing:
                sid = existing.get("session_id", "")[:12]
                await interaction.response.send_message(
                    f"You already have an active session ({sid}…).\n"
                    f"Use `/endtalk` to close it first, then `/talk` again.",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(thinking=True)
            try:
                session = await asyncio.to_thread(_create_realtime_session)
            except Exception as e:
                await interaction.followup.send(content=f"Could not create session: {e!s}"[:1900])
                return

            session_id = session.get("session_id") or session.get("id") or ""
            if session_id:
                _active_talk[user_id] = {"session_id": session_id}

            lk_token = session.get("token", "")
            lk_url = session.get("livekit_url", "")
            lk_room = session.get("room", "")
            viewer_base = os.environ.get("ATLAS_VIEWER_BASE_URL", "").strip().rstrip("/")

            if viewer_base and lk_token and lk_url:
                from urllib.parse import urlencode
                qs = urlencode({"token": lk_token, "url": lk_url, "room": lk_room})
                viewer_url = f"{viewer_base}/?{qs}"
                await interaction.followup.send(
                    content=(
                        "**Your avatar session is ready!**\n\n"
                        f"[Talk to Avatar]({viewer_url})\n\n"
                        "Click the link to open the viewer — you can talk with your mic "
                        "and see the avatar respond in real time.\n\n"
                        "Use `/endtalk` when you're done (stops billing)."
                    ),
                )
            else:
                if session_id:
                    _active_talk.pop(user_id, None)
                    try:
                        await asyncio.to_thread(_leave_session, session_id)
                    except Exception:
                        pass
                await interaction.followup.send(
                    content=(
                        "Realtime sessions require a viewer.\n\n"
                        "1. Deploy [atlas-avatar-viewer]"
                        "(https://github.com/NorthModelLabs/atlas-avatar-viewer)\n"
                        "2. Set `ATLAS_VIEWER_BASE_URL` in your `.env`\n"
                        "3. Restart the bot and try `/talk` again"
                    ),
                )

    @bot.tree.command(
        name="endtalk",
        description="Close your active realtime avatar session (stops billing).",
    )
    @_guild_decorator
    async def endtalk_cmd(interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        existing = _active_talk.pop(user_id, None)
        if not existing:
            await interaction.response.send_message("No active session to close.", ephemeral=True)
            return
        sid = existing.get("session_id", "")
        await interaction.response.defer(thinking=True)
        try:
            await asyncio.to_thread(_leave_session, sid)
            await interaction.followup.send(
                content=f"Session {sid[:12]}… closed. Use `/talk` to start a new one.",
            )
        except Exception as e:
            await interaction.followup.send(content=f"Tried to close session: {e!s}"[:1900])

    @bot.event
    async def on_message(message: discord.Message) -> None:
        # Log before message_content early-return so we can see if MESSAGE_CREATE reaches this process.
        if message.guild and not message.author.bot:
            _debug_avatar(
                f"discord_avatar_bot: raw_msg ch={message.channel.id} "
                f"mc_intent={intents.message_content} "
                f"ref={bool(message.reference and message.reference.message_id)} "
                f"content_len={len(message.content or '')}"
            )
        if not intents.message_content:
            return
        if message.author.bot:
            return

        try:
            # --- User replied to the bot's message → LLM sees prior turn + lip-sync answer ---
            parent: discord.Message | None = None
            if message.reference and message.reference.message_id:
                parent = await _fetch_referenced_message(message)
                pa_id = parent.author.id if parent and parent.author else None
                _debug_avatar(
                    f"discord_avatar_bot: on_message ref=1 parent={'set' if parent else 'none'} "
                    f"parent_author={pa_id} bot_id={bot.user.id if bot.user else None} "
                    f"this_ch={message.channel.id} ref_ch={message.reference.channel_id}"
                )
            if (
                parent is not None
                and bot.user is not None
                and parent.author.id == bot.user.id
            ):
                # Prefer raw content; fall back to clean_content if the gateway delivered empty content.
                user_line = (message.content or message.clean_content or "").strip()
                _debug_avatar(f"discord_avatar_bot: reply user_line_len={len(user_line)}")
                if not user_line:
                    await message.reply(
                        "Reply with some text and I’ll answer + send a lip-sync clip. "
                        "(`/ask` works the same without replying.)",
                        mention_author=False,
                    )
                    return
                _debug_avatar("discord_avatar_bot: reply-to-bot → LLM + render")
                async with message.channel.typing():
                    ctx = parent.clean_content or "(no text in that message)"
                    try:
                        answer = await asyncio.to_thread(_llm_spoken_followup, ctx, user_line)
                    except Exception as e:
                        await message.reply(content=str(e)[:1900], mention_author=False)
                        return
                    preview = answer if len(answer) <= 1700 else (answer[:1697] + "…")
                    caption = f"**Answer:**\n{preview}"
                    try:

                        async def send(**kwargs: Any) -> None:
                            await message.reply(**kwargs, mention_author=False)

                        await _do_reply(send=send, script=answer, content_with_file=caption)
                    except Exception as e:
                        await message.reply(content=f"Error: {e!s}"[:1900], mention_author=False)
                return

            # --- @mention: same LLM + Answer + MP4 as /ask (not verbatim /generate) ---
            if not message.guild or bot.user is None:
                return
            uid = bot.user.id
            in_array = bot.user in message.mentions
            in_content = _content_mentions_user(message.content, uid)
            if not (in_array or in_content):
                return
            if not in_array and in_content:
                _debug_avatar("discord_avatar_bot: mention detected from content (message.mentions empty)")
            text = _strip_mentions(message.content)
            if not text:
                await message.reply(
                    "Mention me with something to say to the avatar, e.g. `@bob how are you?` "
                    "— I’ll answer in character and lip-sync that answer (same as `/ask`). "
                    "For **verbatim** script on the avatar, use `/generate`. "
                    "Or **reply** to one of my messages to continue with context.",
                    mention_author=False,
                )
                return
            async with message.channel.typing():

                async def send(**kwargs: Any) -> None:
                    await message.reply(**kwargs, mention_author=False)

                try:
                    answer = await asyncio.to_thread(_llm_spoken_answer, text)
                except Exception as e:
                    await message.reply(content=str(e)[:1900], mention_author=False)
                    return
                preview = answer if len(answer) <= 1700 else (answer[:1697] + "…")
                caption = f"**Answer:**\n{preview}"
                try:
                    await _do_reply(send=send, script=answer, content_with_file=caption)
                except Exception as e:
                    await message.reply(content=f"Error: {e!s}"[:1900], mention_author=False)
        finally:
            await bot.process_commands(message)

    @bot.event
    async def on_ready() -> None:
        assert bot.user is not None
        viewer = os.environ.get("ATLAS_VIEWER_BASE_URL", "").strip()
        print(
            "discord_avatar_bot: /ask=Claude + MP4; /generate=verbatim; "
            f"/talk={'viewer → ' + viewer if viewer else 'NO ATLAS_VIEWER_BASE_URL'}; "
            "@mention=same as /ask; reply-to-bot=LLM+MP4.",
            flush=True,
        )
        print(f"Logged in as {bot.user} (id={bot.user.id})", flush=True)
        names = [f"{g.name!s} (id={g.id})" for g in bot.guilds[:12]]
        tail = f" …+{len(bot.guilds) - 12} more" if len(bot.guilds) > 12 else ""
        print(
            f"discord_avatar_bot: in {len(bot.guilds)} server(s){tail}: "
            f"{'; '.join(names) if names else 'NONE — bot is in no servers; invite/re-add the app.'}",
            file=sys.stderr,
            flush=True,
        )
        try:
            if guild_sync is not None:
                synced = await bot.tree.sync(guild=guild_sync)
                print(
                    f"Slash commands synced to guild {guild_raw}: {[c.name for c in synced]}",
                    flush=True,
                )
            else:
                synced = await bot.tree.sync()
                print(f"Slash commands synced (global): {[c.name for c in synced]}", flush=True)
        except Exception as e:
            print(f"Command sync failed: {e}", file=sys.stderr, flush=True)

    try:
        bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        print(
            "Discord login failed: a privileged intent is on in .env but not enabled in the Portal.\n"
            "  → https://discord.com/developers/applications → your app → Bot → "
            "Privileged Gateway Intents:\n"
            "  • **Message Content** — if DISCORD_MESSAGE_CONTENT_INTENT=1\n"
            "  • **Server Members** — if DISCORD_GUILD_MEMBERS_INTENT=1\n"
            "  Or remove those lines from .env to match what the Portal allows.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
