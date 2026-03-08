from random                                   import choice
from core.ecs                                 import System
from core.managers.entity_manager             import EntityManager
from core.managers.event_manager              import EventManager
from core.managers.circuit_manager            import CircuitManager
from entities.itens.control_pannel            import ControlPannel
from core.circuit_tools.serialization_manager import SerializationManager
from core.circuit_tools.solve_circuit         import CircuitSolver
from core.settings                            import path_in_ltspice


class ResistorPairValidatorSystem(System):
    def __init__(self, level_path: str, tolerance_percent: float = 2.0):
        super().__init__()
        self.level_path         = level_path
        self.event_manager      = EventManager.get()
        self.circuit_manager    = CircuitManager.get()
        self.tolerance_percent  = tolerance_percent

    def _float_equals_percent(self, a: float, b: float, percent_tol: float) -> bool:
        if a == 0 and b == 0:
            return True

        reference = max(abs(a), abs(b))
        diff      = abs(a - b)
        allowed   = reference * (percent_tol / 100.0)
        return diff <= allowed

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        """
        Fase 5:
        - Recebe um dicionário {area_id: [lista de valores de resistores (labels)]}
        - Para cada painel:
            * escolhe um resistor aleatório da sua área;
            * atualiza SEMPRE o componente R3 do netlist de solução com esse valor;
            * resolve o circuito;
            * lê corrente ou tensão de R1, R2, ... conforme target_component;
            * guarda essas soluções no próprio ControlPannel.
        """
        resistors_per_area: dict[int, list[str]] = event.get("components", {})

        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)

        for control_pannel in control_pannels:
            area = control_pannel.component_for_area

            if area not in resistors_per_area or len(resistors_per_area[area]) == 0:
                print(f"[ResPair] Nenhum resistor disponível para a área {area} (painel {control_pannel.pannel_id})")
                continue

            resistors_list = resistors_per_area[area]
            resistor_chosen = choice(resistors_list)
            resistors_list.remove(resistor_chosen)

            netlist_path = str(path_in_ltspice(self.level_path, f"pannel{control_pannel.pannel_id}_solution.net"))

            # Sempre substituímos o componente R3 pelo valor escolhido aleatoriamente.
            # O circuito de solução usa o R3 como "resistor secreto" que o jogador precisa descobrir.
            SerializationManager.update_component_value(
                netlist_path,
                "R3",
                resistor_chosen
            )

            solver = CircuitSolver(netlist_path)
            if not solver.is_solved:
                print(f"[ResPair] Falha ao resolver circuito do painel {control_pannel.pannel_id}")
                continue

            resistor_results = solver.get_resistor_results()
            if not resistor_results:
                print(f"[ResPair] Nenhum resultado de resistor no painel {control_pannel.pannel_id}")
                continue

            solution_type = control_pannel.solution_type  # "current" ou "voltage"
            if solution_type not in ("current", "voltage"):
                print(f"[ResPair] solution_type inválido em painel {control_pannel.pannel_id}: {solution_type}")
                continue

            raw_targets = str(control_pannel.target_component)
            target_names = [name.strip() for name in raw_targets.split(",") if name.strip()]

            if not target_names:
                print(f"[ResPair] Nenhum target_component configurado no painel {control_pannel.pannel_id}")
                continue

            solution_values: dict[str, float] = {}

            for r_name in target_names:
                if r_name not in resistor_results:
                    print(f"[ResPair] Resistor {r_name} não encontrado no netlist do painel {control_pannel.pannel_id}")
                    continue

                entry = resistor_results[r_name].get(solution_type)
                if not entry:
                    print(
                        f"[ResPair] solution_type '{solution_type}' não encontrado para {r_name} "
                        f"(painel {control_pannel.pannel_id})"
                    )
                    continue

                try:
                    solution_values[r_name] = float(entry["value"])
                except Exception as e:
                    print(f"[ResPair] Erro ao converter valor de {r_name} para float (painel {control_pannel.pannel_id}): {e}")
                    continue

            if not solution_values:
                print(f"[ResPair] Nenhuma solução válida calculada para painel {control_pannel.pannel_id}")
                continue

            control_pannel.solution_value = solution_values
            print(f"[ResPair] Painel {control_pannel.pannel_id} → soluções: {solution_values}")

        self.event_manager.post({"type": "solutions_done"})

    def update(self, entity_mn, dt):
        control_pannels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)

        for control_pannel in control_pannels:
            if control_pannel.done:
                continue

            solution_values = control_pannel.solution_value
            if not isinstance(solution_values, dict) or not solution_values:
                continue

            solution_type = control_pannel.solution_type
            if solution_type not in ("current", "voltage"):
                continue

            circuit_data = self.circuit_manager.get_circuit_values(control_pannel.name_file)
            if not circuit_data:
                continue

            all_ok = True

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
                except Exception:
                    all_ok = False
                    break

                if not self._float_equals_percent(answer, expected_value, self.tolerance_percent):
                    all_ok = False
                    break

            if all_ok:
                control_pannel.action()
