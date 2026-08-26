# Scripted clip workflow

A small Python CLI that walks the Akapulu Labs clip API: list clips, create a clip, generate audio, print phonemes and per-chunk video instructions, then render video.

[Clip workflow guide →](https://docs.akapulu.com/guides/clips/workflow)

## Prerequisites

- **Python 3.10+**
- An **Akapulu API key** — <https://akapulu.com/api-keys>

The script uses **Clara** (`1f777f64-3758-4a7d-9cbc-c64ae654f7d1`) unless you set another catalog id. Browse avatars at <https://akapulu.com/catalog>.

Video takes several minutes and uses more credits than audio. Approximate costs are in the [clips overview](https://docs.akapulu.com/guides/clips/overview).

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

The script prints clip/take status every 10 seconds. After audio is ready it prints phonemes, `audio_url`, and each chunk’s face / upper-body instructions, then saves the audio under `downloads/<take_id>/`. Confirm render, wait for video, then it saves the mp4 in that same folder. `downloads/` is gitignored.
