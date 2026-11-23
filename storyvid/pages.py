"""Split narration into on-screen pages and time each page to the spoken audio."""
from __future__ import annotations

MIN_PAGE_SECONDS = 1.5


def split_pages(body: str, max_words: int = 16) -> list[str]:
    words = body.split()
    pages: list[str] = []
    current: list[str] = []
    for word in words:
        current.append(word)
        # Prefer breaking at the end of a sentence once the page is reasonably full.
        ends_sentence = word[-1:] in ".!?"
        if len(current) >= max_words or (ends_sentence and len(current) >= max_words // 2):
            pages.append(" ".join(current))
            current = []
    if current:
        pages.append(" ".join(current))
    return pages


def page_durations(pages: list[str], total_seconds: float) -> list[float]:
    """Split total_seconds across pages in proportion to word count, with a minimum per page."""
    if not pages:
        return []
    weights = [max(1, len(p.split())) for p in pages]
    total_weight = sum(weights)
    durations = [max(MIN_PAGE_SECONDS, total_seconds * w / total_weight) for w in weights]
    # Rescale so the sum matches the audio exactly (keeps the video the same length as the narration).
    scale = total_seconds / sum(durations)
    return [d * scale for d in durations]
