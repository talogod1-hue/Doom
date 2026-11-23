"""Free text-to-speech via gTTS (Google Translate's public voice, no API key)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def synthesize(text: str, out_mp3: Path, lang: str = "en") -> Path:
    try:
        from gtts import gTTS
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("Narration needs gTTS: pip install gTTS") from exc
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    gTTS(text=text, lang=lang, slow=False).save(str(out_mp3))
    return out_mp3


def duration_seconds(media: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(media)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])
