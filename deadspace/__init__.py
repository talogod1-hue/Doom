"""Remove dead space (silence and/or black frames) from any video via ffmpeg."""

from .core import plan_keep, run

__all__ = ["plan_keep", "run"]
