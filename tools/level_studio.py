"""Level Studio: a local web tool for teachers to edit and add levels.

    python tools/level_studio.py            # opens http://127.0.0.1:8765

It only listens on this computer and writes straight into assets/maps/fases and code/circuitos,
so changes show up in git and in the next game run.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "tools"), str(REPO / "code")]

from core.settings import COMERCIAL_RESISTORS, MAP_CURRENT_SOURCE_POOL, MAP_VOLTAGE_SOURCE_POOL  # noqa: E402
from studio.campaign import Campaign, CampaignError, STAGES  # noqa: E402
from studio.level_service import PANEL_ACTIONS, LevelService  # noqa: E402
from studio.tmx_io import TmxDocument, TmxFormatError  # noqa: E402

MAPS_DIR = REPO / "assets" / "maps" / "fases"
CIRCUITS_DIR = REPO / "code" / "circuitos"
STATIC_DIR = REPO / "tools" / "studio" / "static"
DEFAULT_PORT = 8765
HOST = "127.0.0.1"
MAX_BODY_BYTES = 8 * 1024 * 1024
BLANK_TEMPLATE = "__blank__"


def object_templates(campaign: Campaign) -> dict:
    """One sample of every object kind used in the stage maps, so new objects start with the right properties."""
    templates: dict[str, dict] = {}
    for scene in campaign.stage_levels():
        for group in TmxDocument(campaign.tmx_path(scene)).to_dict()["objectgroups"]:
            for obj in group["objects"]:
                name = obj.get("name")
                if name and obj["shape"] != "tile" and name not in templates:
                    sample = {key: value for key, value in obj.items() if key not in ("id", "x", "y")}
                    templates[name] = {"layer": group["name"], "object": sample}
    return templates


class StudioHandler(BaseHTTPRequestHandler):
    campaign = Campaign(MAPS_DIR, CIRCUITS_DIR)
    service = LevelService(campaign)

    # plumbing -----------------------------------------------------------

    def log_message(self, format, *args):
        sys.stderr.write("[studio] " + format % args + "\n")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status: int = HTTPStatus.OK) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, message: str, status: int = HTTPStatus.BAD_REQUEST) -> None:
        self._json({"error": message}, status)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            raise ValueError("Pedido grande demais")
        return json.loads(self.rfile.read(length) or b"{}")

    def _file(self, path: Path, root: Path) -> None:
        resolved = path.resolve()
        if root.resolve() not in resolved.parents or not resolved.is_file():
            self._error("Arquivo não encontrado", HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        self._send(HTTPStatus.OK, resolved.read_bytes(), content_type)

    def _trusted(self, method: str) -> bool:
        # Block DNS rebinding and cross-site writes: other pages can't send JSON without a CORS preflight.
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        if host not in ("127.0.0.1", "localhost"):
            return False
        return method == "get" or (self.headers.get("Content-Type") or "").startswith("application/json")

    def _dispatch(self, method: str) -> None:
        if not self._trusted(method):
            self._error("Pedido recusado", HTTPStatus.FORBIDDEN)
            return
        url = urlparse(self.path)
        query = {key: values[0] for key, values in parse_qs(url.query).items()}
        route = getattr(self, f"{method}_{url.path.strip('/').replace('/', '_') or 'index'}", None)
        if route is None:
            if method == "get" and url.path.startswith("/static/"):
                self._file(STATIC_DIR / url.path.removeprefix("/static/"), STATIC_DIR)
                return
            self._error("Rota desconhecida", HTTPStatus.NOT_FOUND)
            return
        try:
            route(query)
        except (CampaignError, TmxFormatError, ValueError, KeyError) as exc:
            self._error(str(exc))

    def do_GET(self):
        self._dispatch("get")

    def do_POST(self):
        self._dispatch("post")

    def do_PUT(self):
        self._dispatch("put")

    # routes -------------------------------------------------------------

    def get_index(self, query):
        self._file(STATIC_DIR / "index.html", STATIC_DIR)

    def get_tiles(self, query):
        """A tileset image, addressed relative to the map that uses it."""
        tmx = self.campaign.tmx_path(query["scene"])
        self._file(tmx.parent / query["image"], self.campaign.maps_dir.parents[1])

    def get_api_catalog(self, query):
        self._json({
            "resistors": list(COMERCIAL_RESISTORS),
            "voltage_sources": MAP_VOLTAGE_SOURCE_POOL,
            "current_sources": MAP_CURRENT_SOURCE_POOL,
            "panel_actions": list(PANEL_ACTIONS),
            "templates": object_templates(self.campaign),
        })

    def get_api_campaign(self, query):
        self._json({
            "chain": self.campaign.chain(),
            "stages": self.campaign.stages(),
            "issues": self.campaign.issues(),
            "suggested_names": {stage.number: self.campaign.suggest_name(stage.number) for stage in STAGES},
        })

    def post_api_campaign_insert(self, query):
        body = self._body()
        blank = body.get("template") == BLANK_TEMPLATE
        self.campaign.insert_after(body["after"], body["name"], None if blank else body.get("template") or None, blank=blank)
        self.get_api_campaign(query)

    def post_api_campaign_remove(self, query):
        self.campaign.remove(self._body()["scene"])
        self.get_api_campaign(query)

    def post_api_campaign_move(self, query):
        body = self._body()
        self.campaign.move(body["scene"], body["after"])
        self.get_api_campaign(query)

    def get_api_level(self, query):
        scene = query["scene"]
        stage = self.campaign.stage_levels()[scene]
        self._json({
            "scene": scene,
            "stage": {"number": stage.number, "title": stage.title, "answer_types": list(stage.answer_types)},
            "map": TmxDocument(self.campaign.tmx_path(scene)).to_dict(),
            "config": self.service.load_config(scene),
        })

    def put_api_level(self, query):
        scene = query["scene"]
        body = self._body()
        if "map" in body:
            document = TmxDocument(self.campaign.tmx_path(scene))
            document.update(body["map"])
            document.save()
        if "config" in body:
            self.service.save_config(scene, body["config"])
        self.get_api_level(query)

    def get_api_circuit(self, query):
        self._json(self.service.load_circuit(query["scene"], query["name"]))

    def put_api_circuit(self, query):
        self.service.save_circuit(query["scene"], query["name"], self._body())
        self._json({"saved": True})

    def post_api_solve(self, query):
        self._json(self.service.solve(self._body()))

    def get_api_check(self, query):
        self._json(self.service.check(query["scene"]))

    def post_api_play(self, query):
        scene = self._body()["scene"]
        self.campaign.tmx_path(scene)  # only stage levels can be launched from here
        env = dict(os.environ, ALEX_START_SCENE=scene)
        subprocess.Popen([sys.executable, str(REPO / "main.py")], cwd=REPO, env=env)
        self._json({"started": scene})


def main() -> None:
    parser = argparse.ArgumentParser(description="Estúdio de fases do Farol de Alexandria")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = HTTPServer((HOST, args.port), StudioHandler)
    url = f"http://{HOST}:{args.port}/"
    print(f"Estúdio de fases aberto em {url} (Ctrl+C para fechar)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
