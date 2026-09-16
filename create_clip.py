#!/usr/bin/env python3
"""Happy-path clip workflow: create clip → poll until complete → download wav/mp4."""

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


def poll_clip(clip_id: str) -> dict:
    path = f"/clips/{clip_id}/"
    while True:
        clip = api("GET", path)
        status = clip.get("status")
        print(f"  status: {status}")
        if status == FAILED:
            sys.exit(f"Clip failed: {clip.get('error')}")
        if status == VIDEO_READY:
            return clip
        time.sleep(POLL_EVERY_S)


def main() -> None:
    load_env()
    avatar_id = (os.environ.get("AKAPULU_AVATAR_ID") or "").strip() or DEFAULT_AVATAR_ID
    print(f"Avatar: {avatar_id}\n")

    print("Existing clips:")
    clips = api("GET", "/clips/").get("clips") or []
    if not clips:
        print("  (none)")
    for clip in clips:
        print(f"  {clip['id']}  {clip['name']}  status={clip.get('status')}")
    print()

    name = input("New clip name: ").strip()
    text = input("Spoken line: ").strip()
    if not text:
        sys.exit("Spoken line is required.")
    body = {"avatar_id": avatar_id, "text": text}
    if name:
        body["name"] = name
    clip = api("POST", "/clips/create/", body)
    clip_id = clip["id"]
    print(f"Created clip {clip_id} (status {clip.get('status')})")
    print(f"phonemes:\n{clip.get('phonemes') or '(none)'}\n")
    print(
        f"credits_charged={clip.get('credits_charged')} "
        f"estimated_seconds={clip.get('estimated_seconds')}\n"
    )

    print(f"Polling every {POLL_EVERY_S}s until {VIDEO_READY}...")
    clip = poll_clip(clip_id)
    audio_url = clip.get("audio_url")
    video_url = clip.get("video_url")
    if not audio_url:
        sys.exit("audio_url was empty.")
    if not video_url:
        sys.exit("video_url was empty.")
    print(f"audio_url:\n{audio_url}\n")
    print(f"video_url:\n{video_url}\n")
    download(audio_url, DOWNLOADS / clip_id / "audio.wav")
    download(video_url, DOWNLOADS / clip_id / "video.mp4")


if __name__ == "__main__":
    main()
