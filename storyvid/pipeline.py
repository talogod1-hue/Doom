"""One daily run: take the next story, narrate it, render it, upload it, then archive the story."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import pages, queue, render, tts, youtube

ROOT = Path(__file__).resolve().parent
STORIES = ROOT / "stories"
OUT = ROOT / "out"
LOG = OUT / "log.jsonl"


def _log(entry: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entry["time"] = dt.datetime.now(dt.timezone.utc).isoformat()
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def run(story_path: Path | None = None, upload: bool = True, dry_run: bool = False,
        audio_override: Path | None = None) -> dict:
    """Produce one video. dry_run builds the video but doesn't upload or archive the story.

    audio_override skips gTTS and uses an existing audio file (used by tests).
    """
    if story_path is None:
        pending = queue.list_queue(STORIES / "queue")
        if not pending:
            raise RuntimeError("Story queue is empty: add a .txt file to storyvid/stories/queue/")
        story_path = pending[0]

    title, body = queue.parse_story(story_path.read_text(encoding="utf-8"))
    stem = story_path.stem
    workdir = OUT / stem
    narration = audio_override or tts.synthesize(body, workdir / "narration.mp3")
    seconds = tts.duration_seconds(narration)
    page_list = pages.split_pages(body)
    durations = pages.page_durations(page_list, seconds)
    video = render.render_video(title, page_list, durations, Path(narration),
                                OUT / f"{stem}.mp4", workdir)
    result = {"story": story_path.name, "title": title, "video": str(video),
              "seconds": round(seconds, 1), "uploaded": False, "dry_run": dry_run}

    if dry_run:
        _log({**result, "status": "dry_run"})
        return result

    if upload:
        description = (f"{title}\n\nA Minecraft drama, narrated.\n\n"
                       "#Minecraft #MinecraftStory #Shorts")
        result["youtube_id"] = youtube.upload_from_env(video, title, description)
        result["uploaded"] = True

    queue.mark_posted(story_path, STORIES / "posted")
    _log({**result, "status": "posted" if upload else "built"})
    return result
