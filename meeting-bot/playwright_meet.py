#!/usr/bin/env python3
"""Open Google Meet in a persistent Chromium profile (headed).

You join Meet manually (login, Ask to join, etc.). This is not an official Google
Meet API integration — automation may break, trigger warnings, or conflict with
your org policy. Use at your own risk.

Requires: pip install -r meeting-bot/requirements.txt && playwright install chromium
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--meet-url", required=True, help="https://meet.google.com/...")
    p.add_argument(
        "--profile-dir",
        default="",
        help="Persistent Chromium user data dir (default: meeting-bot/.browser-profile)",
    )
    args = p.parse_args()
    url = args.meet_url.strip()
    if "meet.google.com/" not in url.lower() and ".google.com/meet/" not in url.lower():
        print("Error: expected a Google Meet URL.", file=sys.stderr)
        return 2

    profile = (
        Path(args.profile_dir).expanduser().resolve()
        if args.profile_dir.strip()
        else Path(__file__).resolve().parent / ".browser-profile"
    )
    profile.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Install deps: pip install -r meeting-bot/requirements.txt && playwright install chromium",
            file=sys.stderr,
        )
        return 2

    print(f"Launching headed Chromium (profile: {profile})", file=sys.stderr)
    print("Log into Google if prompted, then join the call. Close the window or press Enter here to exit.", file=sys.stderr)

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=False,
            channel=None,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        try:
            input("Press Enter to close the browser and exit…\n")
        except EOFError:
            pass
        finally:
            context.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
