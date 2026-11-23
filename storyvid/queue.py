"""Story queue: plain-text files in stories/queue, posted oldest-first."""
from __future__ import annotations

import shutil
from pathlib import Path


def parse_story(text: str) -> tuple[str, str]:
    """First non-empty line is the title; the rest is the narration body."""
    lines = [line.rstrip() for line in text.splitlines()]
    lines = [line for line in lines if line.strip()]
    if not lines:
        raise ValueError("story is empty")
    title = lines[0].lstrip("#").strip()
    body = " ".join(lines[1:]).strip()
    if not body:
        raise ValueError("story has a title but no body")
    return title, body


def list_queue(queue_dir: Path) -> list[Path]:
    """Queued story files, oldest filename first (name files 001-*.txt, 002-*.txt, ...)."""
    return sorted(p for p in queue_dir.glob("*.txt") if p.is_file())


def mark_posted(story: Path, posted_dir: Path) -> Path:
    posted_dir.mkdir(parents=True, exist_ok=True)
    target = posted_dir / story.name
    shutil.move(str(story), str(target))
    return target
