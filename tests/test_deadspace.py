import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from deadspace import core


def _have_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


class IntervalLogicTest(unittest.TestCase):
    def test_merge_joins_overlaps_and_drops_empty(self):
        self.assertEqual(
            core.merge([(5, 6), (0, 2), (1, 3), (4, 4)]),
            [(0, 3), (5, 6)],
        )

    def test_intersect(self):
        self.assertEqual(
            core.intersect([(0, 4), (6, 10)], [(2, 7)]),
            [(2, 4), (6, 7)],
        )

    def test_dead_intervals_modes(self):
        sil, blk = [(0, 5)], [(3, 8)]
        self.assertEqual(core.dead_intervals("silence", sil, blk), [(0, 5)])
        self.assertEqual(core.dead_intervals("black", sil, blk), [(3, 8)])
        self.assertEqual(core.dead_intervals("both", sil, blk), [(3, 5)])
        with self.assertRaises(ValueError):
            core.dead_intervals("nope", sil, blk)

    def test_plan_keep_pads_each_cut(self):
        keep = core.plan_keep(10.0, [(2.0, 6.0)], pad=0.25)
        self.assertEqual(keep, [(0.0, 2.25), (5.75, 10.0)])

    def test_plan_keep_no_dead_keeps_everything(self):
        self.assertEqual(core.plan_keep(10.0, [], pad=0.25), [(0.0, 10.0)])

    def test_plan_keep_fully_dead_keeps_only_pad_edges(self):
        self.assertEqual(
            core.plan_keep(10.0, [(0.0, 10.0)], pad=0.25),
            [(0.0, 0.25), (9.75, 10.0)],
        )

    def test_plan_keep_drops_sub_min_gap(self):
        # Gap between cuts is 0.05 s, below MIN_KEEP, so it is dropped.
        keep = core.plan_keep(10.0, [(1.0, 4.0), (4.05, 8.0)], pad=0.0)
        self.assertEqual(keep, [(0.0, 1.0), (8.0, 10.0)])

    def test_build_filter_av(self):
        f = core.build_filter([(0, 1), (2, 3)], has_video=True, has_audio=True)
        self.assertIn("[0:v]trim=start=0.000000:end=1.000000", f)
        self.assertIn("[0:a]atrim=start=2.000000:end=3.000000", f)
        self.assertTrue(f.endswith("concat=n=2:v=1:a=1[outv][outa]"))

    def test_build_filter_audio_only(self):
        f = core.build_filter([(0, 1)], has_video=False, has_audio=True)
        self.assertNotIn("[0:v]", f)
        self.assertTrue(f.endswith("concat=n=1:v=0:a=1[outa]"))


@unittest.skipUnless(_have_ffmpeg(), "ffmpeg not installed")
class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "in.mp4"
        # 2 s red with tone, 3 s black with silence, 2 s blue with tone.
        fc = (
            "color=c=red:s=160x120:r=25:d=2[v0];"
            "sine=frequency=440:d=2,volume=0.5[a0];"
            "color=c=black:s=160x120:r=25:d=3[v1];"
            "anullsrc=r=44100:cl=mono,atrim=0:3[a1];"
            "color=c=blue:s=160x120:r=25:d=2[v2];"
            "sine=frequency=660:d=2,volume=0.5[a2];"
            "[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]"
        )
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
             str(self.src)],
            check=True,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_silence_mode_removes_dead_middle(self):
        out = self.tmp / "out.mp4"
        s = core.run(self.src, out, mode="silence", min_dead=1.0, pad=0.25)
        self.assertTrue(out.exists())
        # Dead 2.0-5.0 shrinks to 2.25-4.75: 2.5 s removed of 7 s.
        self.assertAlmostEqual(s["duration"], 7.0, delta=0.15)
        self.assertAlmostEqual(core.probe(out)["duration"], 4.5, delta=0.2)

    def test_both_mode_matches_black_and_silent_region(self):
        out = self.tmp / "both.mp4"
        s = core.run(self.src, out, mode="both", min_dead=1.0, pad=0.25)
        self.assertAlmostEqual(core.probe(out)["duration"], 4.5, delta=0.2)
        self.assertEqual(len(s["dead"]), 1)

    def test_dry_run_writes_nothing(self):
        s = core.run(self.src, None, mode="silence", dry_run=True)
        self.assertIsNone(s["output"])
        self.assertGreater(s["removed_duration"], 2.0)


if __name__ == "__main__":
    unittest.main()
