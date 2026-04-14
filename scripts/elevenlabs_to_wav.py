#!/usr/bin/env python3
"""ElevenLabs TTS → 16-bit mono 44.1kHz WAV for Atlas /v1/generate (same MP3→WAV path as avatar_discord_narrator).

Usage:
  python3 scripts/elevenlabs_to_wav.py "Spoken line here" /path/out.wav
Loads repo-root .env if present. Needs ELEVENLABS_API_KEY, ffmpeg on PATH.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import requests

_REPO = Path(__file__).resolve().parents[1]


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


def _voice_id() -> str:
    manual = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()
    if manual:
        return manual
    key = os.environ["ELEVENLABS_API_KEY"].strip()
    r = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": key},
        timeout=30,
    )
    if r.ok:
        for v in r.json().get("voices") or []:
            if (v.get("category") or "").lower() == "premade" and v.get("voice_id"):
                return str(v["voice_id"])
    return "21m00Tcm4TlvDq8ikWAM"


def main() -> int:
    _load_dotenv()
    text = (sys.argv[1] if len(sys.argv) > 1 else "Quick Atlas offline speech test.").strip()
    out = Path(sys.argv[2] if len(sys.argv) > 2 else (_REPO / "claude-code-avatar/test-fixtures/speech-eleven.wav")).expanduser()
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        print("Set ELEVENLABS_API_KEY (see .env.example).", file=sys.stderr)
        return 2

    voice = _voice_id()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    r = requests.post(
        url,
        headers={"xi-api-key": key, "Accept": "audio/mpeg", "Content-Type": "application/json"},
        json={"text": text[:2500]},
        params={"output_format": "mp3_44100_128"},
        timeout=120,
    )
    if not r.ok:
        print(r.text[:2000], file=sys.stderr)
        return 3

    tmp = out.parent / (out.stem + ".mp3.tmp")
    tmp.write_bytes(r.content)
    out.parent.mkdir(parents=True, exist_ok=True)
    pr = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(tmp),
            "-ac",
            "1",
            "-ar",
            "44100",
            "-sample_fmt",
            "s16",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    tmp.unlink(missing_ok=True)
    if pr.returncode != 0:
        print(pr.stderr or pr.stdout or "ffmpeg failed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
