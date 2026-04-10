"""Shared Atlas API HTTP helpers for atlas_cli.py and skill scripts."""
from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


def eprint(*a: object) -> None:
    print(*a, file=sys.stderr)


def base_url() -> str:
    return os.environ.get("ATLAS_API_BASE", "https://api.atlasv1.com").rstrip("/")


def auth_headers(*, required: bool) -> dict[str, str]:
    if not required:
        return {}
    key = os.environ.get("ATLAS_API_KEY", "").strip()
    if not key:
        eprint("Error: set ATLAS_API_KEY in the environment.")
        sys.exit(2)
    return {"Authorization": f"Bearer {key}"}


def emit_response(r: requests.Response) -> int:
    if not r.ok:
        eprint(f"HTTP {r.status_code}")
    try:
        data = r.json()
        print(json.dumps(data, indent=2))
    except Exception:
        print(r.text or "(empty body)")
    return 0 if r.ok else 3


def api_index() -> requests.Response:
    return requests.get(f"{base_url()}/", timeout=30)


def api_health() -> requests.Response:
    return requests.get(f"{base_url()}/v1/health", timeout=30)


def api_status() -> requests.Response:
    return requests.get(
        f"{base_url()}/v1/status",
        headers={**auth_headers(required=True)},
        timeout=30,
    )


def api_me() -> requests.Response:
    return requests.get(
        f"{base_url()}/v1/me",
        headers={**auth_headers(required=True)},
        timeout=30,
    )


def api_realtime_create(
    mode: str,
    face: str | None,
    face_url: str | None,
) -> requests.Response:
    b = base_url()
    h = auth_headers(required=True)
    if face:
        p = Path(face)
        if not p.is_file():
            eprint(f"Error: face file not found: {p}")
            sys.exit(2)
        mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        with p.open("rb") as fh:
            return requests.post(
                f"{b}/v1/realtime/session",
                headers=h,
                data={"mode": mode},
                files={"face": (p.name, fh, mime)},
                timeout=120,
            )
    body: dict[str, Any] = {"mode": mode}
    if face_url:
        body["face_url"] = face_url
    return requests.post(
        f"{b}/v1/realtime/session",
        headers={**h, "Content-Type": "application/json"},
        json=body,
        timeout=120,
    )


def api_realtime_get(session_id: str) -> requests.Response:
    return requests.get(
        f"{base_url()}/v1/realtime/session/{session_id}",
        headers={**auth_headers(required=True)},
        timeout=30,
    )


def api_realtime_patch(session_id: str, face: str) -> requests.Response:
    p = Path(face)
    if not p.is_file():
        eprint(f"Error: face file not found: {p}")
        sys.exit(2)
    mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
    with p.open("rb") as fh:
        return requests.patch(
            f"{base_url()}/v1/realtime/session/{session_id}",
            headers={**auth_headers(required=True)},
            files={"face": (p.name, fh, mime)},
            timeout=120,
        )


def api_realtime_delete(session_id: str) -> requests.Response:
    return requests.delete(
        f"{base_url()}/v1/realtime/session/{session_id}",
        headers={**auth_headers(required=True)},
        timeout=60,
    )


def api_generate(audio: str, image: str, callback_url: str | None) -> requests.Response:
    ap = Path(audio)
    ip = Path(image)
    if not ap.is_file() or not ip.is_file():
        eprint("Error: --audio and --image must be existing files.")
        sys.exit(2)
    am = mimetypes.guess_type(str(ap))[0] or "application/octet-stream"
    im = mimetypes.guess_type(str(ip))[0] or "application/octet-stream"
    h = {**auth_headers(required=True)}
    if callback_url:
        h["X-Callback-URL"] = callback_url
    with ap.open("rb") as af, ip.open("rb") as imf:
        return requests.post(
            f"{base_url()}/v1/generate",
            headers=h,
            files={
                "audio": (ap.name, af, am),
                "image": (ip.name, imf, im),
            },
            timeout=120,
        )


def api_jobs_list(limit: int | None, offset: int | None) -> requests.Response:
    params: dict[str, int] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return requests.get(
        f"{base_url()}/v1/jobs",
        headers={**auth_headers(required=True)},
        params=params or None,
        timeout=30,
    )


def api_jobs_get(job_id: str) -> requests.Response:
    return requests.get(
        f"{base_url()}/v1/jobs/{job_id}",
        headers={**auth_headers(required=True)},
        timeout=30,
    )


def api_jobs_result(job_id: str) -> requests.Response:
    return requests.get(
        f"{base_url()}/v1/jobs/{job_id}/result",
        headers={**auth_headers(required=True)},
        timeout=30,
    )


def api_jobs_wait(job_id: str, interval: float, timeout_sec: int) -> int:
    deadline = time.time() + timeout_sec
    h = auth_headers(required=True)
    b = base_url()
    while time.time() < deadline:
        r = requests.get(f"{b}/v1/jobs/{job_id}", headers=h, timeout=30)
        try:
            data = r.json()
        except Exception:
            eprint(r.text)
            return 3
        status = data.get("status")
        print(json.dumps(data, indent=2))
        if status in ("completed", "failed"):
            return 0 if status == "completed" else 3
        time.sleep(interval)
    eprint("Error: timeout waiting for job terminal state.")
    return 3


def api_avatar_session(
    livekit_url: str,
    livekit_token: str,
    room_name: str,
    avatar_image: str | None,
) -> requests.Response:
    h = auth_headers(required=True)
    data = {
        "livekit_url": livekit_url,
        "livekit_token": livekit_token,
        "room_name": room_name,
    }
    if avatar_image:
        p = Path(avatar_image)
        if not p.is_file():
            eprint(f"Error: avatar_image not found: {p}")
            sys.exit(2)
        mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
        with p.open("rb") as fh:
            return requests.post(
                f"{base_url()}/v1/avatar/session",
                headers=h,
                data=data,
                files={"avatar_image": (p.name, fh, mime)},
                timeout=120,
            )
    return requests.post(
        f"{base_url()}/v1/avatar/session",
        headers=h,
        data=data,
        timeout=120,
    )
