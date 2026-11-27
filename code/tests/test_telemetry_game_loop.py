import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from game import Game


class CountingTelemetry:
    def __init__(self):
        self.flushes = 0
        self.drained = 0

    def flush(self):
        self.flushes += 1

    def flush_all(self):
        self.drained += 1


class VisibilityLog:
    def __init__(self):
        self.states = []
        self.finished = False

    def observe_visibility(self, state):
        self.states.append(state)

    def finish(self):
        self.finished = True


def make_game(visibility_reader=None):
    game = Game.__new__(Game)
    game.telemetry = CountingTelemetry()
    game.session_tracker = VisibilityLog()
    game.visibility_reader = visibility_reader
    game._telemetry_elapsed = 0.0
    return game


class GameTelemetryLoopTest(unittest.TestCase):
    def test_telemetry_flushes_at_most_once_per_second(self):
        game = make_game()

        for _ in range(90):
            game._report_telemetry_periodically(1 / 60)

        self.assertEqual(game.telemetry.flushes, 1)

    def test_visibility_is_polled_with_each_flush(self):
        game = make_game(visibility_reader=lambda: "hidden")

        game._report_telemetry_periodically(1.0)

        self.assertEqual(game.session_tracker.states, ["hidden"])

    def test_finishing_ends_the_session_and_drains_the_queue(self):
        game = make_game()

        game._finish_telemetry()

        self.assertTrue(game.session_tracker.finished)
        self.assertEqual(game.telemetry.drained, 1)


if __name__ == "__main__":
    unittest.main()
