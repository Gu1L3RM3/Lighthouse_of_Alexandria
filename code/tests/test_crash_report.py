import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.crash_report import run_reporting_crashes


class CrashReportTests(unittest.TestCase):
    def test_a_crash_is_reported_and_still_raised(self):
        reports: list[str] = []

        async def crashing_game():
            raise KeyError("door")

        with self.assertRaises(KeyError):
            asyncio.run(run_reporting_crashes(crashing_game, reports.append))

        self.assertEqual(reports, ["KeyError: 'door'"])

    def test_a_normal_run_reports_nothing(self):
        reports: list[str] = []

        async def quiet_game():
            return None

        asyncio.run(run_reporting_crashes(quiet_game, reports.append))

        self.assertEqual(reports, [])

    def test_quitting_the_game_is_not_a_crash(self):
        reports: list[str] = []

        async def quitting_game():
            raise SystemExit

        with self.assertRaises(SystemExit):
            asyncio.run(run_reporting_crashes(quitting_game, reports.append))

        self.assertEqual(reports, [])


if __name__ == "__main__":
    unittest.main()
