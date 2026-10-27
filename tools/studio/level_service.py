"""Level data for the studio: circuits, level.json, and the per-panel checklist.

The checklist mirrors what each stage's validator needs at runtime, but reports it up front
in words a teacher can act on.
"""
from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from core.circuit_tools.circuit_domain import CircuitError, CircuitValidationError, ElementKind
from core.circuit_tools.circuit_file_service import SolvedCircuit
from core.circuit_tools.circuit_repository import CircuitJsonRepository
from core.circuit_tools.circuit_topology import CircuitGraphBuilder
from core.circuit_tools.numeric_solver import DcMnaSolver, MissingGroundError, SingularCircuitError
from core.level_config import LevelConfig, LevelConfigError
from core.settings import CELL_SIZE, LEVEL_CONFIG_FILE

from studio.campaign import Campaign
from studio.tmx_io import TmxDocument

PANEL_OBJECT = "control_pannel"
ITEM_LAYER = "itens"
REQUIRED_PANEL_PROPERTIES = ("pannel_id", "type_solution", "target_component", "component_for_area", "action")
PANEL_ACTIONS = ("door", "iron_gate", "active", "bomb_bonus")
COMPONENT_ITEMS = ("resistor", "voltage_source", "current_source")
CIRCUIT_NAME = re.compile(r"^pannel\d+(_solution)?$")
SINGLE_RESISTOR_STAGE = 3
EQUIVALENT_RESISTANCE_STAGE = 4
THEVENIN_STAGES = (6, 7, 8)


def _explain(exc: Exception) -> str:
    if isinstance(exc, MissingGroundError):
        return "Falta um terra (GND) no circuito."
    if isinstance(exc, SingularCircuitError):
        return "O circuito não tem solução única: confira fios soltos, peças sem ligação ou fontes em curto."
    if isinstance(exc, CircuitValidationError):
        return f"Peça inválida: {exc}"
    return str(exc)


