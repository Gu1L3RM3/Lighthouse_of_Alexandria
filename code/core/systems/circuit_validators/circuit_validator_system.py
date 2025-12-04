from random                                   import choice
from core.ecs                                 import System
from entities.itens.control_pannel            import ControlPannel
from core.managers.circuit_manager            import CircuitManager
from core.managers.entity_manager             import EntityManager
from core.managers.event_manager              import EventManager
from core.circuit_tools.serialization_manager import SerializationManager
from core.circuit_tools.solve_circuit         import CircuitSolver


class CircuitValidatorSystem(System):
    def __init__(self,level_path):
        super().__init__()
        self.level_path =  level_path
        self.circuit_manager = CircuitManager.get()
        self.event_manager   = EventManager.get()


    #TODO: Fazer funcionar para qualquer tipo de lista de componentes [resistors,current sources,voltage_sources]
    def set_solutions(self, event: dict, entity_manager: EntityManager):

        resistors_per_area: dict[int, list[str]] = event['components']

        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)

        for control_pannel in control_pannels:

            area = control_pannel.component_for_area

            if area not in resistors_per_area or len(resistors_per_area[area]) == 0:
                raise ValueError(
                    f"Nenhum resistor disponível para a área {area} (painel {control_pannel.pannel_id})"
                )

            resistors_list  = resistors_per_area[area]
            resistor_chosen = choice(resistors_list)
            resistors_list.remove(resistor_chosen)

            target_component = control_pannel.target_component
            solution_type    = control_pannel.solution_type

            netlist_path = f'ltspice/{self.level_path}/pannel{control_pannel.pannel_id}_solution.net'

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

            print(new_solution_value, control_pannel.pannel_id)

            control_pannel.solution_value = new_solution_value
        self.event_manager.post({'type':'solutions_done'})
    def _float_equals_percent(self,a: float, b: float, percent_tol: float) -> bool:
        """
        Compara dois floats com tolerância percentual.
        
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
                continue
            resistor_results =  self.circuit_manager.get_circuit_values(control_pannel.name_file)
            if not resistor_results:
                continue

            target_component = control_pannel.target_component
            solution_type    = control_pannel.solution_type
            solution_value   = control_pannel.solution_value

            answer = float(resistor_results[target_component][solution_type]['value'])
        
            tolerance_percent = 2 
            is_correct_answer = self._float_equals_percent(answer,solution_value,tolerance_percent)

            if  is_correct_answer:
                control_pannel.action()
            

