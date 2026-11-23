"""Build the video with ffmpeg: a Minecraft-style blocky background, a title card, and timed text pages."""
from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

TITLE_SECONDS = 3.0
WIDTH, HEIGHT, FPS = 1080, 1920, 30  # vertical, for Shorts-style uploads
DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WRAP_COLUMNS = 18  # characters per line at fontsize 72 on a 1080px-wide frame


def wrap(text: str) -> str:
    return "\n".join(textwrap.wrap(text, width=WRAP_COLUMNS))


def _font() -> str:
    return os.environ.get("STORYVID_FONT", DEFAULT_FONT)


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True)


def _segment(text_file: Path, seconds: float, out: Path, background: str) -> None:
    """One still-background clip with wrapped text drawn from a file (avoids escaping issues)."""
    text_filter = (
        f"drawtext=fontfile={_font()}:textfile={text_file}:reload=0:fontcolor=white:"
        f"fontsize=72:line_spacing=20:x=(w-text_w)/2:y=(h-text_h)/2:"
        f"box=1:boxcolor=black@0.45:boxborderw=40"
    )
    _run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"color=c={background}:s={WIDTH}x{HEIGHT}:r={FPS}:d={seconds:.3f}",
        "-vf", text_filter, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        str(out),
    ])


def render_video(title: str, pages: list[str], durations: list[float],
                 narration_mp3: Path, out_mp4: Path, workdir: Path) -> Path:
    if len(pages) != len(durations):
        raise ValueError("pages and durations must match")
    workdir.mkdir(parents=True, exist_ok=True)

    segments: list[Path] = []
    title_txt = workdir / "title.txt"
    title_txt.write_text(wrap(title), encoding="utf-8")
    title_seg = workdir / "seg_title.mp4"
    _segment(title_txt, TITLE_SECONDS, title_seg, "0x3b2a1a")
    segments.append(title_seg)

    for i, (page, seconds) in enumerate(zip(pages, durations)):
        txt = workdir / f"page_{i:03d}.txt"
        txt.write_text(wrap(page), encoding="utf-8")
        seg = workdir / f"seg_{i:03d}.mp4"
        # Alternate two grass/stone-like colours so consecutive pages read as separate scenes.
        _segment(txt, seconds, seg, "0x4f7a2e" if i % 2 == 0 else "0x6b5b45")
        segments.append(seg)

    concat_list = workdir / "segments.txt"
    concat_list.write_text("".join(f"file '{s.resolve()}'\n" for s in segments), encoding="utf-8")
    silent_video = workdir / "video.mp4"
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
          "-c", "copy", str(silent_video)])

    # Narration starts after the title card; trailing video length matches the audio.
    delay_ms = int(TITLE_SECONDS * 1000)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-i", str(silent_video), "-i", str(narration_mp3),
        "-filter_complex", f"[1:a]adelay={delay_ms}|{delay_ms},apad[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
        "-shortest", str(out_mp4),
    ])
    return out_mp4
