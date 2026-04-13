#!/usr/bin/env python3
"""Orchestrate Atlas realtime session + Google Meet assist (checklist / open / paste).

This does NOT join Meet as a bot. It runs monorepo scripts:
  skills/atlas-avatar/scripts/atlas_session.py
  skills/atlas-bridge-google-meet/scripts/meet_assist.py

Repo root: ATLAS_AGENT_REPO, or auto-detect from this file's location inside the clone.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _meet_chat_reminder() -> None:
    print(
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  This text is ONLY in your terminal — Google Meet never sees it\n"
        "  until YOU paste it: click Meet chat → paste (⌘V / Ctrl+V).\n"
        "  Meet “join / accept” invites are for people in Meet, not Atlas.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        file=sys.stderr,
    )


def _maybe_copy_pasteboard(text: str) -> None:
    if sys.platform != "darwin":
        print(
            "Tip: use --copy on macOS to put the block on the clipboard; "
            "else copy the text above manually.",
            file=sys.stderr,
        )
        return
    try:
        subprocess.run(["pbcopy"], input=text, text=True, check=True, timeout=5)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Could not copy to clipboard: {e}", file=sys.stderr)
        return
    print("Copied to clipboard — open Meet chat and press ⌘V.", file=sys.stderr)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def repo_root() -> Path:
    env = os.environ.get("ATLAS_AGENT_REPO", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if _is_repo(p):
            return p
        _die(f"ATLAS_AGENT_REPO is set but is not the monorepo root (missing atlas_session): {p}")
    here = Path(__file__).resolve().parent
    for d in (here, *here.parents):
        if _is_repo(d):
            return d
    _die(
        "Could not find monorepo root (expected skills/atlas-avatar/scripts/atlas_session.py). "
        "Clone the full repo or set ATLAS_AGENT_REPO."
    )


def _is_repo(d: Path) -> bool:
    return (d / "skills" / "atlas-avatar" / "scripts" / "atlas_session.py").is_file()


def _py() -> str:
    return sys.executable


def paths(root: Path) -> tuple[Path, Path]:
    atlas = root / "skills" / "atlas-avatar" / "scripts" / "atlas_session.py"
    assist = root / "skills" / "atlas-bridge-google-meet" / "scripts" / "meet_assist.py"
    if not atlas.is_file() or not assist.is_file():
        _die(f"Missing scripts under {root}")
    return atlas, assist


def run_checklist(root: Path, meet_url: str) -> int:
    _, assist = paths(root)
    return subprocess.call([_py(), str(assist), "checklist", "--meet-url", meet_url])


def run_open_meet(root: Path, meet_url: str) -> int:
    _, assist = paths(root)
    return subprocess.call([_py(), str(assist), "open-meet", "--meet-url", meet_url])


def run_paste(
    root: Path,
    meet_url: str,
    session_file: Path,
    viewer_url: str,
    *,
    copy: bool = False,
) -> int:
    _, assist = paths(root)
    cmd = [_py(), str(assist), "paste-message", "--meet-url", meet_url, "-f", str(session_file)]
    if viewer_url.strip():
        cmd += ["--viewer-url", viewer_url.strip()]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        if r.stderr:
            print(r.stderr, end="", file=sys.stderr)
        return r.returncode
    block = (r.stdout or "").rstrip() + "\n"
    if block.strip():
        sys.stdout.write(block)
    _meet_chat_reminder()
    if copy and block.strip():
        _maybe_copy_pasteboard(block)
    return 0


def run_session_start(
    root: Path,
    mode: str,
    face: str,
    face_url: str,
    output: Path,
) -> int:
    atlas, _ = paths(root)
    cmd = [_py(), str(atlas), "start", "--mode", mode]
    if face_url.strip():
        cmd += ["--face-url", face_url.strip()]
    if face.strip():
        cmd += ["--face", face.strip()]
    env = os.environ.copy()
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        if r.stderr:
            print(r.stderr, end="", file=sys.stderr)
        if r.stdout:
            print(r.stdout, end="", file=sys.stderr)
        return r.returncode
    raw = r.stdout.strip()
    if not raw:
        _die("atlas_session start produced empty stdout")
    try:
        json.loads(raw)
    except json.JSONDecodeError as e:
        _die(f"atlas_session start did not return JSON: {e}\n{raw[:500]}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(raw + "\n", encoding="utf-8")
    print(f"Wrote {output}", file=sys.stderr)
    return 0


def cmd_up(args: argparse.Namespace) -> int:
    root = repo_root()
    if args.open_meet:
        run_open_meet(root, args.meet_url)
    rc = run_session_start(root, args.mode, args.face or "", args.face_url or "", Path(args.output))
    if rc != 0:
        return rc
    return run_paste(
        root,
        args.meet_url,
        Path(args.output),
        args.viewer_url or "",
        copy=bool(getattr(args, "copy", False)),
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    u = sub.add_parser(
        "up",
        help="Atlas session start → write JSON → Meet paste-message (optional --open-meet)",
    )
    u.add_argument("--meet-url", required=True)
    u.add_argument("--output", "-o", default="session.json", help="Where to write realtime JSON")
    u.add_argument("--mode", choices=("conversation", "passthrough"), default="conversation")
    u.add_argument("--face", default="", help="Local face image path")
    u.add_argument("--face-url", default="", dest="face_url", help="HTTPS face URL")
    u.add_argument("--viewer-url", default="", help="HTTPS viewer link for Meet chat paste")
    u.add_argument(
        "--open-meet",
        action="store_true",
        help="Open Meet in default browser before starting Atlas session",
    )
    u.add_argument(
        "--copy",
        action="store_true",
        help="macOS: copy Meet chat block to clipboard (pbcopy) after printing",
    )
    u.set_defaults(fn=cmd_up)

    c = sub.add_parser("checklist", help="JSON checklist (delegates to meet_assist)")
    c.add_argument("--meet-url", required=True)
    c.set_defaults(fn=lambda a: run_checklist(repo_root(), a.meet_url))

    o = sub.add_parser("open-meet", help="Open Meet URL in browser")
    o.add_argument("--meet-url", required=True)
    o.set_defaults(fn=lambda a: run_open_meet(repo_root(), a.meet_url))

    pm = sub.add_parser("paste", help="Draft Meet chat text from session JSON")
    pm.add_argument("--meet-url", required=True)
    pm.add_argument("--session-file", "-f", required=True)
    pm.add_argument("--viewer-url", default="")
    pm.add_argument("--copy", action="store_true", help="macOS: copy block to clipboard (pbcopy)")
    pm.set_defaults(
        fn=lambda a: run_paste(
            repo_root(),
            a.meet_url,
            Path(a.session_file),
            a.viewer_url,
            copy=bool(a.copy),
        )
    )

    args = p.parse_args()
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
