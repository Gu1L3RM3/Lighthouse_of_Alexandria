from random import choice
import json

from core.ecs import System
from core.managers.event_manager import EventManager
from core.managers.circuit_manager import CircuitManager
from core.managers.entity_manager import EntityManager
from core.circuit_tools.solve_circuit import CircuitSolver
from core.circuit_tools.serialization_manager import SerializationManager
from entities.itens.control_pannel import ControlPannel
from core.settings import path_in_circuitos, path_in_ltspice


class MaxPowerTransferValidatorSystem(System):
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

    def _parse_solution_types(self, raw: str) -> set[str]:
        if not raw:
            return {"power"}
        tokens = [p.strip().lower() for p in str(raw).split(";") if p.strip()]
        allowed = {"power", "resistance", "voltage", "current"}
        parsed = {t for t in tokens if t in allowed}
        return parsed or {"power"}

    def _pick_source(self, area_sources: dict) -> tuple[str | None, str | None]:
        v_list = list(area_sources.get("voltage", []))
        i_list = list(area_sources.get("current", []))

        if v_list:
            chosen = choice(v_list)
            v_list.remove(chosen)
            area_sources["voltage"] = v_list
            return "V1", chosen
        if i_list:
            chosen = choice(i_list)
            i_list.remove(chosen)
            area_sources["current"] = i_list
            return "I1", chosen
        return None, None

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

    def _pick_source_for_net(self, area_sources: dict, solution_netlist: str) -> tuple[str | None, str | None]:
        has_v1 = self._net_has_component(solution_netlist, "V1")
        has_i1 = self._net_has_component(solution_netlist, "I1")

        v_list = list(area_sources.get("voltage", []))
        i_list = list(area_sources.get("current", []))

        if has_v1 and v_list:
            chosen = choice(v_list)
            v_list.remove(chosen)
            area_sources["voltage"] = v_list
            return "V1", chosen

        if has_i1 and i_list:
            chosen = choice(i_list)
            i_list.remove(chosen)
            area_sources["current"] = i_list
            return "I1", chosen

        return None, None

    def _pick_resistor_for_area(self, area_resistors: list[str]) -> str | None:
        if not area_resistors:
            return None
        chosen = choice(area_resistors)
        area_resistors.remove(chosen)
        return chosen

    def _update_resistor_label_value_in_json(self, json_path: str, resistor_name: str, new_value: str):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        changed = False
        for entity in data:
            if entity.get("entity_type") != "Resistor":
                continue
            for component in entity.get("components", []):
                if component.get("type") != "LabelComponent":
                    continue
                if component.get("name") == resistor_name:
                    component["value"] = str(new_value)
                    changed = True

        if not changed:
            return

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            return

    def _read_solution_targets(self, cp: ControlPannel, solution_netlist: str) -> dict | None:
        target_name = str(cp.target_component).strip()
        if not target_name:
            return None

        solver = CircuitSolver(solution_netlist)
        if not solver.is_solved:
            return None

        resistor_results = solver.get_resistor_results() or {}
        target = resistor_results.get(target_name)
        if not target:
            return None

        voltage = float(target["voltage"]["value"])
        current = float(target["current"]["value"])
        power = float(target["power"]["value"])
        resistance = abs(voltage / current) if abs(current) > 1e-12 else float("inf")

        return {
            "target": target_name,
            "voltage": voltage,
            "current": current,
            "power": power,
            "resistance": resistance,
        }

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        sources_per_area = event.get("sources", {})
        resistors_per_area = event.get("resistors", {})
        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)

        for cp in control_pannels:
            if not cp.active:
                continue

            area = getattr(cp, "component_for_area", None)
            solution_netlist = str(path_in_ltspice(self.level_path, f"pannel{cp.pannel_id}_solution.net"))
            panel_netlist = str(path_in_ltspice(self.level_path, f"pannel{cp.pannel_id}.net"))
            panel_json = str(path_in_circuitos(self.level_path, f"pannel{cp.pannel_id}.json"))
            panel_solution_json = str(path_in_circuitos(self.level_path, f"pannel{cp.pannel_id}_solution.json"))

            area_sources = sources_per_area.get(area)
            if isinstance(area_sources, dict):
                source_name, source_value = self._pick_source_for_net(area_sources, solution_netlist)
                if source_name and source_value is not None:
                    try:
                        SerializationManager.update_component_value(solution_netlist, source_name, source_value)
                    except Exception:
                        pass

            area_resistors = resistors_per_area.get(area)
            if isinstance(area_resistors, list):
                chosen_r = self._pick_resistor_for_area(area_resistors)
                if chosen_r:
                    if self._net_has_component(solution_netlist, "R1"):
                        try:
                            SerializationManager.update_component_value(solution_netlist, "R1", chosen_r)
                        except Exception:
                            pass
                    if self._net_has_component(solution_netlist, "R2"):
                        try:
                            SerializationManager.update_component_value(solution_netlist, "R2", chosen_r)
                        except Exception:
                            pass
                    if self._net_has_component(panel_netlist, "R1"):
                        try:
                            SerializationManager.update_component_value(panel_netlist, "R1", chosen_r)
                        except Exception:
                            pass
                    self._update_resistor_label_value_in_json(panel_json, "R1", chosen_r)
                    self._update_resistor_label_value_in_json(panel_solution_json, "R1", chosen_r)

            solution_values = self._read_solution_targets(cp, solution_netlist)
            if not solution_values:
                continue

            cp.solution_value = solution_values

        self.event_manager.post({"type": "solutions_done"})

    def update(self, entity_mn, dt):
        _ = dt
        control_pannels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)

        for cp in control_pannels:
            if cp.done or not cp.active:
                continue

            expected = cp.solution_value
            if not isinstance(expected, dict):
                continue

            target = expected.get("target")
            if not target:
                continue

            requested_types = self._parse_solution_types(cp.solution_type)
            if "power" not in requested_types:
                requested_types.add("power")
            if "resistance" not in requested_types:
                requested_types.add("resistance")

            circuit_data = self.circuit_manager.get_circuit_values(cp.name_file)
            if not circuit_data:
                continue

            target_data = circuit_data.get(target)
            if not target_data:
                continue

            try:
                ans_v = float(target_data["voltage"]["value"])
                ans_i = float(target_data["current"]["value"])
                ans_p = float(target_data["power"]["value"])
            except Exception:
                continue

            ans_r = abs(ans_v / ans_i) if abs(ans_i) > 1e-12 else float("inf")

            all_ok = True
            if "power" in requested_types:
                exp_p = float(expected["power"])
                all_ok = all_ok and self._float_equals_percent(ans_p, exp_p, self.tolerance_percent)

            if all_ok and "resistance" in requested_types:
                exp_r = float(expected["resistance"])
                all_ok = all_ok and self._float_equals_percent(ans_r, exp_r, self.tolerance_percent)

            if all_ok and "voltage" in requested_types:
                exp_v = float(expected["voltage"])
                all_ok = all_ok and self._float_equals_percent(ans_v, exp_v, self.tolerance_percent)

            if all_ok and "current" in requested_types:
                exp_i = float(expected["current"])
                all_ok = all_ok and self._float_equals_percent(ans_i, exp_i, self.tolerance_percent)

            if all_ok:
                cp.action()