class LevelService:
    def __init__(self, campaign: Campaign):
        self.campaign = campaign
        self.repository = CircuitJsonRepository()
        self.builder = CircuitGraphBuilder(CELL_SIZE)
        self.solver = DcMnaSolver()

    # files --------------------------------------------------------------

    def circuit_path(self, scene: str, name: str) -> Path:
        if not CIRCUIT_NAME.match(name):
            raise ValueError(f"Nome de circuito inválido: {name!r}")
        return self.campaign.circuits_dir / self.campaign.level_path(scene) / f"{name}.json"

    def load_circuit(self, scene: str, name: str) -> dict:
        path = self.circuit_path(scene, name)
        if not path.exists():
            return {"schema_version": 2, "elements": []}
        return self.repository.to_payload(self.repository.load(path))

    def save_circuit(self, scene: str, name: str, payload: dict) -> None:
        self.repository.save(self.circuit_path(scene, name), self.repository.decode(payload))

    def config_path(self, scene: str) -> Path:
        return self.campaign.circuits_dir / self.campaign.level_path(scene) / LEVEL_CONFIG_FILE

    def load_config(self, scene: str) -> dict:
        return asdict(LevelConfig.load(self.config_path(scene)))

    def save_config(self, scene: str, payload: dict) -> None:
        LevelConfig.from_dict(payload).save(self.config_path(scene))

    # solving ------------------------------------------------------------

    def solve(self, payload: dict) -> dict:
        try:
            solved = self._solve_document(self.repository.decode(payload))
        except (CircuitError, ValueError) as exc:
            return {"error": _explain(exc), "resistors": {}, "totals": None}
        return {"error": None, "resistors": solved.get_resistor_results(), "totals": solved.get_total_values()}

    def _solve_document(self, document) -> SolvedCircuit:
        graph = self.builder.build(document)
        return SolvedCircuit(graph, self.solver.solve(graph))

    # checklist ----------------------------------------------------------

    def check(self, scene: str) -> dict:
        stage = self.campaign.stage_levels()[scene]
        data = self.campaign_map(scene)
        objects = [obj for group in data["objectgroups"] for obj in group["objects"]]
        items = [obj for obj in objects if obj.get("name") in COMPONENT_ITEMS]
        panels = [obj for obj in objects if obj.get("name") == PANEL_OBJECT]

        problems = []
        if not panels:
            problems.append("A fase não tem nenhum painel (control_pannel).")
        if not any(obj.get("name") == "player" for obj in objects):
            problems.append("Coloque o ponto de partida do jogador (player).")
        try:
            LevelConfig.load(self.config_path(scene))
        except LevelConfigError as exc:
            problems.append(f"level.json inválido: {exc}")
        return {
            "scene": scene,
            "stage": stage.number,
            "problems": problems,
            "panels": [self._check_panel(scene, stage, panel, items) for panel in panels],
        }

    def campaign_map(self, scene: str) -> dict:
        return TmxDocument(self.campaign.tmx_path(scene)).to_dict()

    def _check_panel(self, scene, stage, panel, items) -> dict:
        props = {prop["name"]: prop["value"] for prop in panel["properties"]}
        panel_id = props.get("pannel_id", "?")
        report = {"id": int(panel_id) if str(panel_id).isdigit() else panel_id, "object_id": panel["id"],
                  "problems": [], "expected": {}}
        problems = report["problems"]

        missing = [name for name in REQUIRED_PANEL_PROPERTIES if not props.get(name)]
        if missing:
            problems.append(f"Preencha: {', '.join(missing)}.")
            return report
        if props["action"] not in PANEL_ACTIONS:
            problems.append(f"Ação '{props['action']}' desconhecida; use {', '.join(PANEL_ACTIONS)}.")
        if props["type_solution"] not in stage.answer_types:
            problems.append(
                f"A etapa {stage.number} não valida '{props['type_solution']}'; use {', '.join(stage.answer_types)}."
            )
        area = str(props["component_for_area"])
        if not any(_prop(item, "area") == area and item["name"] == "resistor" for item in items):
            problems.append(f"Não há resistores para coletar na área {area}.")

        for name in (f"pannel{panel_id}", f"pannel{panel_id}_solution"):
            if not self.circuit_path(scene, name).exists():
                problems.append(f"Falta o circuito {name}.json.")
        if problems:
            return report

        try:
            document = self.repository.load(self.circuit_path(scene, f"pannel{panel_id}_solution"))
            solved = self._solve_document(document)
        except (CircuitError, ValueError) as exc:
            problems.append(f"Gabarito: {_explain(exc)}")
            return report

        resistors = [e.name for e in document.elements if e.kind is ElementKind.RESISTOR]
        if stage.number == SINGLE_RESISTOR_STAGE:
            if len(resistors) != 1:
                problems.append(f"O gabarito da etapa 3 precisa de exatamente 1 resistor (tem {len(resistors)}).")
            targets = resistors[:1]
        else:
            targets = [name.strip() for name in props["target_component"].split(",") if name.strip()]
            for name in targets:
                if name not in {e.name for e in document.elements if e.name}:
                    problems.append(f"O componente {name} não existe no gabarito.")

        report["expected"] = self._expected(stage.number, solved, targets)
        return report

    @staticmethod
    def _expected(stage_number: int, solved: SolvedCircuit, targets: list[str]) -> dict:
        results = solved.get_resistor_results()
        expected = {name: results[name] for name in targets if name in results}
        if stage_number == EQUIVALENT_RESISTANCE_STAGE:
            totals = solved.get_total_values()
            if totals:
                expected["resistance"] = totals["resistance"]
        if stage_number in THEVENIN_STAGES:
            for name in targets:
                thevenin = solved.get_thevenin(name)
                if thevenin:
                    expected[f"thevenin_{name}"] = {"voltage": thevenin["voltage"], "resistance": thevenin["resistance"]}
        return expected


def _prop(obj: dict, name: str) -> str | None:
    return next((str(prop["value"]) for prop in obj["properties"] if prop["name"] == name), None)
