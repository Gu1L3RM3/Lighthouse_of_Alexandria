import configparser
import json
import unittest
from pathlib import Path

PYGBAG_INI = Path(__file__).resolve().parents[2] / "pygbag.ini"
# Local-only folders: pygbag bundles everything in the tree that is not listed here.
NEVER_SHIPPED = ["/.claude", "/.github", "/.playwright-mcp", "/scripts", "/paper_figures", "/site"]


class WebBundleExcludesTests(unittest.TestCase):
    def test_local_only_folders_are_left_out_of_the_web_bundle(self):
        parser = configparser.ConfigParser()
        parser.read(PYGBAG_INI, encoding="utf-8")
        ignored = json.loads(parser["DEPENDENCIES"]["ignoreDirs"])

        self.assertEqual([folder for folder in NEVER_SHIPPED if folder not in ignored], [])


if __name__ == "__main__":
    unittest.main()
