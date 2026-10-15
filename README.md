**Deprecated.** This repository is not maintained. The current public example is [akapulu-examples](https://github.com/Akapulu/akapulu-examples).

# Scripted clip workflow

A small Python CLI that walks the Akapulu Labs clip API: list clips, create a clip from a script, print phonemes, poll until complete, then download audio and video.

[Clip workflow guide →](https://docs.akapulu.com/guides/clips/workflow)

## Prerequisites

- **Python 3.10+**
- An **Akapulu API key** — <https://akapulu.com/api-keys>

The script uses **Clara** (`1f777f64-3758-4a7d-9cbc-c64ae654f7d1`) unless you set another catalog id. Browse avatars at <https://akapulu.com/catalog>.

Credits are **1 per estimated minute** of generated video. See the [clips overview](https://docs.akapulu.com/guides/clips/overview).

## Setup

```bash
git clone https://github.com/Akapulu/scripted-clip-workflow.git && cd scripted-clip-workflow
cp .env.example .env
```

Edit `.env` and set `AKAPULU_API_KEY`. Leave `AKAPULU_AVATAR_ID` as Clara, or paste another catalog UUID.

## Run

```bash
python3 create_clip.py
```

The script prints clip status every 10 seconds. On create it prints phonemes. When `status` is `complete` it saves the wav and mp4 under `downloads/<clip_id>/`. `downloads/` is gitignored.
