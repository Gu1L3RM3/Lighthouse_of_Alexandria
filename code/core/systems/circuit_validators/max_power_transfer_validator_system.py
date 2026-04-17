from random import choice
import json
import math
from core.ecs import System
from core.managers.event_manager import EventManager
from core.managers.circuit_manager import CircuitManager
from core.managers.entity_manager import EntityManager
from core.circuit_tools.solve_circuit import CircuitSolver
from core.circuit_tools.serialization_manager import SerializationManager
from core.circuit_tools.lt_spice_generate import LtSpiceGenerate
from entities.itens.control_pannel import ControlPannel
from entities.itens.resistor_item import ResistorItem
from core.components.label_component import LabelComponent
from core.settings import path_in_circuitos, path_in_ltspice, COMERCIAL_RESISTORS


class MaxPowerTransferValidatorSystem(System):
    """
    Validador de máxima transferência de potência.
    Usa as rotinas novas do CircuitSolver para calcular Vth/Rth do componente alvo.
    """

    def __init__(self, level_path: str, tolerance_percent: float = 2.0):
        super().__init__()
        self.level_path = level_path
        self.event_manager = EventManager.get()
        self.circuit_manager = CircuitManager.get()
        self.tolerance_percent = tolerance_percent
        self.debug = True  # habilita logs simples no console
        # Evita spam: loga validacao apenas quando o estado do painel muda.
        self._last_validation_state: dict[int, bool] = {}

    # ------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------
    def _log(self, msg: str):
        if self.debug:
            print(f"[MaxPowerTransfer] {msg}")

    @staticmethod
    def _float_equals_percent(a: float, b: float, percent_tol: float) -> bool:
        if a == 0 and b == 0:
            return True
        reference = max(abs(a), abs(b))
        return abs(a - b) <= reference * (percent_tol / 100.0)

    @staticmethod
    def _parse_solution_types(raw: str) -> set[str]:
        if not raw:
            return {"power"}
        tokens = [p.strip().lower() for p in str(raw).split(";") if p.strip()]
        allowed = {"power", "resistance", "voltage", "current"}
        parsed = {t for t in tokens if t in allowed}
        return parsed or {"power"}

    @staticmethod
    def _label_to_value(label: str) -> float | None:
        """Converte rótulo de resistor (com ou sem sufixo) para valor em ohms."""
        if label is None:
            return None
        label = str(label).strip()
        if not label:
            return None
        if label in COMERCIAL_RESISTORS:
            return float(COMERCIAL_RESISTORS[label])

        suffix_map = {"k": 1e3, "K": 1e3, "m": 1e-3, "M": 1e6}
        for suf, mult in suffix_map.items():
            if label.endswith(suf):
                try:
                    return float(label[:-1]) * mult
                except Exception:
                    return None

        try:
            return float(label)
        except Exception:
            return None

    @staticmethod
    def _nearest_commercial_resistor(target_value: float, allowed_labels: list[str] | None = None) -> tuple[str | None, float | None]:
        """
        Escolhe o valor comercial mais prÃ³ximo de target_value.
        Busca sempre na tabela completa; quem chama garante colocar o valor entre os itens.
        Retorna (label, valor_em_ohms) ou (None, None) se nÃ£o houver candidato.
        """
        if target_value is None or not math.isfinite(target_value) or target_value <= 0:
            return None, None

        candidates = [(lbl, float(val)) for lbl, val in COMERCIAL_RESISTORS.items()]

        if not candidates:
            return None, None

        label, value = min(candidates, key=lambda item: abs(item[1] - target_value))
        return label, value

    @staticmethod
    def _random_resistor_label() -> str:
        from random import choice as _choice

        return _choice(list(COMERCIAL_RESISTORS.keys()))

    @staticmethod
    def _net_has_component(netlist_path: str, component_name: str) -> bool:
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

    @staticmethod
    def _list_resistors(netlist_path: str) -> list[str]:
        names = []
        try:
            with open(netlist_path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("*") or line.startswith("."):
                        continue
                    parts = line.split()
                    if parts and parts[0].startswith("R"):
                        names.append(parts[0])
        except Exception:
            pass
        return names

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
            except Exception as ex:
                self._log(f"Painel {panel_id}{suffix}: falha ao sincronizar netlist ({ex})")

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

    @staticmethod
    def _pick_resistor_for_area(area_resistors: list[str]) -> str | None:
        if not area_resistors:
            return None
        chosen = choice(area_resistors)
        area_resistors.remove(chosen)
        return chosen

    @staticmethod
    def _update_resistor_label_value_in_json(json_path: str, resistor_name: str, new_value: str):
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

    # ------------------------------------------------------
    # Pré-processamento das soluções esperadas
    # ------------------------------------------------------
    def _compute_expected_from_thevenin(self, cp: ControlPannel, solution_netlist: str, load_resistance: float | None = None) -> dict | None:
        """
        Usa o CircuitSolver.get_thevenin para obter Vth e Rth do componente alvo
        e derivar as grandezas de máxima potência.
        """
        target_name = str(cp.target_component).strip()
        if not target_name:
            return None

        solver = CircuitSolver(solution_netlist)
        if not solver.is_solved:
            return None

        th = solver.get_thevenin(target_name)
        if not th:
            return None

        vth = float(th["voltage"]["value"])
        rth = float(th["resistance"]["value"])
        if rth <= 0:
            return None

        rl = float(load_resistance) if load_resistance and load_resistance > 0 else rth

        # Para qualquer RL: P = (Vth**2 * RL) / (Rth + RL)**2
        expected_power = (vth ** 2 * rl) / ((rth + rl) ** 2)
        expected_voltage = vth * (rl / (rth + rl))
        expected_current = expected_voltage / rl

        return {
            "target": target_name,
            "vth": vth,
            "rth": rth,
            "rl": rl,
            "power": expected_power,
            "resistance": rl,
            "voltage": expected_voltage,
            "current": expected_current,
        }

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        self._last_validation_state.clear()
        sources_per_area = event.get("sources", {})
        resistors_per_area = event.get("resistors", {})
        raw_panel_ids = event.get("panel_ids")
        panel_ids_filter = None
        if raw_panel_ids is not None:
            try:
                panel_ids_filter = {int(pid) for pid in raw_panel_ids}
            except Exception:
                panel_ids_filter = None
        control_pannels: list[ControlPannel] = entity_manager.get_entities_by_class(ControlPannel)
        resistor_items: list[ResistorItem] = entity_manager.get_entities_by_class(ResistorItem)

        items_by_area: dict[int, list[ResistorItem]] = {}
        for item in resistor_items:
            items_by_area.setdefault(item.area_id, []).append(item)

        for cp in control_pannels:
            if not cp.active:
                continue
            if panel_ids_filter is not None and int(cp.pannel_id) not in panel_ids_filter:
                continue

            self._sync_netlists_from_json(cp.pannel_id, entity_manager)

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
                        self._log(f"Painel {cp.pannel_id}: fonte {source_name} ajustada para {source_value}")
                    except Exception:
                        pass

            area_resistors = list(resistors_per_area.get(area, []))

            # Randomiza todos os resistores do circuito problema, exceto o alvo (R1).
            target_resistor = cp.target_component or "R1"
            for r_name in self._list_resistors(solution_netlist):
                if r_name == target_resistor:
                    continue
                rand_label = self._random_resistor_label()
                for net_path in (solution_netlist, panel_netlist):
                    if self._net_has_component(net_path, r_name):
                        try:
                            SerializationManager.update_component_value(net_path, r_name, rand_label)
                        except Exception:
                            pass
                self._update_resistor_label_value_in_json(panel_json, r_name, rand_label)
                self._update_resistor_label_value_in_json(panel_solution_json, r_name, rand_label)

            base_expected = self._compute_expected_from_thevenin(cp, solution_netlist)
            if not base_expected:
                self._log(f"Painel {cp.pannel_id}: falha ao calcular Thevenin.")
                continue

            chosen_label, chosen_value = self._nearest_commercial_resistor(base_expected["rth"], area_resistors)
            self._log(
                f"Painel {cp.pannel_id}: Rth={base_expected['rth']:.3g} Ohm -> "
                f"resistor comercial escolhido {chosen_label} ({chosen_value} Ohm)"
            )
            if chosen_value is None:
                chosen_value = base_expected["rth"]

            # Garante que o resistor resposta esteja entre os itens da fase.
            if chosen_label and chosen_label not in area_resistors:
                if area_resistors:
                    area_resistors[0] = chosen_label
                else:
                    area_resistors.append(chosen_label)
            if chosen_label:
                items = items_by_area.get(area, [])
                if items:
                    item = items[0]
                    item.value = chosen_label
                    lbl = item.get(LabelComponent)
                    if lbl:
                        lbl.value = chosen_label
                    self._log(f"Painel {cp.pannel_id}: item de resistor atualizado para {chosen_label}")

            # R1 permanece para o jogador substituir; a valida��o usa chosen_value como carga.
            cp.solution_value = self._compute_expected_from_thevenin(cp, solution_netlist, load_resistance=chosen_value)
            if cp.solution_value:
                self._log(
                    f"Painel {cp.pannel_id}: expectativas -> P={cp.solution_value['power']:.3g}W, "
                    f"V={cp.solution_value['voltage']:.3g}V, I={cp.solution_value['current']:.3g}A, "
                    f"RL={cp.solution_value['rl']:.3g} Ohm"
                )

        self.event_manager.post({"type": "solutions_done"})

    # ------------------------------------------------------
    # Loop de validação em runtime
    # ------------------------------------------------------
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
                all_ok = all_ok and self._float_equals_percent(ans_p, float(expected["power"]), self.tolerance_percent)

            if all_ok and "resistance" in requested_types:
                all_ok = all_ok and self._float_equals_percent(ans_r, float(expected["resistance"]), self.tolerance_percent)

            if all_ok and "voltage" in requested_types:
                all_ok = all_ok and self._float_equals_percent(ans_v, float(expected["voltage"]), self.tolerance_percent)

            if all_ok and "current" in requested_types:
                all_ok = all_ok and self._float_equals_percent(ans_i, float(expected["current"]), self.tolerance_percent)

            panel_id = int(cp.pannel_id)
            previous_state = self._last_validation_state.get(panel_id)
            if previous_state is None or previous_state != all_ok:
                self._last_validation_state[panel_id] = all_ok
                self._log(
                    f"Painel {cp.pannel_id}: medido P={ans_p:.3g}W V={ans_v:.3g}V I={ans_i:.3g}A R={ans_r:.3g} Ohm "
                    f"| esperado P={expected['power']:.3g}W V={expected['voltage']:.3g}V I={expected['current']:.3g}A "
                    f"RL={expected['rl']:.3g} Ohm -> {'OK' if all_ok else 'FAIL'}"
                )

            if all_ok:
                cp.action()
                self._last_validation_state.pop(panel_id, None)




