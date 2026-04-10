#!/usr/bin/env python3
"""Atlas API — unified CLI (uses atlas_api.py). Server version: GET / → version.

Uses ATLAS_API_KEY and optional ATLAS_API_BASE (default https://api.atlasv1.com).

Exit codes: 0 ok, 2 validation/config, 3 HTTP error from API.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

import atlas_api as api


def cmd_index(_: argparse.Namespace) -> int:
    return api.emit_response(api.api_index())


def cmd_health(_: argparse.Namespace) -> int:
    return api.emit_response(api.api_health())


def cmd_status(_: argparse.Namespace) -> int:
    return api.emit_response(api.api_status())


def cmd_me(_: argparse.Namespace) -> int:
    return api.emit_response(api.api_me())


def cmd_realtime_create(args: argparse.Namespace) -> int:
    mode = args.mode or "conversation"
    face = args.face or None
    face_url = args.face_url or None
    return api.emit_response(api.api_realtime_create(mode, face, face_url))


def cmd_realtime_get(args: argparse.Namespace) -> int:
    return api.emit_response(api.api_realtime_get(args.session_id))


def cmd_realtime_patch(args: argparse.Namespace) -> int:
    return api.emit_response(api.api_realtime_patch(args.session_id, args.face))


def cmd_realtime_delete(args: argparse.Namespace) -> int:
    return api.emit_response(api.api_realtime_delete(args.session_id))


def cmd_generate(args: argparse.Namespace) -> int:
    cb = args.callback_url or None
    return api.emit_response(api.api_generate(args.audio, args.image, cb))


def cmd_jobs_list(args: argparse.Namespace) -> int:
    return api.emit_response(api.api_jobs_list(args.limit, args.offset))


def cmd_jobs_get(args: argparse.Namespace) -> int:
    return api.emit_response(api.api_jobs_get(args.job_id))


def cmd_jobs_result(args: argparse.Namespace) -> int:
    return api.emit_response(api.api_jobs_result(args.job_id))


def cmd_jobs_wait(args: argparse.Namespace) -> int:
    return api.api_jobs_wait(args.job_id, args.interval, args.timeout)


def cmd_avatar_session(args: argparse.Namespace) -> int:
    img = args.avatar_image or None
    return api.emit_response(
        api.api_avatar_session(
            args.livekit_url,
            args.livekit_token,
            args.room_name,
            img,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Atlas API CLI — use ATLAS_API_KEY and optional ATLAS_API_BASE.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", help="GET / (API index, no auth)").set_defaults(fn=cmd_index)
    sub.add_parser("health", help="GET /v1/health (no auth)").set_defaults(fn=cmd_health)
    sub.add_parser("status", help="GET /v1/status").set_defaults(fn=cmd_status)
    sub.add_parser("me", help="GET /v1/me").set_defaults(fn=cmd_me)

    rt = sub.add_parser("realtime", help="Realtime LiveKit sessions")
    rts = rt.add_subparsers(dest="rtc", required=True)

    c = rts.add_parser("create", help="POST /v1/realtime/session")
    c.add_argument("--mode", choices=("conversation", "passthrough"), default="conversation")
    c.add_argument("--face-url", dest="face_url", default="", help="HTTPS URL (JSON body)")
    c.add_argument("--face", default="", help="Local image file (multipart)")
    c.set_defaults(fn=cmd_realtime_create)

    g = rts.add_parser("get", help="GET /v1/realtime/session/{id}")
    g.add_argument("session_id")
    g.set_defaults(fn=cmd_realtime_get)

    pa = rts.add_parser("patch", help="PATCH face swap — multipart face file")
    pa.add_argument("session_id")
    pa.add_argument("--face", required=True)
    pa.set_defaults(fn=cmd_realtime_patch)

    d = rts.add_parser("delete", help="DELETE /v1/realtime/session/{id}")
    d.add_argument("session_id")
    d.set_defaults(fn=cmd_realtime_delete)

    gen = sub.add_parser("generate", help="POST /v1/generate (offline video job)")
    gen.add_argument("--audio", required=True)
    gen.add_argument("--image", required=True)
    gen.add_argument("--callback-url", default="", help="X-Callback-URL header (HTTPS)")
    gen.set_defaults(fn=cmd_generate)

    jobs = sub.add_parser("jobs", help="Job queue")
    js = jobs.add_subparsers(dest="jobcmd", required=True)

    jl = js.add_parser("list", help="GET /v1/jobs")
    jl.add_argument("--limit", type=int, default=None)
    jl.add_argument("--offset", type=int, default=None)
    jl.set_defaults(fn=cmd_jobs_list)

    jg = js.add_parser("get", help="GET /v1/jobs/{id}")
    jg.add_argument("job_id")
    jg.set_defaults(fn=cmd_jobs_get)

    jr = js.add_parser("result", help="GET /v1/jobs/{id}/result")
    jr.add_argument("job_id")
    jr.set_defaults(fn=cmd_jobs_result)

    jw = js.add_parser("wait", help="Poll GET /v1/jobs/{id} until completed or failed")
    jw.add_argument("job_id")
    jw.add_argument("--interval", type=float, default=2.0)
    jw.add_argument("--timeout", type=int, default=600)
    jw.set_defaults(fn=cmd_jobs_wait)

    av = sub.add_parser("avatar-session", help="POST /v1/avatar/session (BYO LiveKit)")
    av.add_argument("--livekit-url", required=True)
    av.add_argument("--livekit-token", required=True)
    av.add_argument("--room-name", required=True)
    av.add_argument("--avatar-image", default="", help="Optional face image file")
    av.set_defaults(fn=cmd_avatar_session)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    fn = getattr(args, "fn", None)
    if fn is None:
        parser.print_help()
        sys.exit(2)
    sys.exit(fn(args))


if __name__ == "__main__":
    main()
