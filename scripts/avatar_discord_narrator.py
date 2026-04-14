#!/usr/bin/env python3
"""LLM short script → ElevenLabs TTS → face image from S3 → Atlas /v1/generate → Discord MP4.

Loads repo-root .env if present. Syncs ATLAS_API_BASE from ATLAS_API_URL if needed.

Required env: ATLAS_API_KEY, DISCORD_WEBHOOK_URL, ELEVENLABS_API_KEY.

With Claude script: also ANTHROPIC_API_KEY, LLM_MODEL, AWS_* + AWS_ENDPOINT_URL_S3, and bucket
(AVATARHUB_S3_BUCKET, default avatarhub) unless --use-local-fixture-face.

Optional: HELICONE_API_KEY (Anthropic via anthropic.helicone.ai), ELEVENLABS_VOICE_ID (else first premade from GET /v1/voices, else Rachel id).

Usage:
  python3 scripts/avatar_discord_narrator.py "Topic for Claude to turn into a spoken script"
  python3 scripts/avatar_discord_narrator.py --no-llm --use-local-fixture-face "Speak this text with TTS only (smoke test)"
  python3 scripts/avatar_discord_narrator.py --face-key path/in/bucket.jpg "Another topic"
"""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
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


def _sync_env() -> None:
    """Atlas CLI reads ATLAS_API_BASE; some .env files only set ATLAS_API_URL."""
    if not os.environ.get("ATLAS_API_BASE", "").strip():
        u = os.environ.get("ATLAS_API_URL", "").strip()
        if u:
            os.environ["ATLAS_API_BASE"] = u


