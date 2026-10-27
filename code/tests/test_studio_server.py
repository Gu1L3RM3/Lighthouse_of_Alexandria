import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for path in (REPO / "tools", REPO / "code"):
    if str(path) not in sys.path:
        sys.path.append(str(path))

import level_studio
from studio.campaign import Campaign
from studio.level_service import LevelService


class StudioServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        maps = tmp / "assets" / "maps" / "fases"
        shutil.copytree(REPO / "assets" / "maps" / "fases", maps)
        tileset = Path("images") / "Top_Down_Adventure_Pack_v.1.0" / "Dungeon_Tileset.png"
        (tmp / "assets" / tileset).parent.mkdir(parents=True)
        shutil.copy(REPO / "assets" / tileset, tmp / "assets" / tileset)
        shutil.copytree(REPO / "code" / "circuitos" / "generic_levels_4", tmp / "circuitos" / "generic_levels_4")
        campaign = Campaign(maps, tmp / "circuitos")

        class Handler(level_studio.StudioHandler):
            pass

        Handler.campaign = campaign
        Handler.service = LevelService(campaign)
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls._tmp.cleanup()

    def _request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        payload = json.dumps(body).encode() if body is not None else None
        connection.request(method, path, body=payload, headers=headers or {})
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response.status, data

    def test_campaign_lists_the_stages(self):
        status, data = self._request("GET", "/api/campaign")

        self.assertEqual(status, 200)
        self.assertEqual([stage["number"] for stage in json.loads(data)["stages"]], [3, 4, 5, 6, 7, 8])

    def test_writes_without_a_json_content_type_are_refused(self):
        status, _ = self._request("POST", "/api/campaign/remove", {"scene": "fase_4"}, {"Content-Type": "text/plain"})

        self.assertEqual(status, 403)

    def test_requests_for_another_host_are_refused(self):
        status, _ = self._request("GET", "/api/campaign", headers={"Host": "evil.example:80"})

        self.assertEqual(status, 403)

    def test_tile_images_cannot_escape_the_assets_folder(self):
        status, _ = self._request("GET", "/tiles?scene=fase_4&image=../../../../../code/game.py")

        self.assertEqual(status, 404)

    def test_tileset_image_of_a_level_is_served(self):
        status, data = self._request(
            "GET", "/tiles?scene=fase_4&image=../../../images/Top_Down_Adventure_Pack_v.1.0/Dungeon_Tileset.png"
        )

        self.assertEqual(status, 200)
        self.assertTrue(data.startswith(b"\x89PNG"))

    def test_domain_errors_come_back_as_messages(self):
        status, data = self._request(
            "POST", "/api/campaign/remove", {"scene": "fase_4"}, {"Content-Type": "application/json"}
        )

        self.assertEqual(status, 400)
        self.assertIn("original", json.loads(data)["error"])


if __name__ == "__main__":
    unittest.main()
