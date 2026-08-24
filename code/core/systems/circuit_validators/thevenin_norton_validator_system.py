from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from random import choice, shuffle
from core.ecs import System
from core.managers.event_manager import EventManager
from core.managers.circuit_manager import CircuitManager
from core.managers.entity_manager import EntityManager
from core.circuit_tools.circuit_entity_mapper import CircuitEntityMapper
from core.circuit_tools.circuit_domain import CircuitError
from core.circuit_tools.circuit_file_service import CircuitFileService, CircuitService
from core.components.label_component import LabelComponent
from entities.itens.control_pannel import ControlPannel
from entities.itens.current_source_item import CurrentSourceItem
from entities.itens.resistor_item import ResistorItem
from entities.itens.voltage_source_item import VoltageSourceItem
from core.settings import (
    CELL_SIZE,
    COMERCIAL_RESISTORS,
    MAP_CURRENT_SOURCE_POOL,
    MAP_VOLTAGE_SOURCE_POOL,
    THEVENIN_NORTON_TARGET_RESISTOR,
    path_in_circuitos,
)
from utils.setter_values import SetterValues


class TheveninNortonValidatorSystem(System):
    TARGET_RESISTOR = THEVENIN_NORTON_TARGET_RESISTOR

    def __init__(
        self,
        level_path: str,
        tolerance_percent: float = 2.0,
        circuit_service: CircuitService | None = None,
        entity_mapper: CircuitEntityMapper | None = None,
    ):
        super().__init__()
        self.level_path = level_path
        self.tolerance_percent = tolerance_percent
        self.event_manager = EventManager.get()
        self.circuit_manager = CircuitManager.get()
        self._validation_interval = 0.20
        self._validation_acc = 0.0
        self._panel_rr_index = 0

        self.debug_panel_logs = True
        self.runtime_status_logs = False
        self._panel_status_cache: dict[int, str] = {}
        self.circuits = circuit_service or CircuitFileService(CELL_SIZE)
        self.entity_mapper = entity_mapper or CircuitEntityMapper()

        self._resistor_pool = sorted(
            [(str(label), float(value)) for label, value in COMERCIAL_RESISTORS.items()],
            key=lambda pair: pair[1],
        )
        self._voltage_pool = self._build_labeled_pool(MAP_VOLTAGE_SOURCE_POOL)
        self._current_pool = self._build_labeled_pool(MAP_CURRENT_SOURCE_POOL)

    # =========================================================
    # LOG
    # =========================================================
    def _log(self, message: str):
        _ = message

    def _set_panel_status(self, panel_id: int, status: str):
        if self._panel_status_cache.get(panel_id) == status:
            return
        self._panel_status_cache[panel_id] = status
        if self.runtime_status_logs or status == "solved":
            self._log(f"panel={panel_id} status={status}")

    # =========================================================
    # UTIL
    # =========================================================
    @staticmethod
    def _safe_float(value) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_numeric_value(raw_value) -> float | None:
        if raw_value is None:
            return None

        text = str(raw_value).strip().replace(" ", "")
        if not text:
            return None

        if text.lower().endswith("meg") and len(text) > 3:
            base = text[:-3]
            try:
                return float(base) * 1e6
            except (TypeError, ValueError):
                return None

        if len(text) > 1:
            last = text[-1]
            if last == "M":
                try:
                    return float(text[:-1]) * 1e6
                except (TypeError, ValueError):
                    return None

            suffix_map = {
                "t": 1e12,
                "g": 1e9,
                "k": 1e3,
                "m": 1e-3,
                "u": 1e-6,
                "µ": 1e-6,
                "n": 1e-9,
                "p": 1e-12,
            }
            suffix = last.lower()
            if suffix in suffix_map:
                try:
                    return float(text[:-1]) * suffix_map[suffix]
                except (TypeError, ValueError):
                    return None

        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _float_equals_percent(a: float, b: float, percent_tol: float) -> bool:
        if a == 0 and b == 0:
            return True
        reference = max(abs(a), abs(b))
        return abs(a - b) <= reference * (percent_tol / 100.0)

    def _build_labeled_pool(self, labels: list[str]) -> list[tuple[str, float]]:
        pool: list[tuple[str, float]] = []
        for raw in labels:
            value = self._parse_numeric_value(raw)
            if value is None:
                continue
            pool.append((str(raw), float(value)))
        return pool

    @staticmethod
    def _nearest_labeled(target: float, candidates: list[tuple[str, float]]) -> tuple[str, float] | None:
        if not candidates:
            return None
        return min(candidates, key=lambda pair: abs(pair[1] - target))

    @staticmethod
    def _set_item_value(item, value_label: str):
        item.value = str(value_label)
        if item.has(LabelComponent):
            label: LabelComponent = item.get(LabelComponent)
            label.value = str(value_label)

    def _pick_label_from_pool(self, pool: list[tuple[str, float]]) -> str:
        labels = [str(label) for label, _ in pool] or ["1"]
        return str(choice(labels))

    def _pick_label_from_area(
        self,
        area_labels: dict[int, list[str]],
        area: int,
        fallback_pool: list[tuple[str, float]],
    ) -> str:
        labels = area_labels.get(area, [])
        if labels:
            return str(choice(labels))
        return self._pick_label_from_pool(fallback_pool)

    def _pick_source_label_for_area(
        self,
        sources_per_area: dict[int, dict[str, list[str]]],
        area: int,
        source_kind: str,
    ) -> str:
        area_sources = sources_per_area.get(area, {})
        labels = area_sources.get(source_kind, [])
        if labels:
            return str(choice(labels))
        pool = self._voltage_pool if source_kind == "voltage" else self._current_pool
        return self._pick_label_from_pool(pool)

    def _apply_panel_randomization_inputs(
        self,
        panel_id: int,
        area: int,
        source_kind: str,
        sources_per_area: dict[int, dict[str, list[str]]],
        resistors_per_area: dict[int, list[str]],
    ) -> dict:
        solution_document = str(self._panel_json_path(panel_id, "_solution"))

        source_component = "V1" if source_kind == "voltage" else "I1"
        source_label = self._pick_source_label_for_area(sources_per_area, area, source_kind)
        if self._has_component(solution_document, source_component):
            self.circuits.save_component_value(solution_document, source_component, source_label)
        else:
            self._log(f"panel={panel_id} sem componente {source_component} para randomizar")

        applied_resistors: list[tuple[str, str]] = []
        resistor_names = self._list_resistors(solution_document)
        for r_name in resistor_names:
            if r_name.upper() == self.TARGET_RESISTOR:
                continue
            r_label = self._pick_label_from_area(resistors_per_area, area, self._resistor_pool)
            self.circuits.save_component_value(solution_document, r_name, r_label)
            applied_resistors.append((r_name, r_label))

        return {
            "source": source_label,
            "resistors": applied_resistors,
        }

    # =========================================================
    # PATHS / FILES
    # =========================================================
    def _panel_json_path(self, panel_id: int, suffix: str = ""):
        return path_in_circuitos(self.level_path, f"pannel{panel_id}{suffix}.json")

    def _load_panel_entities(self, panel_id: int):
        try:
            return self.entity_mapper.to_entities(self.circuits.load(self._panel_json_path(panel_id)))
        except (CircuitError, OSError, TypeError, ValueError):
            return []

    def _has_component(self, document_path: str, component_name: str) -> bool:
        return self.circuits.has_component(document_path, component_name)

    def _load_components(self, document_path: str) -> dict[str, tuple[str, str]]:
        return self.circuits.component_nodes(document_path)

    def _list_resistors(self, document_path: str) -> list[str]:
        return self.circuits.resistor_names(document_path)

    # =========================================================
    # TOPOLOGY / PLAYER INPUT
    # =========================================================
    def _entity_label_name(self, entity) -> str:
        if not entity.has(LabelComponent):
            return ""
        label: LabelComponent = entity.get(LabelComponent)
        return str(label.name).strip()

    def _entity_label_value(self, entity) -> str:
        if not entity.has(LabelComponent):
            return ""
        label: LabelComponent = entity.get(LabelComponent)
        return str(label.value).strip()

    def _validate_player_topology(self, panel_id: int) -> tuple[bool, str]:
        entities = self._load_panel_entities(panel_id)
        resistor_labels: list[str] = []
        source_count = 0

        for entity in entities:
            class_name = entity.__class__.__name__
            if class_name == "Resistor":
                resistor_labels.append(self._entity_label_name(entity))
            elif class_name in ("VoltageSource", "CurrentSource"):
                source_count += 1

        if len(resistor_labels) != 2:
            return False, "invalid_topology_resistors"
        if self.TARGET_RESISTOR not in resistor_labels:
            return False, "invalid_topology_missing_R1"
        if source_count != 1:
            return False, "invalid_topology_sources"

        return True, ""

    def _validate_expected_topology(
        self,
        cp: ControlPannel,
        net_components: dict[str, tuple[str, str]]
    ) -> tuple[bool, str]:
        solution_value = cp.solution_value
        if not isinstance(solution_value, dict):
            return False, "waiting_solution_value"

        expected = solution_value.get("expected", {})
        expected_kind = expected.get("source_kind")
        if expected_kind not in ("voltage", "current"):
            return False, "waiting_expected_source_kind"

        # Identify components
        r1_nodes = net_components.get(self.TARGET_RESISTOR)
        if not r1_nodes:
            return False, "invalid_topology_missing_R1_net"

        # pick source by kind
        source_names = [n for n in net_components if n.lower().startswith('v')] if expected_kind == "voltage" else [n for n in net_components if n.lower().startswith('i')]
        if not source_names:
            return False, "invalid_topology_missing_source_net"
        source_name = source_names[0]
        source_nodes = net_components.get(source_name)
        if not source_nodes:
            return False, "invalid_topology_missing_source_net"

        # helper sets
        def shared_count(a: tuple[str, str], b: tuple[str, str]) -> int:
            return len(set(a) & set(b))

        # resistors different from R1
        resistor_items = {k: v for k, v in net_components.items() if k.lower().startswith("r") and k.upper() != self.TARGET_RESISTOR}
        if not resistor_items:
            return False, "invalid_topology_missing_other_resistors_net"

        if expected_kind == "voltage":
            # Need at least one resistor in series with source and R1 (chain)
            for name, nodes in resistor_items.items():
                if shared_count(nodes, source_nodes) == 1 and shared_count(nodes, r1_nodes) == 1:
                    self._log(f"panel={cp.pannel_id} topo_ok_thevenin resistor={name}")
                    return True, ""
            return False, "invalid_series_rth"

        else:
            # Norton: resistor must be parallel with source and R1 (same nodes)
            for name, nodes in resistor_items.items():
                if set(nodes) == set(source_nodes) and set(nodes) == set(r1_nodes):
                    self._log(f"panel={cp.pannel_id} topo_ok_norton resistor={name}")
                    return True, ""
            return False, "invalid_parallel_rn"

    def _extract_player_equivalent_values(self, panel_id: int) -> tuple[dict | None, str]:
        entities = self._load_panel_entities(panel_id)
        resistors: list[dict] = []
        sources: list[dict] = []

        for entity in entities:
            class_name = entity.__class__.__name__
            label_name = self._entity_label_name(entity)
            label_raw_value = self._entity_label_value(entity)
            label_num_value = self._parse_numeric_value(label_raw_value)

            if class_name == "Resistor":
                resistors.append({"name": label_name, "value": label_num_value})
            elif class_name == "VoltageSource":
                sources.append({"kind": "voltage", "name": label_name, "value": label_num_value})
            elif class_name == "CurrentSource":
                sources.append({"kind": "current", "name": label_name, "value": label_num_value})

        if len(sources) != 1:
            return None, "invalid_topology_sources"

        source = sources[0]
        if source["value"] is None:
            return None, "invalid_source_value"

        other_resistors = [r for r in resistors if r["name"] != self.TARGET_RESISTOR]
        if len(other_resistors) != 1:
            return None, "invalid_topology_other_resistor"

        other_resistor = other_resistors[0]
        if other_resistor["value"] is None:
            return None, "invalid_other_resistor_value"

        return {
            "source_kind": source["kind"],
            "source_value": float(source["value"]),
            "resistor_value": float(other_resistor["value"]),
        }, ""

    # =========================================================
    # SOLUTION PREP (target first -> map values later)
    # =========================================================
    def _infer_panel_mode(self, panel_id: int) -> tuple[str | None, str | None]:
        solution_document = str(self._panel_json_path(panel_id, "_solution"))
        has_v1 = self._has_component(solution_document, "V1")
        has_i1 = self._has_component(solution_document, "I1")

        if has_v1 and not has_i1:
            return "thevenin", "voltage"
        if has_i1 and not has_v1:
            return "norton", "current"
        if has_v1:
            return "thevenin", "voltage"
        if has_i1:
            return "norton", "current"
        return None, None

    def _prepare_panel_solution(
        self,
        cp: ControlPannel,
        entity_manager: EntityManager,
        sources_per_area: dict[int, dict[str, list[str]]],
        resistors_per_area: dict[int, list[str]],
    ) -> dict | None:
        area = getattr(cp, "component_for_area", None)
        if area is None:
            self._log(f"panel={cp.pannel_id} ignorado: sem area")
            return None

        mode, source_kind = self._infer_panel_mode(cp.pannel_id)
        if mode is None or source_kind is None:
            self._log(f"panel={cp.pannel_id} sem modo inferido")
            return None

        random_result = self._apply_panel_randomization_inputs(
            panel_id=cp.pannel_id,
            area=area,
            source_kind=source_kind,
            sources_per_area=sources_per_area,
            resistors_per_area=resistors_per_area,
        )
        picked_source = random_result.get("source")
        picked_resistors = random_result.get("resistors", [])

        solution_document = str(self._panel_json_path(cp.pannel_id, "_solution"))
        solver = self.circuits.solve(solution_document)
        if not solver.is_solved:
            self._log(f"panel={cp.pannel_id} solver falhou para {solution_document}")
            return None

        thevenin = solver.get_thevenin(self.TARGET_RESISTOR)
        norton = solver.get_norton(self.TARGET_RESISTOR)
        if thevenin is None or norton is None:
            self._log(f"panel={cp.pannel_id} falha ao calcular Thevenin/Norton")
            return None

        vth = self._safe_float(thevenin.get("voltage", {}).get("value"))
        rth = self._safe_float(thevenin.get("resistance", {}).get("value"))
        inorton = self._safe_float(norton.get("current", {}).get("value"))
        rnorton = self._safe_float(norton.get("resistance", {}).get("value"))
        if None in (vth, rth, inorton, rnorton):
            self._log(f"panel={cp.pannel_id} valores invalidos de equivalente")
            return None

        if mode == "thevenin":
            source_label = "Vth"
            target_source_raw = abs(float(vth))
            source_candidate = self._nearest_labeled(target_source_raw, self._voltage_pool)
            resistance_label = "Rth"
            target_resistance_raw = abs(float(rth))
        else:
            source_label = "In"
            target_source_raw = abs(float(inorton))
            source_candidate = self._nearest_labeled(target_source_raw, self._current_pool)
            resistance_label = "Rn"
            target_resistance_raw = abs(float(rnorton))

        resistance_candidate = self._nearest_labeled(target_resistance_raw, self._resistor_pool)
        if source_candidate is None or resistance_candidate is None:
            self._log(f"panel={cp.pannel_id} sem candidatos comerciais para aproximacao")
            return None

        source_pick_label, source_pick_value = source_candidate
        resistor_pick_label, resistor_pick_value = resistance_candidate

        cp.solution_value = {
            "target": self.TARGET_RESISTOR,
            "mode": mode,
            "thevenin": {
                "voltage": float(vth),
                "resistance": float(rth),
            },
            "norton": {
                "current": float(inorton),
                "resistance": float(rnorton),
            },
            "expected": {
                "source_kind": source_kind,
                "source_label": source_label,
                "source_value_raw": float(target_source_raw),
                "source_value": float(source_pick_value),
                "source_value_label": source_pick_label,
                "resistance_label": resistance_label,
                "resistance_value_raw": float(target_resistance_raw),
                "resistance_value": float(resistor_pick_value),
                "resistance_value_label": resistor_pick_label,
            },
        }

        self._log(
            f"GABARITO painel={cp.pannel_id} area={area} "
            f"entrada_random(source={picked_source}, resistores={picked_resistors}) "
            f"Thevenin(Vth={SetterValues.format_eng(float(vth), 'V')}, Rth={SetterValues.format_eng(float(rth), '')}) "
            f"Norton(In={SetterValues.format_eng(float(inorton), 'A')}, Rn={SetterValues.format_eng(float(rnorton), '')}) "
            f"modo={mode} alvo_aprox={source_label}:{source_pick_label} {resistance_label}:{resistor_pick_label}"
        )

        return {
            "area": area,
            "source_kind": source_kind,
            "source_pick_label": source_pick_label,
            "resistor_pick_label": resistor_pick_label,
        }

    def _apply_requirements_to_map_items(self, entity_manager: EntityManager, requirements: list[dict]):
        req_by_area: dict[int, dict[str, list[str]]] = defaultdict(lambda: {
            "voltage": [],
            "current": [],
            "resistor": [],
        })

        for req in requirements:
            area = req.get("area")
            if area is None:
                continue
            source_kind = req.get("source_kind")
            source_label = req.get("source_pick_label")
            resistor_label = req.get("resistor_pick_label")

            if source_kind == "voltage" and source_label:
                req_by_area[area]["voltage"].append(str(source_label))
            if source_kind == "current" and source_label:
                req_by_area[area]["current"].append(str(source_label))
            if resistor_label:
                req_by_area[area]["resistor"].append(str(resistor_label))

        resistor_items: list[ResistorItem] = entity_manager.get_entities_by_class(ResistorItem)
        voltage_items: list[VoltageSourceItem] = entity_manager.get_entities_by_class(VoltageSourceItem)
        current_items: list[CurrentSourceItem] = entity_manager.get_entities_by_class(CurrentSourceItem)

        resistors_by_area: dict[int, list[ResistorItem]] = defaultdict(list)
        voltages_by_area: dict[int, list[VoltageSourceItem]] = defaultdict(list)
        currents_by_area: dict[int, list[CurrentSourceItem]] = defaultdict(list)

        for item in resistor_items:
            resistors_by_area[getattr(item, "area_id", None)].append(item)
        for item in voltage_items:
            voltages_by_area[getattr(item, "area_id", None)].append(item)
        for item in current_items:
            currents_by_area[getattr(item, "area_id", None)].append(item)

        def random_fill_labels(
            size: int,
            required_labels: list[str],
            fallback_pool: list[tuple[str, float]],
            area: int,
            kind: str,
        ) -> list[str]:
            if size <= 0:
                if required_labels:
                    self._log(f"area={area} sem itens de {kind} para atender requisito: {required_labels}")
                return []

            pool_labels = [str(label) for label, _ in fallback_pool] or ["1"]
            labels_result: list[str | None] = [None] * size

            required_clean = [str(label) for label in required_labels if str(label).strip()]
            if len(required_clean) > size:
                self._log(
                    f"area={area} faltam itens de {kind}: required={len(required_clean)} available={size}"
                )

            slots = list(range(size))
            shuffle(slots)

            for idx, required_label in enumerate(required_clean[:size]):
                labels_result[slots[idx]] = required_label

            for idx in range(size):
                if labels_result[idx] is None:
                    labels_result[idx] = choice(pool_labels)

            return [str(label) for label in labels_result]

        def fill_items(items: list, required_labels: list[str], fallback_pool: list[tuple[str, float]], area: int, kind: str):
            assigned_labels = random_fill_labels(
                size=len(items),
                required_labels=required_labels,
                fallback_pool=fallback_pool,
                area=area,
                kind=kind,
            )
            for idx, item in enumerate(items):
                self._set_item_value(item, assigned_labels[idx])
            if items:
                self._log(f"area={area} kind={kind} assigned={assigned_labels}")

        all_areas = set(resistors_by_area) | set(voltages_by_area) | set(currents_by_area)
        for area in all_areas:
            req = req_by_area.get(area, {"voltage": [], "current": [], "resistor": []})
            fill_items(resistors_by_area.get(area, []), req["resistor"], self._resistor_pool, area, "resistor")
            fill_items(voltages_by_area.get(area, []), req["voltage"], self._voltage_pool, area, "voltage")
            fill_items(currents_by_area.get(area, []), req["current"], self._current_pool, area, "current")
            self._log(
                f"area={area} req(res={req['resistor']}, volt={req['voltage']}, curr={req['current']}) "
                f"itens(res={len(resistors_by_area.get(area, []))}, volt={len(voltages_by_area.get(area, []))}, curr={len(currents_by_area.get(area, []))})"
            )

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        event_data = deepcopy(event) if isinstance(event, dict) else {}
        sources_per_area = event_data.get("sources", {}) if isinstance(event_data.get("sources", {}), dict) else {}
        resistors_per_area = event_data.get("resistors", {}) if isinstance(event_data.get("resistors", {}), dict) else {}

        panels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)
        active_panels = [cp for cp in panels if cp.active]
        active_panels.sort(key=lambda cp: getattr(cp, "pannel_id", 0))

        requirements: list[dict] = []
        for cp in active_panels:
            req = self._prepare_panel_solution(
                cp=cp,
                entity_manager=entity_manager,
                sources_per_area=sources_per_area,
                resistors_per_area=resistors_per_area,
            )
            if req is not None:
                requirements.append(req)

        self._apply_requirements_to_map_items(entity_manager, requirements)
        self.event_manager.post({"type": "solutions_done"})

    # =========================================================
    # RUNTIME VALIDATION
    # =========================================================
    def _validate_equivalent_values(self, cp: ControlPannel, player_values: dict) -> tuple[bool, str]:
        solution_value = cp.solution_value
        if not isinstance(solution_value, dict):
            return False, "waiting_solution_value"

        expected = solution_value.get("expected", {})
        expected_source_kind = expected.get("source_kind")
        expected_source = self._safe_float(expected.get("source_value"))
        expected_resistance = self._safe_float(expected.get("resistance_value"))
        source_label = str(expected.get("source_label", "source"))
        resistance_label = str(expected.get("resistance_label", "resistance"))

        if expected_source_kind not in ("voltage", "current"):
            return False, "waiting_expected_source_kind"
        if expected_source is None:
            return False, "waiting_expected_source_value"
        if expected_resistance is None:
            return False, "waiting_expected_resistance_value"

        source_kind = player_values.get("source_kind")
        answer_source = self._safe_float(player_values.get("source_value"))
        answer_resistance = self._safe_float(player_values.get("resistor_value"))

        if answer_source is None:
            return False, "invalid_source_value"
        if answer_resistance is None:
            return False, "invalid_other_resistor_value"
        if source_kind != expected_source_kind:
            return False, f"source_kind_mismatch expected={expected_source_kind} got={source_kind}"

        if not self._float_equals_percent(abs(answer_source), abs(expected_source), self.tolerance_percent):
            return False, f"mismatch_{source_label} expected={expected_source} got={answer_source}"

        if not self._float_equals_percent(abs(answer_resistance), abs(expected_resistance), self.tolerance_percent):
            return False, f"mismatch_{resistance_label} expected={expected_resistance} got={answer_resistance}"

        return True, ""

    def _validate_panel_runtime(self, cp: ControlPannel):
        if not cp.active:
            self._set_panel_status(cp.pannel_id, "inactive")
            return
        if cp.done:
            self._set_panel_status(cp.pannel_id, "already_done")
            return

        topology_ok, topology_reason = self._validate_player_topology(cp.pannel_id)
        if not topology_ok:
            self._set_panel_status(cp.pannel_id, topology_reason)
            return

        circuit_data = self.circuit_manager.get_circuit_values(cp.name_file)
        if not circuit_data:
            self._set_panel_status(cp.pannel_id, "waiting_player_circuit_data")
            return

        # Topologia elétrica esperada (série para Thevenin, paralelo para Norton)
        document_components = self._load_components(str(self._panel_json_path(cp.pannel_id)))
        topo_expected_ok, topo_expected_reason = self._validate_expected_topology(cp, document_components)
        if not topo_expected_ok:
            self._set_panel_status(cp.pannel_id, topo_expected_reason)
            return

        player_values, player_reason = self._extract_player_equivalent_values(cp.pannel_id)
        if not player_values:
            self._set_panel_status(cp.pannel_id, player_reason or "invalid_player_equivalent")
            return

        valid, reason = self._validate_equivalent_values(cp, player_values)
        if valid:
            self._set_panel_status(cp.pannel_id, "solved")
            cp.action()
        else:
            self._set_panel_status(cp.pannel_id, reason or "validation_failed")

    def update(self, entity_mn, dt):
        self._validation_acc += max(0.0, float(dt))
        if self._validation_acc < self._validation_interval:
            return
        self._validation_acc = 0.0

        panels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)
        candidates = [cp for cp in panels if cp.active and not cp.done]
        if not candidates:
            self._panel_rr_index = 0
            return

        if self._panel_rr_index >= len(candidates):
            self._panel_rr_index = 0

        cp = candidates[self._panel_rr_index]
        self._panel_rr_index = (self._panel_rr_index + 1) % len(candidates)
        self._validate_panel_runtime(cp)




