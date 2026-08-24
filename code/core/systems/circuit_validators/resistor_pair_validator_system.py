from random import choice
from core.ecs import System
from core.managers.entity_manager import EntityManager
from core.managers.event_manager import EventManager
from core.managers.circuit_manager import CircuitManager
from entities.itens.control_pannel import ControlPannel
from core.circuit_tools.circuit_file_service import CircuitFileService, CircuitService
from core.circuit_tools.circuit_domain import CircuitError
from core.settings import CELL_SIZE, path_in_circuitos


class ResistorPairValidatorSystem(System):
    def __init__(
        self,
        level_path: str,
        tolerance_percent: float = 2.0,
        circuit_service: CircuitService | None = None,
    ):
        super().__init__()
        self.level_path = level_path
        self.event_manager = EventManager.get()
        self.circuit_manager = CircuitManager.get()
        self.tolerance_percent = tolerance_percent
        self._validation_interval = 0.12
        self._validation_acc = 0.0
        self._panel_rr_index = 0
        self.debug = True
        self._panel_status_cache: dict[int, str] = {}
        self.circuits = circuit_service or CircuitFileService(CELL_SIZE)

    def _log(self, message: str):
        _ = message

    def _set_panel_status(self, panel_id: int, status: str, details: str = ""):
        if self._panel_status_cache.get(panel_id) == status:
            return
        self._panel_status_cache[panel_id] = status
        message = f"panel={panel_id} status={status}"
        if details:
            message += f" | {details}"
        self._log(message)

    def _panel_json_path(self, panel_id: int, suffix: str = ""):
        return path_in_circuitos(self.level_path, f"pannel{panel_id}{suffix}.json")

    def _float_equals_percent(self, a: float, b: float, percent_tol: float) -> bool:
        if a == 0 and b == 0:
            return True

        reference = max(abs(a), abs(b))
        diff = abs(a - b)
        allowed = reference * (percent_tol / 100.0)
        return diff <= allowed

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        """
        Fase 5:
        - Recebe um dicionario {area_id: [lista de valores de resistores (labels)]}
        - Para cada painel:
            * escolhe um resistor aleatorio da sua area;
            * atualiza SEMPRE o componente R3 do documento de solucao com esse valor;
            * resolve o circuito;
            * le corrente ou tensao de R1, R2, ... conforme target_component;
            * guarda essas solucoes no proprio ControlPannel.
        """
        resistors_per_area: dict[int, list[str]] = event.get("components", {})

        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)

        for control_pannel in control_pannels:
            area = control_pannel.component_for_area

            if area not in resistors_per_area or len(resistors_per_area[area]) == 0:
                continue

            resistors_list = resistors_per_area[area]
            resistor_chosen = choice(resistors_list)

            # Prioriza o documento jogavel do painel para calcular gabarito.
            # Se ele nao tiver R3 (alguns paineis antigos), faz fallback para _solution.
            document_path = str(self._panel_json_path(control_pannel.pannel_id))
            try:
                self.circuits.save_component_value(
                    document_path,
                    "R3",
                    resistor_chosen
                )
            except (CircuitError, OSError):
                document_path = str(self._panel_json_path(control_pannel.pannel_id, "_solution"))
                self.circuits.save_component_value(
                    document_path,
                    "R3",
                    resistor_chosen
                )

            solver = self.circuits.solve(document_path)
            if not solver.is_solved:
                continue

            resistor_results = solver.get_resistor_results()
            if not resistor_results:
                continue

            solution_type = control_pannel.solution_type  # "current" ou "voltage"
            if solution_type not in ("current", "voltage"):
                continue

            raw_targets = str(control_pannel.target_component)
            target_names = [name.strip() for name in raw_targets.split(",") if name.strip()]

            if not target_names:
                continue

            solution_values: dict[str, float] = {}

            for r_name in target_names:
                if r_name not in resistor_results:
                    continue

                entry = resistor_results[r_name].get(solution_type)
                if not entry:
                    continue

                try:
                    solution_values[r_name] = float(entry["value"])
                except (TypeError, ValueError):
                    continue

            if not solution_values:
                continue

            control_pannel.solution_value = solution_values
            self._log(
                f"GABARITO panel={control_pannel.pannel_id} area={area} "
                f"tipo={solution_type} alvo={solution_values} (R3={resistor_chosen})"
            )

        self.event_manager.post({"type": "solutions_done"})

    def update(self, entity_mn, dt):
        self._validation_acc += max(0.0, float(dt))
        if self._validation_acc < self._validation_interval:
            return
        self._validation_acc = 0.0

        control_pannels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)
        for done_panel in control_pannels:
            if done_panel.done:
                self._set_panel_status(int(done_panel.pannel_id), "already_done")

        candidates = [cp for cp in control_pannels if not cp.done]
        if not candidates:
            self._panel_rr_index = 0
            return

        if self._panel_rr_index >= len(candidates):
            self._panel_rr_index = 0
        control_pannel = candidates[self._panel_rr_index]
        self._panel_rr_index = (self._panel_rr_index + 1) % len(candidates)

        solution_values = control_pannel.solution_value
        if not isinstance(solution_values, dict) or not solution_values:
            self._set_panel_status(int(control_pannel.pannel_id), "waiting_solution")
            return

        solution_type = control_pannel.solution_type
        if solution_type not in ("current", "voltage"):
            self._set_panel_status(int(control_pannel.pannel_id), "invalid_solution_type")
            return

        circuit_data = self.circuit_manager.get_circuit_values(control_pannel.name_file)
        if not circuit_data:
            self._set_panel_status(int(control_pannel.pannel_id), "waiting_circuit_data")
            return

        all_ok = True
        measured_values: dict[str, float] = {}

        for r_name, expected_value in solution_values.items():
            res_entry = circuit_data.get(r_name)
            if not res_entry:
                all_ok = False
                break

            if solution_type not in res_entry:
                all_ok = False
                break

            try:
                answer = float(res_entry[solution_type]["value"])
            except (KeyError, TypeError, ValueError):
                all_ok = False
                break
            measured_values[r_name] = answer

            if not self._float_equals_percent(answer, expected_value, self.tolerance_percent):
                if not self._float_equals_percent(abs(answer), abs(expected_value), self.tolerance_percent):
                    all_ok = False
                    break

        if all_ok:
            self._set_panel_status(
                int(control_pannel.pannel_id),
                "solved",
                (
                    f"medido={measured_values} esperado={solution_values} "
                    f"tipo={solution_type} tol={self.tolerance_percent}%"
                ),
            )
            control_pannel.action()
        else:
            self._set_panel_status(
                int(control_pannel.pannel_id),
                "wrong_answer",
                (
                    f"medido={measured_values} esperado={solution_values} "
                    f"tipo={solution_type} tol={self.tolerance_percent}%"
                ),
            )
