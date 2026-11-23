# Jarvis

A personal AI assistant in the spirit of Jarvis. Dependency-free Python 3.10+.

## What it does

- **Local skills (offline, no API cost):** time and date, arithmetic, system status, quick notes.
- **Conversation:** anything else goes to Claude when `ANTHROPIC_API_KEY` is set, under a Jarvis persona.
- **Voice output (optional):** speaks replies via `say` (macOS) or `espeak` / `espeak-ng` (Linux).

## Run it

```bash
export ANTHROPIC_API_KEY=your-key          # optional, enables open conversation
export JARVIS_USER_NAME="Alex"             # optional
export JARVIS_HONORIFIC="sir"              # optional
export JARVIS_MODEL="claude-sonnet-5-5"    # optional

python3 -m jarvis                          # interactive session
python3 -m jarvis --speak                  # with spoken replies
python3 -m jarvis --once "what is 12 * 7"  # single request
```

Notes are stored in `~/.jarvis_notes.json` (override with `JARVIS_NOTES_FILE`).

## Remove dead space from a video

`deadspace` cuts silent stretches (and optionally black frames) out of any video that ffmpeg can read. It needs `ffmpeg` and `ffprobe` on your PATH.

```bash
python3 -m deadspace talk.mp4                        # cut silence -> talk_nodead.mp4
python3 -m deadspace talk.mp4 --mode both            # cut only where black AND silent
python3 -m deadspace talk.mp4 --dry-run              # report cuts, write nothing
python3 -m deadspace talk.mp4 --noise-db -40 --min-dead 2 --pad 0.3 -o out.mp4
```

Options: `--mode silence|black|both`, `--noise-db` (audio below this is silent, default -35), `--min-dead` (shortest cut in seconds, default 1.0), `--pad` (seconds kept at each edge of a cut, default 0.25), `--black-threshold`, `--crf` (x264 quality, default 20). Output is re-encoded to H.264/AAC.

Tests for it are included in the test command above (`tests/test_deadspace.py`).

## Test

```bash
python3 -m unittest tests.test_jarvis tests.test_deadspace tests.test_storyvid -v
```

## Layout

| File | Role |
|------|------|
| `jarvis/main.py` | CLI loop; local skills first, then the LLM |
| `jarvis/tools.py` | Local skills and a safe arithmetic evaluator |
| `jarvis/brain.py` | Anthropic Messages API client (stdlib HTTP) |
| `jarvis/persona.py` | Jarvis system prompt |
| `jarvis/voice.py` | Optional OS speech output |
| `deadspace/core.py` | Video dead-space detection (ffmpeg) and cutting |
| `deadspace/__main__.py` | `python3 -m deadspace` command line |

## Not yet included

Speech input (microphone), wake word, and device control (smart home, app launching). These need extra dependencies and platform-specific setup; they can be added as separate modules without changing the core.

## Daily story videos (storyvid)

Turns the next story in a queue into a vertical video and uploads it to YouTube. Free to run: stories are yours, narration uses gTTS, visuals and assembly use ffmpeg, and uploads use the YouTube Data API.

1. Install the one extra dependency: `pip3 install gTTS` (ffmpeg and ffprobe must be on PATH).
2. Add stories as `.txt` files in `storyvid/stories/queue/`. The first line is the title, the rest is the narration. Name files so they sort in posting order, e.g. `002-the-haunted-mine.txt`.
3. Test without uploading: `python3 -m storyvid run --dry-run`. The video lands in `storyvid/out/`.
4. Build and archive without uploading: `python3 -m storyvid run --no-upload`.
5. Full run: `python3 -m storyvid run`. It uploads, then moves the story to `storyvid/stories/posted/`.

Uploads are `private` by default. Set `YOUTUBE_PRIVACY=public` once you're happy with the output.

### YouTube credentials (one-time)

1. In Google Cloud Console, create a project, enable **YouTube Data API v3**, and create an **OAuth client ID** (type: Desktop app).
2. Get a refresh token for scope `https://www.googleapis.com/auth/youtube.upload` (for example with Google's OAuth Playground, using your own client ID and secret).
3. Export the values:

```bash
export YOUTUBE_CLIENT_ID=...
export YOUTUBE_CLIENT_SECRET=...
export YOUTUBE_REFRESH_TOKEN=...
```

The default quota is 10,000 units a day, and each upload costs about 1,600, so you can post roughly 6 videos a day. Google may limit uploads from an unverified API project to private until the project is audited.

### Daily schedule

Add a cron entry (adjust the paths and time):

```bash
0 9 * * * cd /home/user/Doom && YOUTUBE_CLIENT_ID=... YOUTUBE_CLIENT_SECRET=... YOUTUBE_REFRESH_TOKEN=... python3 -m storyvid run >> storyvid/out/cron.log 2>&1
```

Each run logs to `storyvid/out/log.jsonl`. If the queue is empty, the run fails with a clear message, so add stories ahead of time.

Tests: `python3 -m unittest tests.test_storyvid -v`
