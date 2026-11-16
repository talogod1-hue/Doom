import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_tmp = tempfile.mkdtemp()
os.environ["JARVIS_NOTES_FILE"] = str(Path(_tmp) / "notes.json")

from jarvis import tools  # noqa: E402
from jarvis.brain import Brain  # noqa: E402
from jarvis.main import respond  # noqa: E402
from jarvis.persona import build_system_prompt  # noqa: E402


class SafeEvalTests(unittest.TestCase):
    def test_arithmetic(self):
        self.assertEqual(tools.safe_eval("2 + 3 * 4"), 14)
        self.assertEqual(tools.safe_eval("(2 + 3) ** 2"), 25)
        self.assertEqual(tools.safe_eval("-7 // 2"), -4)

    def test_rejects_code(self):
        for bad in ["__import__('os').system('x')", "open('f')", "a + 1", "[1,2]"]:
            with self.subTest(bad=bad), self.assertRaises((ValueError, SyntaxError, TypeError)):
                tools.safe_eval(bad)

    def test_rejects_huge_power(self):
        with self.assertRaises(ValueError):
            tools.safe_eval("2 ** 99999")


class RouteTests(unittest.TestCase):
    def test_calculator_route(self):
        self.assertEqual(respond("what is 6 * 7", Brain("x", api_key=None)), "That comes to 42.")

    def test_time_route(self):
        self.assertTrue(tools.route_local("what time is it").startswith("It is "))

    def test_notes_round_trip(self):
        tools.route_local("note buy coffee")
        self.assertIn("buy coffee", tools.route_local("notes"))

    def test_unknown_falls_through(self):
        self.assertIsNone(tools.route_local("write me a sonnet about gears"))

    def test_no_key_offline_message(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            reply = Brain("x", api_key=None).ask("hello")
        self.assertIn("ANTHROPIC_API_KEY", reply)


class PersonaTests(unittest.TestCase):
    def test_prompt_uses_name_and_honorific(self):
        prompt = build_system_prompt(user_name="Alex", honorific="boss")
        self.assertIn("Alex", prompt)
        self.assertIn('"boss"', prompt)


if __name__ == "__main__":
    unittest.main()
