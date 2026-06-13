from typing import Dict
import random

from core.circuit_tools.serialization_manager import SerializationManager
from core.circuit_tools.solve_circuit import CircuitSolver
from core.circuit_tools.lt_spice_generate import LtSpiceGenerate
from core.components.label_component import LabelComponent
from core.ecs import System
from core.managers.circuit_manager import CircuitManager
from core.managers.entity_manager import EntityManager
from core.managers.event_manager import EventManager
from core.settings import COMERCIAL_RESISTORS, path_in_circuitos, path_in_ltspice
from entities.itens.control_pannel import ControlPannel
from entities.itens.resistor_item import ResistorItem
from utils.setter_values import SetterValues


class ResistorAssotiationValidatorSystem(System):
    def __init__(self, level_path: str):
        super().__init__()
        self.level_path = level_path
        self.event_manager = EventManager.get()
        self.circuit_manager = CircuitManager.get()
        self.tolerance_percent = 2.0
        self._validation_interval = 0.12
        self._validation_acc = 0.0
        self._panel_rr_index = 0

        self.serialization_manager = SerializationManager()

    def _panel_json_path(self, panel_id: int, suffix: str = ""):
        return path_in_circuitos(self.level_path, f"pannel{panel_id}{suffix}.json")

    def _panel_net_path(self, panel_id: int, suffix: str = ""):
        return path_in_ltspice(self.level_path, f"pannel{panel_id}{suffix}.net")

    def _panel_asc_path(self, panel_id: int, suffix: str = ""):
        return path_in_ltspice(self.level_path, f"pannel{panel_id}{suffix}.asc")

    def _sync_netlists_from_json(self, panel_id: int, entity_manager: EntityManager):
        for suffix in ("", "_solution"):
            json_path = self._panel_json_path(panel_id, suffix)
            if not json_path.exists():
                continue
            try:
                LtSpiceGenerate(
                    json_filepath=str(json_path),
                    net_filepath=str(self._panel_net_path(panel_id, suffix)),
                    lt_spice_filepath=str(self._panel_asc_path(panel_id, suffix)),
                    entity_manager=entity_manager,
                ).save_netlist()
            except Exception:
                pass

    def _set_resistor_item_value(self, item: ResistorItem, value: float):
        formatted = SetterValues.format_eng(float(value), "")
        item.value = formatted
        label: LabelComponent = item.get(LabelComponent)
        if label:
            label.value = formatted

    def _log_panel_solution(
        self,
        panel_id: int,
        area: int,
        req_real: float | None,
        req_com: float | None,
        status: str,
    ):
        _ = (panel_id, area, req_real, req_com, status)

    def _log_area_distribution(self, area: int, items: list[ResistorItem], targets: list[float]):
        _ = (area, items, targets)

    def _print_panel_answers(self, control_pannels: list[ControlPannel]):
        _ = control_pannels

    def _float_equals_percent(self, a: float, b: float, percent_tol: float) -> bool:
        if a == 0 and b == 0:
            return True
        reference = max(abs(a), abs(b))
        diff = abs(a - b)
        allowed = reference * (percent_tol / 100.0)
        return diff <= allowed

    def _closest_comercial_resistor(self, value: float) -> tuple[str, float]:
        best_key, best_val = min(
            COMERCIAL_RESISTORS.items(),
            key=lambda kv: abs(kv[1] - value),
        )
        return best_key, best_val

    def _random_comercial_value(self) -> tuple[str, float]:
        key = random.choice(list(COMERCIAL_RESISTORS.keys()))
        return key, COMERCIAL_RESISTORS[key]

    def _random_comercial_value_different_from(
        self,
        excluded_val: float,
        used_vals: set[float],
    ) -> tuple[str, float]:
        valid_items = [
            (k, v)
            for k, v in COMERCIAL_RESISTORS.items()
            if v not in used_vals and abs(v - excluded_val) > 1e-12
        ]

        if valid_items:
            return random.choice(valid_items)

        farthest_key, farthest_val = max(
            COMERCIAL_RESISTORS.items(),
            key=lambda kv: abs(kv[1] - excluded_val),
        )
        return farthest_key, farthest_val

    def _randomize_resistors_in_netlist(self, netlist_path: str) -> Dict[str, str]:
        label_map: Dict[str, str] = {}

        netlist_text = SerializationManager.load_netlist_text(netlist_path)
        if netlist_text is None:
            return label_map
        lines = netlist_text.splitlines()

        resistor_line_indices: list[int] = []
        for i, line in enumerate(lines):
            stripped = line.strip().lower()
            if stripped.startswith("r"):
                resistor_line_indices.append(i)

        if not resistor_line_indices:
            return label_map

        for idx in resistor_line_indices:
            parts = lines[idx].split()
            if len(parts) < 4:
                continue

            comp_name = parts[0]
            _, new_val = self._random_comercial_value()
            formatted = SetterValues.format_eng(new_val, "")

            parts[3] = formatted
            lines[idx] = " ".join(parts)
            label_map[comp_name] = formatted

        SerializationManager.save_netlist_text(netlist_path, "\n".join(lines) + "\n")

        return label_map

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        """
        Fase 4:
        - randomiza resistores dos netlists com valores comerciais;
        - atualiza os JSONs de circuito com os mesmos valores;
        - calcula Req por painel e define solution_value;
        - distribui valores de resistores por area sem sobrescrever
          paines que compartilham a mesma area.
        """
        _ = event
        resistor_items: list[ResistorItem] = entity_manager.get_entities_by_class(ResistorItem)
        resistors_by_area: dict[int, list[ResistorItem]] = {}

        for resistor_item in resistor_items:
            resistors_by_area.setdefault(resistor_item.area_id, []).append(resistor_item)

        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)
        target_values_by_area: dict[int, list[float]] = {}

        for control_pannel in control_pannels:
            area = control_pannel.component_for_area
            area_res_items = resistors_by_area.get(area, [])
            panel_id = control_pannel.pannel_id

            self._sync_netlists_from_json(panel_id, entity_manager)

            if not area_res_items:
                self._log_panel_solution(panel_id, area, None, None, "no_resistors_in_area")
                continue

            netlist_path = str(self._panel_net_path(panel_id, "_solution"))
            json_solution_path = path_in_circuitos(self.level_path, f"pannel{panel_id}.json")

            label_updates = self._randomize_resistors_in_netlist(netlist_path)
            if label_updates:
                try:
                    self.serialization_manager.update_resistor_labels_in_file(
                        json_solution_path,
                        label_updates,
                    )
                except FileNotFoundError:
                    pass
                except Exception:
                    pass

            solver = CircuitSolver(netlist_path)
            if not solver.is_solved:
                self._log_panel_solution(panel_id, area, None, None, "solver_failed")
                continue

            req_real = solver.get_equivalent_resistance()
            if req_real is None:
                self._log_panel_solution(panel_id, area, None, None, "req_none")
                continue

            _, req_com = self._closest_comercial_resistor(req_real)
            control_pannel.solution_value = req_com
            target_values_by_area.setdefault(area, []).append(req_com)
            self._log_panel_solution(panel_id, area, req_real, req_com, "ok")

        for area, area_items in resistors_by_area.items():
            target_values = list(target_values_by_area.get(area, []))
            random.shuffle(target_values)

            available_items = list(area_items)
            random.shuffle(available_items)

            used_values: set[float] = set()

            # Reserve um resistor correto para cada painel da mesma area.
            for target in target_values:
                if not available_items:
                    break
                selected_item = available_items.pop()
                self._set_resistor_item_value(selected_item, target)
                used_values.add(target)

            if used_values:
                excluded_val = next(iter(used_values))
            else:
                _, excluded_val = self._random_comercial_value()

            # Preenche o restante com valores diferentes dos corretos.
            for item in available_items:
                _, fake_val = self._random_comercial_value_different_from(
                    excluded_val=excluded_val,
                    used_vals=used_values,
                )
                used_values.add(fake_val)
                self._set_resistor_item_value(item, fake_val)

            self._log_area_distribution(area, area_items, target_values)

        self._print_panel_answers(control_pannels)
        self.event_manager.post({"type": "solutions_done"})

    def update(self, entity_mn, dt):
        """
        Compara o Req do jogador com o solution_value calculado em set_solutions.
        """
        self._validation_acc += max(0.0, float(dt))
        if self._validation_acc < self._validation_interval:
            return
        self._validation_acc = 0.0

        control_pannels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)
        candidates = [cp for cp in control_pannels if not cp.done and cp.solution_value is not None]
        if not candidates:
            self._panel_rr_index = 0
            return

        if self._panel_rr_index >= len(candidates):
            self._panel_rr_index = 0
        control_pannel = candidates[self._panel_rr_index]
        self._panel_rr_index = (self._panel_rr_index + 1) % len(candidates)

        circuit_data = self.circuit_manager.get_total_values(control_pannel.name_file)
        if not circuit_data:
            return

        resistor_values = self.circuit_manager.get_circuit_values(control_pannel.name_file)
        if not resistor_values:
            return
        if len(resistor_values) != 1:
            return

        req_player = circuit_data.get("resistance", None)
        if req_player is None:
            return

        answer = float(req_player["value"])
        target_req = float(control_pannel.solution_value)
        is_correct = self._float_equals_percent(answer, target_req, self.tolerance_percent)
        if is_correct:
            control_pannel.action()
