import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sharkgame import game as g  # noqa: E402
from sharkgame.__main__ import autopilot  # noqa: E402


def place(game, kind, lane, x=g.WIDTH - 1, size=1):
    """Put a creature directly on the grid so the next tick scrolls it into the shark."""
    game.creatures.append(g.Creature(kind, lane, x, size))


class MovementTests(unittest.TestCase):
    def test_move_up_and_down_clamp_to_lanes(self):
        game = g.Game(seed=1)
        game.shark.lane = 0
        game.step("up")
        self.assertEqual(game.shark.lane, 0)
        game.shark.lane = g.LANES - 1
        game.step("down")
        self.assertEqual(game.shark.lane, g.LANES - 1)

    def test_unknown_action_raises(self):
        with self.assertRaises(ValueError):
            g.Game(seed=1).step("jump")


class CollisionTests(unittest.TestCase):
    def setUp(self):
        self.game = g.Game(seed=1)
        self.game.creatures.clear()
        self.game._rng.random = lambda: 1.0  # disable spawning

    def test_eating_small_fish_gives_xp_and_score(self):
        place(self.game, g.Kind.FISH, lane=1, x=g.SHARK_X + 1, size=1)
        self.game.step("stay")
        self.assertEqual(self.game.shark.xp, 10)
        self.assertEqual(self.game.score, 10)

    def test_fish_bigger_than_shark_gets_away(self):
        place(self.game, g.Kind.FISH, lane=1, x=g.SHARK_X + 1, size=3)
        self.game.step("stay")
        self.assertEqual(self.game.shark.xp, 0)
        self.assertEqual(self.game.score, 0)

    def test_mine_damages_shark(self):
        place(self.game, g.Kind.MINE, lane=1, x=g.SHARK_X + 1)
        self.game.step("stay")
        self.assertEqual(self.game.shark.hp, 100 - g.MINE_DAMAGE)

    def test_boost_doubles_next_fish(self):
        place(self.game, g.Kind.BOOST, lane=1, x=g.SHARK_X + 1)
        self.game.step("stay")
        self.assertGreater(self.game.shark.boost_ticks, 0)
        place(self.game, g.Kind.FISH, lane=1, x=g.SHARK_X + 1, size=1)
        self.game.step("stay")
        # size 1 * 10 * 2 = 20 XP, which exactly reaches level 2 and resets XP to 0.
        self.assertEqual(self.game.score, 20)
        self.assertEqual(self.game.shark.level, 2)

    def test_creature_in_other_lane_is_ignored(self):
        place(self.game, g.Kind.MINE, lane=0, x=g.SHARK_X + 1)
        self.game.step("stay")
        self.assertEqual(self.game.shark.hp, 100)


class ProgressionTests(unittest.TestCase):
    def test_level_up_grows_shark_and_carries_leftover_xp(self):
        game = g.Game(seed=1)
        game.creatures.clear()
        game._rng.random = lambda: 1.0
        game.shark.xp = g.XP_PER_LEVEL - 10
        game.shark.hp = 50
        place(game, g.Kind.FISH, lane=1, x=g.SHARK_X + 1, size=1)  # +10 XP
        game.step("stay")
        self.assertEqual(game.shark.level, 2)
        self.assertEqual(game.shark.xp, 0)
        self.assertEqual(game.shark.max_hp, 110)
        self.assertEqual(game.shark.hp, 70)  # healed by 20

    def test_game_ends_when_hp_reaches_zero(self):
        game = g.Game(seed=1)
        game.shark.hp = 10
        game.creatures.clear()
        game._rng.random = lambda: 1.0
        place(game, g.Kind.MINE, lane=1, x=g.SHARK_X + 1)
        game.step("stay")
        self.assertTrue(game.over)
        self.assertEqual(game.step("stay"), [])  # no further ticks once over


class DeterminismTests(unittest.TestCase):
    def test_same_seed_same_run(self):
        def run(seed):
            game = g.Game(seed=seed)
            while not game.over:
                game.step(autopilot(game))
            return game.score, game.shark.level, game.tick_count

        self.assertEqual(run(7), run(7))

    def test_autopilot_scores_something(self):
        game = g.Game(seed=5)
        while not game.over:
            game.step(autopilot(game))
        self.assertGreater(game.score, 0)


class RenderTests(unittest.TestCase):
    def test_render_shows_shark_and_status(self):
        out = g.render(g.Game(seed=1))
        self.assertIn("S", out)
        self.assertIn("level 1", out)
        self.assertEqual(len(out.splitlines()), g.LANES + 1)


if __name__ == "__main__":
    unittest.main()
