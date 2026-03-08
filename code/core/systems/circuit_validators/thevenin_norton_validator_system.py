from random import choice

from core.ecs import System
from core.managers.event_manager import EventManager
from core.managers.circuit_manager import CircuitManager
from core.managers.entity_manager import EntityManager
from core.circuit_tools.solve_circuit import CircuitSolver
from core.circuit_tools.serialization_manager import SerializationManager
from entities.itens.control_pannel import ControlPannel
from core.settings import path_in_circuitos, path_in_ltspice


class TheveninNortonValidatorSystem(System):
    def __init__(self, level_path: str, tolerance_percent: float = 2.0):
        super().__init__()
        self.level_path = level_path
        self.event_manager = EventManager.get()
        self.circuit_manager = CircuitManager.get()
        self.tolerance_percent = tolerance_percent

    def _float_equals_percent(self, a: float, b: float, percent_tol: float) -> bool:
        if a == 0 and b == 0:
            return True
        reference = max(abs(a), abs(b))
        diff = abs(a - b)
        allowed = reference * (percent_tol / 100.0)
        return diff <= allowed

    def _parse_solution_types(self, s: str) -> set[str]:
        if not s:
            return set()
        parts = [p.strip().lower() for p in str(s).split(";") if p.strip()]
        allowed = {"voltage", "current"}
        return {p for p in parts if p in allowed}

    def _net_has_component(self, netlist_path: str, component_name: str) -> bool:
        try:
            with open(netlist_path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("*") or line.startswith("."):
                        continue
                    parts = line.split()
                    if parts and parts[0] == component_name:
                        return True
        except Exception:
            return False
        return False

    def _load_panel_entities(self, pannel_id: int):
        json_file = path_in_circuitos(self.level_path, f"pannel{pannel_id}.json")
        try:
            return SerializationManager.load_entities_from_json(json_file) or []
        except Exception:
            return []

    def _validate_player_topology(self, pannel_id: int) -> bool:
        # Rule expected by this level: exactly 2 resistors and exactly 1 source.
        entities = self._load_panel_entities(pannel_id)

        resistor_count = 0
        vsrc_count = 0
        isrc_count = 0

        for e in entities:
            name = e.__class__.__name__
            if name == "Resistor":
                resistor_count += 1
            elif name == "VoutageSource":
                vsrc_count += 1
            elif name == "CurrentSource":
                isrc_count += 1

        sources = vsrc_count + isrc_count
        return resistor_count == 2 and sources == 1

    def _pick_source_for_area(self, cp: ControlPannel, types: set[str], area_sources: dict) -> tuple[str | None, str | None]:
        v_list = list(area_sources.get("voltage", []))
        i_list = list(area_sources.get("current", []))

        chosen_kind = None
        chosen_value = None

        # If panel requests voltage/current and voltage exists, prefer voltage.
        if "voltage" in types and v_list:
            chosen_kind = "voltage"
            chosen_value = choice(v_list)
            v_list.remove(chosen_value)
            area_sources["voltage"] = v_list
        elif i_list:
            chosen_kind = "current"
            chosen_value = choice(i_list)
            i_list.remove(chosen_value)
            area_sources["current"] = i_list
        else:
            print(f"[ThN] Area {cp.component_for_area} has no available source values (panel {cp.pannel_id})")

        return chosen_kind, chosen_value

    def _pick_resistor_for_area(self, cp: ControlPannel, area_resistors: list[str]) -> str | None:
        if not area_resistors:
            print(f"[ThN] Area {cp.component_for_area} has no available resistor values (panel {cp.pannel_id})")
            return None

        chosen = choice(area_resistors)
        area_resistors.remove(chosen)
        return chosen

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)

        sources_per_area = event.get("sources", {})      # {area: {"voltage":[...], "current":[...]}}
        resistors_per_area = event.get("resistors", {})  # {area: [resistor_labels]}

        for cp in control_pannels:
            types = self._parse_solution_types(cp.solution_type)
            if not types:
                continue

            raw_targets = str(cp.target_component)
            target_names = [t.strip() for t in raw_targets.split(",") if t.strip()]
            if not target_names:
                continue

            area = getattr(cp, "component_for_area", None)
            if area is None or area not in sources_per_area:
                print(f"[ThN] No sources for area {area} (panel {cp.pannel_id})")
                continue

            area_sources = sources_per_area[area]
            chosen_kind, chosen_value = self._pick_source_for_area(cp, types, area_sources)
            if not chosen_kind or chosen_value is None:
                continue

            netlist_path = str(path_in_ltspice(self.level_path, f"pannel{cp.pannel_id}_solution.net"))

            # Update source in solution netlist.
            if chosen_kind == "voltage":
                if not self._net_has_component(netlist_path, "V1"):
                    print(f"[ThN] Panel {cp.pannel_id} netlist does not contain V1.")
                    continue
                SerializationManager.update_component_value(netlist_path, "V1", chosen_value)
            else:
                if not self._net_has_component(netlist_path, "I1"):
                    print(f"[ThN] Panel {cp.pannel_id} netlist does not contain I1.")
                    continue
                SerializationManager.update_component_value(netlist_path, "I1", chosen_value)

            # Also randomize R2 from resistors available in the same area when present.
            # This keeps answers dynamic with both source and resistor values.
            area_resistors = resistors_per_area.get(area, [])
            chosen_r = self._pick_resistor_for_area(cp, area_resistors)
            if chosen_r and self._net_has_component(netlist_path, "R2"):
                SerializationManager.update_component_value(netlist_path, "R2", chosen_r)

            solver = CircuitSolver(netlist_path)
            if not solver.is_solved:
                print(f"[ThN] Failed to solve panel {cp.pannel_id} netlist")
                continue

            resistor_results = solver.get_resistor_results() or {}
            solution_voltage = {}
            solution_current = {}

            for r_name in target_names:
                if r_name not in resistor_results:
                    continue
                if "voltage" in types:
                    try:
                        solution_voltage[r_name] = float(resistor_results[r_name]["voltage"]["value"])
                    except Exception:
                        pass
                if "current" in types:
                    try:
                        solution_current[r_name] = float(resistor_results[r_name]["current"]["value"])
                    except Exception:
                        pass

            cp.solution_value = {"voltage": solution_voltage, "current": solution_current}

        self.event_manager.post({"type": "solutions_done"})

    def update(self, entity_mn, dt):
        control_pannels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)

        for cp in control_pannels:
            if cp.done:
                continue

            sv = cp.solution_value
            if not isinstance(sv, dict):
                continue

            expected_v = sv.get("voltage", {})
            expected_i = sv.get("current", {})

            types = self._parse_solution_types(cp.solution_type)
            if "voltage" in types and not expected_v:
                continue
            if "current" in types and not expected_i:
                continue

            if not self._validate_player_topology(cp.pannel_id):
                continue

            circuit_data = self.circuit_manager.get_circuit_values(cp.name_file)
            if not circuit_data:
                continue

            all_ok = True

            if "voltage" in types:
                for r_name, exp in expected_v.items():
                    entry = circuit_data.get(r_name)
                    if not entry or "voltage" not in entry:
                        all_ok = False
                        break
                    try:
                        ans = float(entry["voltage"]["value"])
                    except Exception:
                        all_ok = False
                        break
                    if not self._float_equals_percent(ans, exp, self.tolerance_percent):
                        all_ok = False
                        break

            if all_ok and "current" in types:
                for r_name, exp in expected_i.items():
                    entry = circuit_data.get(r_name)
                    if not entry or "current" not in entry:
                        all_ok = False
                        break
                    try:
                        ans = float(entry["current"]["value"])
                    except Exception:
                        all_ok = False
                        break
                    if not self._float_equals_percent(ans, exp, self.tolerance_percent):
                        all_ok = False
                        break

            if all_ok:
                cp.action()
