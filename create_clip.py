#!/usr/bin/env python3
"""Happy-path clip workflow: create clip → audio → print phonemes/chunks → video."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://akapulu.com/api"
POLL_EVERY_S = 10
HERE = Path(__file__).resolve().parent
DOWNLOADS = HERE / "downloads"
AUDIO_READY = "ready_to_render"
VIDEO_READY = "complete"
FAILED = "failed"
DEFAULT_AVATAR_ID = "1f777f64-3758-4a7d-9cbc-c64ae654f7d1"  # Clara


def load_env():
    path = HERE / ".env"
    if not path.is_file():
        sys.exit(f"Missing {path}. Copy .env.example to .env and fill it in.")
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def require_env(name: str) -> str:
    value = (os.environ.get(name) or "").strip()
    if not value:
        sys.exit(f"{name} is missing in .env")
    return value


def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = None
    headers = {
        "Authorization": f"Bearer {require_env('AKAPULU_API_KEY')}",
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        sys.exit(f"{method} {path} failed ({exc.code}): {detail}")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request) as response, dest.open("wb") as out:
        out.write(response.read())
    print(f"saved {dest}")


def format_eta(seconds) -> str:
    total = int(round(float(seconds or 0)))
    if total < 0:
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def poll_take(clip_id: str, take_id: str, done: str) -> dict:
    path = f"/clips/{clip_id}/takes/{take_id}/"
    while True:
        take = api("GET", path)
        status = take.get("status")
        line = f"  status: {status}"
        if status not in {FAILED, done}:
            line += f"  ~{format_eta(take.get('estimated_seconds'))} left"
        print(line)
        if status == FAILED:
            sys.exit(f"Take failed: {take.get('error')}")
        if status == done:
            return take
        time.sleep(POLL_EVERY_S)


def print_chunks(take: dict) -> None:
    print(f"phonemes:\n{take.get('phonemes') or '(none)'}\n")
    print(f"audio_url:\n{take.get('audio_url')}\n")
    chunks = take.get("chunk_prompts") or []
    if not chunks:
        print("No chunk prompts yet.")
        return
    for chunk in chunks:
        index = chunk.get("index")
        print(f"--- chunk {index} ({chunk.get('start')}s–{chunk.get('end')}s) ---")
        print(chunk.get("text") or "")
        print("face_prompt:")
        print(chunk.get("face_prompt") or "")
        print("upper_body_prompt:")
        print(chunk.get("upper_body_prompt") or "")
        print()


def main() -> None:
    load_env()
    avatar_id = (os.environ.get("AKAPULU_AVATAR_ID") or "").strip() or DEFAULT_AVATAR_ID
    print(f"Avatar: {avatar_id}\n")

    print("Existing clips:")
    clips = api("GET", "/clips/").get("clips") or []
    if not clips:
        print("  (none)")
    for clip in clips:
        print(
            f"  {clip['id']}  {clip['name']}  "
            f"takes={clip.get('take_count')}  favorite={clip.get('favorite_id')}"
        )
    print()

    name = input("New clip name: ").strip()
    if not name:
        sys.exit("Clip name is required.")
    clip = api("POST", "/clips/create/", {"name": name})
    clip_id = clip["id"]
    print(f"Created clip {clip_id}\n")

    text = input("Spoken line: ").strip()
    if not text:
        sys.exit("Spoken line is required.")
    take = api(
        "POST",
        f"/clips/{clip_id}/takes/",
        {"avatar_id": avatar_id, "text": text},
    )
    take_id = take["id"]
    print(f"Created take {take_id} (audio starting)\n")

    print(f"Polling audio every {POLL_EVERY_S}s until {AUDIO_READY}...")
    take = poll_take(clip_id, take_id, AUDIO_READY)
    print_chunks(take)
    audio_url = take.get("audio_url")
    if not audio_url:
        sys.exit("audio_url was empty.")
    download(audio_url, DOWNLOADS / take_id / "audio.wav")

    render = input("Render video? [Y/n] ").strip().lower()
    if render in {"n", "no"}:
        print("Stopped after audio.")
        return

    take = api("POST", f"/clips/{clip_id}/takes/{take_id}/render/", {})
    print(f"Video starting (status {take.get('status')})\n")
    print(f"Polling video every {POLL_EVERY_S}s until {VIDEO_READY}...")
    take = poll_take(clip_id, take_id, VIDEO_READY)
    print(f"video_url:\n{take.get('video_url')}")
    video_url = take.get("video_url")
    if not video_url:
        sys.exit("video_url was empty.")
    download(video_url, DOWNLOADS / take_id / "video.mp4")


if __name__ == "__main__":
    main()
