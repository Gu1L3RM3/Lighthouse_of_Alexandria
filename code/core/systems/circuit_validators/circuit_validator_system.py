from random                                   import choice
from core.ecs                                 import System
from entities.itens.control_pannel            import ControlPannel
from core.managers.circuit_manager            import CircuitManager
from core.managers.entity_manager             import EntityManager
from core.managers.event_manager              import EventManager
from core.circuit_tools.serialization_manager import SerializationManager
from core.circuit_tools.solve_circuit         import CircuitSolver
from core.settings                            import path_in_ltspice


class CircuitValidatorSystem(System):
    def __init__(self,level_path):
        super().__init__()
        self.level_path =  level_path
        self.circuit_manager = CircuitManager.get()
        self.event_manager   = EventManager.get()
        self.debug = True
        self._panel_status_cache: dict[int, str] = {}

    def _log(self, message: str):
        if self.debug:
            print(f"[fase_basica][validator] {message}")

    def _set_panel_status(self, panel_id: int, status: str, details: str = ""):
        if self._panel_status_cache.get(panel_id) == status:
            return
        self._panel_status_cache[panel_id] = status
        message = f"panel={panel_id} status={status}"
        if details:
            message += f" | {details}"
        self._log(message)


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

            resistors_list  = resistors_per_area[area]
            resistor_chosen = choice(resistors_list)
            resistors_list.remove(resistor_chosen)

            target_component = control_pannel.target_component
            solution_type    = control_pannel.solution_type

            netlist_path = str(path_in_ltspice(self.level_path, f"pannel{control_pannel.pannel_id}_solution.net"))

            SerializationManager.update_component_value(
                netlist_path,
                target_component,
                resistor_chosen
            )

            circuit_solver = CircuitSolver(netlist_path)
            resistor_results = circuit_solver.get_resistor_results()

            new_solution_value = float(
                resistor_results[target_component][solution_type]['value']
            )


            control_pannel.solution_value = new_solution_value
            self._log(
                f"GABARITO panel={control_pannel.pannel_id} area={area} "
                f"alvo={target_component}.{solution_type}="
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
        control_pannels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)
        for control_pannel in control_pannels:
            if control_pannel.done:
                self._set_panel_status(int(control_pannel.pannel_id), "already_done")
                continue
            resistor_results =  self.circuit_manager.get_circuit_values(control_pannel.name_file)
            if not resistor_results:
                self._set_panel_status(int(control_pannel.pannel_id), "waiting_circuit_data")
                continue

            target_component = control_pannel.target_component
            solution_type    = control_pannel.solution_type
            solution_value   = control_pannel.solution_value

            answer = float(resistor_results[target_component][solution_type]['value'])
        
            tolerance_percent = 2 
            is_correct_answer = self._float_equals_percent(answer,solution_value,tolerance_percent)

            if  is_correct_answer:
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
            

