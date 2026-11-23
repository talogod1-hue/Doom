import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from storyvid import pages, queue, render, youtube


class ParseStoryTests(unittest.TestCase):
    def test_title_then_body(self):
        title, body = queue.parse_story("# My Story\n\nFirst line.\nSecond line.\n")
        self.assertEqual(title, "My Story")
        self.assertEqual(body, "First line. Second line.")

    def test_empty_and_title_only_raise(self):
        with self.assertRaises(ValueError):
            queue.parse_story("   \n\n")
        with self.assertRaises(ValueError):
            queue.parse_story("Just a title")


class QueueTests(unittest.TestCase):
    def test_oldest_first_and_mark_posted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            q = root / "queue"
            q.mkdir()
            (q / "002-b.txt").write_text("B\nbody")
            (q / "001-a.txt").write_text("A\nbody")
            ordered = queue.list_queue(q)
            self.assertEqual([p.name for p in ordered], ["001-a.txt", "002-b.txt"])
            moved = queue.mark_posted(ordered[0], root / "posted")
            self.assertTrue(moved.exists())
            self.assertFalse((q / "001-a.txt").exists())


class PagesTests(unittest.TestCase):
    def test_pages_respect_max_words(self):
        body = " ".join(["word"] * 40)
        result = pages.split_pages(body, max_words=16)
        self.assertTrue(all(len(p.split()) <= 16 for p in result))
        self.assertEqual(sum(len(p.split()) for p in result), 40)

    def test_durations_sum_to_audio_length(self):
        texts = ["one two three", "four five six seven eight", "nine"]
        durations = pages.page_durations(texts, 30.0)
        self.assertAlmostEqual(sum(durations), 30.0, places=6)
        self.assertGreater(durations[1], durations[0])


class YouTubeConfigTests(unittest.TestCase):
    def test_missing_credentials_are_reported(self):
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                youtube.upload_from_env(Path("x.mp4"), "t", "d")
            self.assertIn("YOUTUBE_CLIENT_ID", str(ctx.exception))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
class RenderTests(unittest.TestCase):
    def test_render_produces_vertical_video_with_expected_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            audio = tmp / "voice.mp3"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                            "sine=frequency=200:duration=6", str(audio)], check=True)
            page_list = ["Short page one.", "Another page here."]
            durations = pages.page_durations(page_list, 6.0)
            out = render.render_video("Title", page_list, durations, audio,
                                      tmp / "out.mp4", tmp / "work")
            info = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=width,height",
                 "-of", "csv=p=0:s=x", str(out)], capture_output=True, text=True, check=True)
            self.assertIn("1080x1920", info.stdout)
            length = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(out)], capture_output=True, text=True, check=True).stdout)
            self.assertAlmostEqual(length, render.TITLE_SECONDS + 6.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
