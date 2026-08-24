from random                                   import choice
from core.ecs                                 import System
from entities.itens.control_pannel            import ControlPannel
from core.managers.circuit_manager            import CircuitManager
from core.managers.entity_manager             import EntityManager
from core.managers.event_manager              import EventManager
from core.circuit_tools.circuit_file_service import CircuitFileService, CircuitService
from core.settings import CELL_SIZE, path_in_circuitos


class CircuitValidatorSystem(System):
    def __init__(self, level_path, circuit_service: CircuitService | None = None):
        super().__init__()
        self.level_path =  level_path
        self.circuit_manager = CircuitManager.get()
        self.event_manager   = EventManager.get()
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

    def _list_resistor_names(self, document_path: str) -> list[str]:
        return self.circuits.resistor_names(document_path)

    def _get_unique_resistor_name(self, resistor_results: dict) -> str | None:
        names = [name for name in resistor_results.keys()]
        if len(names) != 1:
            return None
        return names[0]

    def _get_target_measurement(
        self,
        resistor_results: dict,
        target_component: str,
        solution_type: str,
    ) -> float | None:
        component_data = resistor_results.get(target_component)
        if component_data is None:
            return None

        metric_data = component_data.get(solution_type)
        if metric_data is None:
            return None

        value = metric_data.get("value")
        if value is None:
            return None

        return float(value)

    #TODO: Fazer funcionar para qualquer tipo de lista de componentes [resistors,current sources,voltage_sources]
    def set_solutions(self, event: dict, entity_manager: EntityManager):

        resistors_per_area: dict[int, list[str]] = event['components']

        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)

        for control_pannel in control_pannels:
            area = control_pannel.component_for_area

            if area not in resistors_per_area or len(resistors_per_area[area]) == 0:
                raise ValueError(
                    f"Nenhum resistor disponÃ­vel para a Ã¡rea {area} (painel {control_pannel.pannel_id})"
                )

            target_component = control_pannel.target_component
            solution_type    = control_pannel.solution_type

            document_path = str(self._panel_json_path(control_pannel.pannel_id, "_solution"))
            resistor_names_in_solution = self._list_resistor_names(document_path)
            if len(resistor_names_in_solution) != 1:
                self._set_panel_status(
                    int(control_pannel.pannel_id),
                    "invalid_resistor_count",
                    (
                        f"esperado=1 encontrado={len(resistor_names_in_solution)} "
                        "no circuito de solucao"
                    ),
                )
                continue

            target_component = resistor_names_in_solution[0]
            resistors_list = resistors_per_area[area]
            resistor_chosen = choice(resistors_list)
            resistors_list.remove(resistor_chosen)

            try:
                self.circuits.save_component_value(
                    document_path,
                    target_component,
                    resistor_chosen
                )
            except Exception as ex:
                self._set_panel_status(
                    int(control_pannel.pannel_id),
                    "missing_target_component",
                    f"falha ao atualizar resistor da solucao: {ex}",
                )
                continue

            circuit_solver = self.circuits.solve(document_path)
            resistor_results = circuit_solver.get_resistor_results()
            unique_resistor_name = self._get_unique_resistor_name(resistor_results)
            if unique_resistor_name is None:
                self._set_panel_status(
                    int(control_pannel.pannel_id),
                    "invalid_resistor_count",
                    (
                        f"esperado=1 encontrado={len(resistor_results)} "
                        "na leitura da solucao"
                    ),
                )
                continue

            new_solution_value = self._get_target_measurement(
                resistor_results,
                unique_resistor_name,
                solution_type,
            )
            if new_solution_value is None:
                self._set_panel_status(
                    int(control_pannel.pannel_id),
                    "missing_target_component",
                    (
                        f"alvo={unique_resistor_name} tipo={solution_type} "
                        "nao encontrado no circuito de solucao"
                    ),
                )
                continue


            control_pannel.solution_value = new_solution_value
            self._log(
                f"GABARITO panel={control_pannel.pannel_id} area={area} "
                f"alvo={unique_resistor_name}.{solution_type}="
                f"{new_solution_value:.6g} (R_escolhido={resistor_chosen})"
            )
        self.event_manager.post({'type':'solutions_done'})
    def _float_equals_percent(self,a: float, b: float, percent_tol: float) -> bool:
        """
        Compara dois floats com tolerÃ¢ncia percentual.
        
        """
        if a == 0 and b == 0:
            return True 
        
        reference = max(abs(a), abs(b))
        diff = abs(a - b)
        
        allowed = reference * (percent_tol / 100.0)
        return diff <= allowed


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

        resistor_results = self.circuit_manager.get_circuit_values(control_pannel.name_file)
        if not resistor_results:
            self._set_panel_status(int(control_pannel.pannel_id), "waiting_circuit_data")
            return

        solution_type = control_pannel.solution_type
        solution_value = control_pannel.solution_value
        if solution_value is None:
            self._set_panel_status(
                int(control_pannel.pannel_id),
                "waiting_solution_value",
                "painel sem gabarito valido",
            )
            return

        unique_resistor_name = self._get_unique_resistor_name(resistor_results)
        if unique_resistor_name is None:
            self._set_panel_status(
                int(control_pannel.pannel_id),
                "invalid_resistor_count",
                (
                    f"esperado=1 encontrado={len(resistor_results)} "
                    "no circuito do jogador"
                ),
            )
            return

        answer = self._get_target_measurement(
            resistor_results,
            unique_resistor_name,
            solution_type,
        )
        if answer is None:
            self._set_panel_status(
                int(control_pannel.pannel_id),
                "missing_target_component",
                (
                    f"alvo={unique_resistor_name} tipo={solution_type} "
                    "nao encontrado no circuito do jogador"
                ),
            )
            return

        tolerance_percent = 2
        is_correct_answer = self._float_equals_percent(answer, solution_value, tolerance_percent)

        if is_correct_answer:
            self._set_panel_status(
                int(control_pannel.pannel_id),
                "solved",
                (
                    f"medido={answer:.6g} esperado={float(solution_value):.6g} "
                    f"tipo={solution_type} tol={tolerance_percent}%"
                ),
            )
            control_pannel.action()
        else:
            self._set_panel_status(
                int(control_pannel.pannel_id),
                "wrong_answer",
                (
                    f"medido={answer:.6g} esperado={float(solution_value):.6g} "
                    f"tipo={solution_type} tol={tolerance_percent}%"
                ),
            )
            