def _require(*names: str) -> None:
    missing = [n for n in names if not os.environ.get(n, "").strip()]
    if missing:
        print(f"Missing env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)


def _llm_script(topic: str) -> str:
    _require("ANTHROPIC_API_KEY", "LLM_MODEL")
    key = os.environ["ANTHROPIC_API_KEY"].strip()
    model = os.environ["LLM_MODEL"].strip()
    helicone = os.environ.get("HELICONE_API_KEY", "").strip()
    if helicone:
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
    prompt = (
        "Write a short spoken script (under 120 words) for a talking-head AI avatar. "
        "Plain words only — no stage directions, no bullet points, no markdown. "
        "One or two short paragraphs max. Topic:\n\n"
        f"{topic}"
    )
    body = {
        "model": model,
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(url, headers=headers, json=body, timeout=120)
    if not r.ok:
        print(r.text[:2000], file=sys.stderr)
        sys.exit(3)
    data = r.json()
    parts = data.get("content") or []
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    text = text.strip()
    if not text:
        print("LLM returned empty text.", file=sys.stderr)
        sys.exit(3)
    return text


def _elevenlabs_voice_id() -> str:
    """Resolve voice id: env ELEVENLABS_VOICE_ID, else first premade from API, else Rachel."""
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
    return "21m00Tcm4TlvDq8ikWAM"  # Rachel (public premade id)


def _elevenlabs_tts(text: str, out_path: Path) -> None:
    _require("ELEVENLABS_API_KEY")
    key = os.environ["ELEVENLABS_API_KEY"].strip()
    voice = _elevenlabs_voice_id()
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    r = requests.post(
        url,
        headers={"xi-api-key": key, "Accept": "audio/mpeg", "Content-Type": "application/json"},
        json={"text": text},
        params={"output_format": "mp3_44100_128"},
        timeout=120,
    )
    if not r.ok:
        print(r.text[:2000], file=sys.stderr)
        sys.exit(3)
    out_path.write_bytes(r.content)


def _audio_for_atlas(audio: Path, tmp: Path) -> Path:
    """Atlas /v1/generate lip-sync expects decoded PCM-style audio. Raw MP3 multipart
    is often mis-decoded server-side (sounds like static). Convert MP3 → 16-bit mono WAV."""
    suf = audio.suffix.lower()
    if suf == ".wav":
        return audio
    if suf != ".mp3":
        return audio
    wav = tmp / "speech_for_atlas.wav"
    r = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(audio),
            "-ac",
            "1",
            "-ar",
            "44100",
            "-sample_fmt",
            "s16",
            str(wav),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not wav.is_file():
        err = (r.stderr or r.stdout or "").strip() or "ffmpeg failed"
        print(
            "Could not convert ElevenLabs MP3 to WAV for Atlas (need `ffmpeg` on PATH).\n"
            f"{err}",
            file=sys.stderr,
        )
        sys.exit(2)
    return wav


def _s3_client():
    try:
        import boto3  # type: ignore
    except ImportError:
        print(
            "Install boto3 for S3: pip install -r scripts/requirements-narrator.txt",
            file=sys.stderr,
        )
        sys.exit(2)
    kwargs = {
        "aws_access_key_id": os.environ["AWS_ACCESS_KEY_ID"].strip(),
        "aws_secret_access_key": os.environ["AWS_SECRET_ACCESS_KEY"].strip(),
        "endpoint_url": os.environ.get("AWS_ENDPOINT_URL_S3", "").strip() or None,
    }
    region = os.environ.get("AWS_REGION", "").strip() or os.environ.get("AWS_DEFAULT_REGION", "").strip()
    if region and region.lower() not in ("auto", ""):
        kwargs["region_name"] = region
    return boto3.client("s3", **kwargs)


def _list_face_keys(bucket: str, prefix: str) -> list[str]:
    s3 = _s3_client()
    keys: list[str] = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents") or []:
            k = obj.get("Key") or ""
            low = k.lower()
            if low.endswith((".jpg", ".jpeg", ".png", ".webp")):
                keys.append(k)
    return keys


def _download_face(bucket: str, key: str, dest: Path) -> None:
    s3 = _s3_client()
    s3.download_file(bucket, key, str(dest))


def _atlas_offline(audio: Path, image: Path) -> str:
    _require("ATLAS_API_KEY")
    script = _REPO / "skills" / "atlas-avatar" / "scripts" / "atlas_session.py"
    r = subprocess.run(
        [sys.executable, str(script), "offline", "--audio", str(audio), "--image", str(image)],
        capture_output=True,
        text=True,
        cwd=str(_REPO),
        env=os.environ.copy(),
        timeout=180,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        sys.exit(3)
    data = json.loads(r.stdout.strip())
    job = data.get("job_id") or data.get("id") or ""
    if not job:
        print("No job_id from offline.", file=sys.stderr)
        sys.exit(3)
    return str(job)


def _jobs_wait(job: str) -> None:
    script = _REPO / "skills" / "atlas-avatar" / "scripts" / "atlas_session.py"
    r = subprocess.run(
        [sys.executable, str(script), "jobs-wait", job, "--interval", "3", "--timeout", "600"],
        cwd=str(_REPO),
        env=os.environ.copy(),
        timeout=700,
    )
    if r.returncode != 0:
        sys.exit(3)


def _jobs_result_url(job: str) -> str:
    script = _REPO / "skills" / "atlas-avatar" / "scripts" / "atlas_session.py"
    r = subprocess.run(
        [sys.executable, str(script), "jobs-result", job],
        capture_output=True,
        text=True,
        cwd=str(_REPO),
        env=os.environ.copy(),
        timeout=60,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        sys.exit(3)
    data = json.loads(r.stdout.strip())
    url = (data.get("url") or "").strip()
    if not url:
        print("No url in jobs-result.", file=sys.stderr)
        sys.exit(3)
    return url


def _discord_post(mp4: Path, job_id: str, bridge: str, *, pricing_line: str) -> None:
    _require("DISCORD_WEBHOOK_URL")
    post = _REPO / "skills" / "atlas-bridge-discord" / "scripts" / "post_session.py"
    combined = bridge.rstrip()
    if pricing_line:
        combined = f"{combined}\n\n_{pricing_line}_"
    payload = {
        "session_id": job_id,
        "room": "offline-generate",
        "mode": "offline",
        "bridge_note": combined[:1800],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        jpath = f.name
    try:
        r = subprocess.run(
            [sys.executable, str(post), "-f", jpath, "--video", str(mp4)],
            cwd=str(_REPO),
            env=os.environ.copy(),
            timeout=180,
        )
        if r.returncode != 0:
            sys.exit(3)
    finally:
        Path(jpath).unlink(missing_ok=True)


def main() -> int:
    _load_dotenv()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("topic", help="What the avatar should explain (LLM writes the spoken script)")
    p.add_argument(
        "--face-key",
        default="",
        help="Exact S3 object key for the face image (otherwise pick a random image in the bucket)",
    )
    p.add_argument(
        "--prefix",
        default=os.environ.get("AVATARHUB_S3_PREFIX", "").strip(),
        help="S3 prefix when listing faces (default env AVATARHUB_S3_PREFIX or empty)",
    )
    p.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip Claude: speak the topic text directly with ElevenLabs (no ANTHROPIC_API_KEY)",
    )
    p.add_argument(
        "--use-local-fixture-face",
        action="store_true",
        help="Use claude-code-avatar/test-fixtures/face.jpg instead of S3 (for smoke tests)",
    )
    args = p.parse_args()

    _sync_env()

    bucket = os.environ.get("AVATARHUB_S3_BUCKET", "avatarhub").strip()
    req = [
        "ATLAS_API_KEY",
        "DISCORD_WEBHOOK_URL",
        "ELEVENLABS_API_KEY",
    ]
    if not args.use_local_fixture_face:
        req += ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    if not args.no_llm:
        req += ["ANTHROPIC_API_KEY", "LLM_MODEL"]
    _require(*req)
    if not args.use_local_fixture_face and not os.environ.get("AWS_ENDPOINT_URL_S3", "").strip():
        print("Set AWS_ENDPOINT_URL_S3 for your S3-compatible endpoint.", file=sys.stderr)
        return 2

    topic = args.topic.strip()
    if not topic:
        print("Topic is empty.", file=sys.stderr)
        return 2

    if args.no_llm:
        print("Skipping LLM — using topic as spoken script.", file=sys.stderr)
        script_text = topic[:2500]
    else:
        print("LLM: drafting script…", file=sys.stderr)
        script_text = _llm_script(topic)

    tmp = Path(tempfile.mkdtemp(prefix="atlas-narrator-"))
    try:
        audio = tmp / "speech.mp3"
        mp4 = tmp / "out.mp4"

        print("ElevenLabs: TTS…", file=sys.stderr)
        _elevenlabs_tts(script_text, audio)

        if args.use_local_fixture_face:
            fixture = _REPO / "claude-code-avatar" / "test-fixtures" / "face.jpg"
            if not fixture.is_file():
                print(f"Missing {fixture} — run claude-code-avatar/scripts/make-test-assets.sh", file=sys.stderr)
                return 2
            image = tmp / "face.jpg"
            image.write_bytes(fixture.read_bytes())
            print(f"Using local fixture face {fixture}", file=sys.stderr)
        elif args.face_key.strip():
            key = args.face_key.strip()
            ext = Path(key).suffix.lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp"):
                ext = ".jpg"
            image = tmp / f"face{ext}"
            print(f"S3: downloading s3://{bucket}/{key} …", file=sys.stderr)
            _download_face(bucket, key, image)
        else:
            print(f"S3: listing images in s3://{bucket}/{args.prefix}…", file=sys.stderr)
            keys = _list_face_keys(bucket, args.prefix)
            if not keys:
                print("No .jpg/.jpeg/.png/.webp objects found under that prefix.", file=sys.stderr)
                return 2
            key = random.choice(keys)
            print(f"S3: using face {key!r}", file=sys.stderr)
            ext = Path(key).suffix.lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp"):
                ext = ".jpg"
            image = tmp / f"face{ext}"
            _download_face(bucket, key, image)

        print("Atlas: offline generate…", file=sys.stderr)
        atlas_audio = _audio_for_atlas(audio, tmp)
        job = _atlas_offline(atlas_audio, image)
        print(f"Atlas: job {job} — waiting…", file=sys.stderr)
        _jobs_wait(job)

        url = _jobs_result_url(job)
        print("Downloading MP4…", file=sys.stderr)
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        mp4.write_bytes(r.content)
        n = mp4.stat().st_size
        max_b = 25 * 1024 * 1024
        if n > max_b:
            print(f"MP4 too large for Discord attach ({n} bytes). Post link only — not implemented here.", file=sys.stderr)
            return 3

        bridge = f"**Topic:** {topic}\n\n**Script (excerpt):** {script_text[:500]}{'…' if len(script_text) > 500 else ''}"
        print("Discord: uploading…", file=sys.stderr)
        if args.use_local_fixture_face:
            pline = "Atlas /v1/generate + ElevenLabs TTS + local portrait fixture (test-fixtures/face.jpg)"
        else:
            pline = "Atlas /v1/generate + ElevenLabs TTS + S3 face image"
        _discord_post(mp4, job, bridge, pricing_line=pline)
    finally:
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)

    print(json.dumps({"ok": True, "job_id": job}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
