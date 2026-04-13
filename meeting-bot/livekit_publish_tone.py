#!/usr/bin/env python3
"""Join an Atlas realtime LiveKit room as a participant and publish a quiet test tone.

Use the JSON from `atlas_session.py start` or `atlas_cli.py realtime create` (fields:
`livekit_url`, `token`). Helps verify local networking + Atlas passthrough wiring
before you swap in real microphone / Meet loopback audio.

Requires: pip install -r meeting-bot/requirements.txt
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import sys
from pathlib import Path

import numpy as np
from livekit import rtc

SAMPLE_RATE = 48_000
NUM_CHANNELS = 1
SAMPLES_PER_CHANNEL = 480  # 10 ms frames


async def publish_tone(source: rtc.AudioSource, frequency: float = 440.0) -> None:
    amplitude = int(32767 * 0.12)
    audio_frame = rtc.AudioFrame.create(SAMPLE_RATE, NUM_CHANNELS, SAMPLES_PER_CHANNEL)
    audio_data = np.frombuffer(audio_frame.data, dtype=np.int16)
    total_samples = 0
    while True:
        t = (total_samples + np.arange(SAMPLES_PER_CHANNEL, dtype=np.float64)) / SAMPLE_RATE
        wave = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
        np.copyto(audio_data, wave)
        await source.capture_frame(audio_frame)
        total_samples += SAMPLES_PER_CHANNEL


async def run(args: argparse.Namespace) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raw = Path(args.session_file).read_text(encoding="utf-8")
    data = json.loads(raw)
    url = data.get("livekit_url")
    token = data.get("token")
    if not url or not token:
        logging.error("session JSON must include livekit_url and token")
        return 2

    room = rtc.Room()
    stop = asyncio.Event()

    def _sig(*_: object) -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _sig)
        except NotImplementedError:
            # Windows: use --duration or close the terminal; Ctrl+C may not wake `stop`.
            if args.duration <= 0:
                logging.warning(
                    "No SIGINT handler on this platform; pass --duration > 0 to exit cleanly."
                )

    await room.connect(url, token)
    logging.info("Connected to LiveKit room=%s local=%s", room.name, room.local_participant.identity)

    source = rtc.AudioSource(SAMPLE_RATE, NUM_CHANNELS)
    track = rtc.LocalAudioTrack.create_audio_track("oss-meet-bot-tone", source)
    opts = rtc.TrackPublishOptions()
    opts.source = rtc.TrackSource.SOURCE_MICROPHONE
    await room.local_participant.publish_track(track, opts)
    logging.info("Publishing 440 Hz test tone (quiet). Ctrl+C to stop.")

    tone_task = asyncio.create_task(publish_tone(source, args.frequency))

    async def stop_after() -> None:
        if args.duration > 0:
            await asyncio.sleep(args.duration)
            stop.set()

    waiter = asyncio.create_task(stop_after()) if args.duration > 0 else None
    await stop.wait()
    if waiter:
        waiter.cancel()
    tone_task.cancel()
    try:
        await tone_task
    except asyncio.CancelledError:
        pass
    await room.disconnect()
    logging.info("Disconnected.")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--session-file", "-f", required=True, help="JSON from Atlas realtime create")
    p.add_argument("--duration", type=float, default=0.0, help="Stop after N seconds (0 = until Ctrl+C)")
    p.add_argument("--frequency", type=float, default=440.0, help="Tone Hz")
    args = p.parse_args()
    try:
        raise SystemExit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
