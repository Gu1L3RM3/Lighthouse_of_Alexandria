from random import choice
import math

from core.ecs import System
from core.managers.event_manager import EventManager
from core.managers.circuit_manager import CircuitManager
from core.managers.entity_manager import EntityManager
from core.circuit_tools.circuit_file_service import CircuitFileService
from entities.itens.control_pannel import ControlPannel
from entities.itens.resistor_item import ResistorItem
from core.components.label_component import LabelComponent
from core.settings import (
    CELL_SIZE,
    path_in_circuitos,
    COMERCIAL_RESISTORS,
)


class MaxPowerTransferValidatorSystem(System):
    """
    Validator for maximum power transfer.

    Rule:
    - Compute Thevenin seen from target resistor terminals (usually R1).
    - Correct answer item is the commercial resistor closest to Rth.
    - Validation compares player circuit against expected values computed with RL=answer.
    """

    def __init__(self, level_path: str, tolerance_percent: float = 5.0):
        super().__init__()
        self.level_path = level_path
        self.event_manager = EventManager.get()
        self.circuit_manager = CircuitManager.get()
        self.tolerance_percent = tolerance_percent
        self.debug = False
        self.gabarito_debug = False
        self._last_validation_state: dict[int, bool] = {}
        self._last_skip_reason: dict[int, str] = {}
        self.validation_debug = False
        self.validation_debug_panels: set[int] = {3}
        self._exact_rth_answer_panels: set[int] = set()
        self.circuits = CircuitFileService(CELL_SIZE)

        # Keep target resistor in problem circuit fixed (requested behavior).
        self._fixed_target_resistor_label = "10"

    # ------------------------------------------------------
    # Utility
    # ------------------------------------------------------
    def _log(self, msg: str):
        _ = msg

    def _trace(self, cp: ControlPannel | None, msg: str):
        _ = (cp, msg)

    @staticmethod
    def _fmt_ohm(value: float | None) -> str:
        if value is None or not math.isfinite(value):
            return "n/a"
        abs_v = abs(float(value))
        if abs_v >= 1e6:
            return f"{value/1e6:.3g}M Ohm"
        if abs_v >= 1e3:
            return f"{value/1e3:.3g}k Ohm"
        return f"{value:.6g} Ohm"

    def _log_gabarito(self, cp: ControlPannel, expected: dict | None):
        _ = (cp, expected)

    def _print_panel_answers(self, control_pannels: list[ControlPannel]):
        _ = control_pannels

    @staticmethod
    def _float_equals_percent(a: float, b: float, percent_tol: float) -> bool:
        if a == 0 and b == 0:
            return True
        reference = max(abs(a), abs(b))
        return abs(a - b) <= reference * (percent_tol / 100.0)

    @staticmethod
    def _percent_error(measured: float, expected: float) -> float:
        if measured == 0 and expected == 0:
            return 0.0
        reference = max(abs(measured), abs(expected))
        if reference <= 1e-18:
            return 0.0
        return (abs(measured - expected) / reference) * 100.0

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
    def _same_resistance_value(a: float | None, b: float | None, rel_tol: float = 1e-9, abs_tol: float = 1e-12) -> bool:
        if a is None or b is None:
            return False
        if not math.isfinite(a) or not math.isfinite(b):
            return False
        return math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=abs_tol)

    @staticmethod
    def _nearest_commercial_resistor(target_value: float, forbidden_value: float | None = None) -> tuple[str | None, float | None]:
        if target_value is None or not math.isfinite(target_value) or target_value <= 0:
            return None, None

        candidates = [(lbl, float(val)) for lbl, val in COMERCIAL_RESISTORS.items()]
        if not candidates:
            return None, None

        if forbidden_value is not None and math.isfinite(forbidden_value) and forbidden_value > 0:
            filtered = [
                item for item in candidates
                if not MaxPowerTransferValidatorSystem._same_resistance_value(item[1], forbidden_value)
            ]
            if filtered:
                candidates = filtered

        label, value = min(candidates, key=lambda item: abs(item[1] - target_value))
        return label, value

    @staticmethod
    def _is_valid_number(value: float) -> bool:
        return value is not None and math.isfinite(value)

    def _is_reasonable_expected(self, expected: dict | None) -> bool:
        if not expected:
            return False
        try:
            v = float(expected.get("voltage", 0.0))
            i = float(expected.get("current", 0.0))
            p = float(expected.get("power", 0.0))
            rl = float(expected.get("rl", 0.0))
            rth = float(expected.get("rth", 0.0))
            vth = float(expected.get("vth", 0.0))
        except Exception:
            return False

        if not all(self._is_valid_number(x) for x in (v, i, p, rl, rth, vth)):
            return False
        if rl <= 0 or rth <= 0:
            return False
        if abs(v) > 1e9 or abs(i) > 1e6 or abs(p) > 1e10:
            return False
        return True

    def _normalize_and_assert_expected_consistency(self, expected: dict) -> dict:
        """
        Single source of truth for expected resistance fields.
        Keeps `rl`, `resistance` and `answer_value` numerically consistent.
        """
        rl = float(expected.get("rl", expected.get("resistance", expected.get("answer_value", 0.0))))
        expected["rl"] = rl
        expected["resistance"] = rl
        expected["answer_value"] = rl

        assert self._same_resistance_value(float(expected["resistance"]), float(expected["answer_value"])), (
            "Inconsistent expected fields: resistance != answer_value"
        )
        assert self._same_resistance_value(float(expected["rl"]), float(expected["answer_value"])), (
            "Inconsistent expected fields: rl != answer_value"
        )
        return expected

    def _has_component(self, document_path: str, component_name: str) -> bool:
        return self.circuits.has_component(document_path, component_name)

    def _list_resistors(self, document_path: str) -> list[str]:
        return self.circuits.resistor_names(document_path)

    def _read_component_value(self, document_path: str, component_name: str) -> tuple[str | None, float | None]:
        return self.circuits.component_value(document_path, component_name)

    def _panel_json_path(self, panel_id: int, suffix: str = ""):
        return path_in_circuitos(self.level_path, f"pannel{panel_id}{suffix}.json")

    def _pick_source(self, area_sources: dict, solution_document: str) -> tuple[str | None, str | None]:
        has_v1 = self._has_component(solution_document, "V1")
        has_i1 = self._has_component(solution_document, "I1")

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
    def _random_resistor_label() -> str:
        from random import choice as _choice

        return _choice(list(COMERCIAL_RESISTORS.keys()))

    def _apply_target_resistor_to_documents(
        self,
        target_resistor: str,
        applied_value: str,
        panel_document: str,
        solution_document: str,
    ):
        for document_path in (solution_document, panel_document):
            if not self._has_component(document_path, target_resistor):
                continue
            self.circuits.update_component_value(document_path, target_resistor, applied_value)

    def _compute_expected_from_thevenin(
        self,
        cp: ControlPannel,
        solution_document: str,
        answer_label: str,
        answer_ohm: float,
    ) -> dict | None:
        target_name = str(cp.target_component).strip()
        if not target_name:
            return None

        solver = self.circuits.solve(solution_document)
        if not solver.is_solved:
            return None

        th = solver.get_thevenin(target_name)
        if not th:
            return None

        try:
            vth = float(th["voltage"]["value"])
            rth = float(th["resistance"]["value"])
        except Exception:
            return None

        if not self._is_valid_number(vth) or not self._is_valid_number(rth):
            return None
        if rth <= 0 or answer_ohm <= 0:
            return None

        rl = float(answer_ohm)
        expected_voltage = vth * (rl / (rth + rl))
        expected_current = expected_voltage / rl
        expected_power = expected_voltage * expected_current

        expected = {
            "target": target_name,
            "answer_label": str(answer_label),
            "answer_value": rl,
            "vth": vth,
            "rth": rth,
            "rl": rl,
            "resistance": rl,
            "voltage": expected_voltage,
            "current": expected_current,
            "power": expected_power,
        }
        expected = self._normalize_and_assert_expected_consistency(expected)
        return expected if self._is_reasonable_expected(expected) else None

    def set_solutions(self, event: dict, entity_manager: EntityManager):
        self._last_validation_state.clear()
        self._last_skip_reason.clear()
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

            area = getattr(cp, "component_for_area", None)
            solution_document = str(self._panel_json_path(cp.pannel_id, "_solution"))
            panel_document = str(self._panel_json_path(cp.pannel_id))

            area_sources = sources_per_area.get(area)
            if isinstance(area_sources, dict):
                source_name, source_value = self._pick_source(area_sources, solution_document)
                if source_name and source_value is not None:
                    for document_path in (solution_document, panel_document):
                        self.circuits.update_component_value(document_path, source_name, source_value)
                    self._trace(cp, f"fonte escolhida: {source_name}={source_value}")

            target_resistor = cp.target_component or "R1"
            self._trace(cp, f"set_solutions: alvo={target_resistor} area={cp.component_for_area}")

            # Randomize all non-target resistors in both problem and solution circuits.
            for r_name in self._list_resistors(solution_document):
                if r_name == target_resistor:
                    continue
                rand_label = self._random_resistor_label()
                for document_path in (solution_document, panel_document):
                    if self._has_component(document_path, r_name):
                        self.circuits.update_component_value(document_path, r_name, rand_label)

            # Keep target resistor fixed in the problem setup.
            self._apply_target_resistor_to_documents(
                target_resistor=target_resistor,
                applied_value=self._fixed_target_resistor_label,
                panel_document=panel_document,
                solution_document=solution_document,
            )

            # Compute Rth from Thevenin and define answer as nearest commercial resistor.
            tmp_expected = self._compute_expected_from_thevenin(
                cp=cp,
                solution_document=solution_document,
                answer_label=self._fixed_target_resistor_label,
                answer_ohm=self._label_to_value(self._fixed_target_resistor_label) or 10.0,
            )
            if not isinstance(tmp_expected, dict):
                cp.solution_value = None
                self._trace(cp, "falha em _compute_expected_from_thevenin (temporario)")
                self._log(f"Painel {cp.pannel_id}: falha ao calcular Thevenin.")
                continue

            rth = float(tmp_expected["rth"])
            panel_id = int(cp.pannel_id)
            if panel_id in self._exact_rth_answer_panels:
                answer_ohm = float(rth)
                answer_label = f"{answer_ohm:.6g}"
                self._trace(
                    cp,
                    f"resposta especial: usando Rth exato sem aproximacao comercial -> {answer_label} Ohm",
                )
            else:
                _, target_problem_value = self._read_component_value(panel_document, target_resistor)
                answer_label, answer_ohm = self._nearest_commercial_resistor(rth, forbidden_value=target_problem_value)
            self._trace(
                cp,
                "thevenin: "
                f"Rth={self._fmt_ohm(rth)} Vth={tmp_expected.get('vth', 0.0):.6g}V "
                f"| R1_problema={self._fmt_ohm(self._read_component_value(panel_document, target_resistor)[1])} "
                f"| resposta_escolhida={answer_label} ({self._fmt_ohm(answer_ohm)})",
            )
            if answer_label is None or answer_ohm is None:
                cp.solution_value = None
                self._trace(cp, "sem candidato comercial para resposta")
                self._log(f"Painel {cp.pannel_id}: sem resistor comercial candidato.")
                continue

            expected = self._compute_expected_from_thevenin(
                cp=cp,
                solution_document=solution_document,
                answer_label=answer_label,
                answer_ohm=float(answer_ohm),
            )
            if not isinstance(expected, dict):
                cp.solution_value = None
                self._trace(cp, "falha em _compute_expected_from_thevenin (final)")
                self._log(f"Painel {cp.pannel_id}: falha ao montar gabarito final.")
                continue

            cp.solution_value = expected
            self._trace(
                cp,
                "gabarito final: "
                f"RL={self._fmt_ohm(expected.get('rl'))} "
                f"P={float(expected.get('power', 0.0)):.6g}W "
                f"V={float(expected.get('voltage', 0.0)):.6g}V "
                f"I={float(expected.get('current', 0.0)):.6g}A",
            )

            # Ensure answer item is available in the area item pool.
            area_resistors = list(resistors_per_area.get(area, []))
            if answer_label not in area_resistors:
                if area_resistors:
                    replace_idx = choice(range(len(area_resistors)))
                    area_resistors[replace_idx] = answer_label
                else:
                    area_resistors.append(answer_label)
                try:
                    area_key = int(area)
                    resistors_per_area.setdefault(area_key, [])
                    if resistors_per_area[area_key]:
                        replace_idx = choice(range(len(resistors_per_area[area_key])))
                        resistors_per_area[area_key][replace_idx] = answer_label
                    else:
                        resistors_per_area[area_key].append(answer_label)
                except Exception:
                    pass

            # Reflect answer item visually on one available resistor item of the same area.
            items = items_by_area.get(area, [])
            if not items:
                try:
                    items = items_by_area.get(int(area), [])
                except Exception:
                    items = []
            if items:
                item = choice(items)
                item.value = answer_label
                lbl = item.get(LabelComponent)
                if lbl:
                    lbl.value = answer_label
                self._trace(
                    cp,
                    f"item resposta injetado na area={area} item_id={getattr(item, 'id', 'n/a')} valor={answer_label}",
                )
            else:
                self._trace(cp, f"nenhum resistor item encontrado para area={area} (sem injeção visual)")

            self._log_gabarito(cp, expected)

        self._print_panel_answers(control_pannels)
        self.event_manager.post({"type": "solutions_done"})

    # ------------------------------------------------------
    # Runtime validation loop
    # ------------------------------------------------------
    def update(self, entity_mn, dt):
        _ = dt
        control_pannels: list[ControlPannel] = entity_mn.get_entities_by_class(ControlPannel)

        for cp in control_pannels:
            if cp.done or not cp.active:
                continue

            expected = cp.solution_value
            if not isinstance(expected, dict):
                self._trace(cp, "skip: painel sem gabarito (solution_value invalido)")
                continue

            target = expected.get("target")
            if not target:
                self._trace(cp, "skip: gabarito sem target")
                continue

            requested_types = self._parse_solution_types(cp.solution_type)
            if "power" not in requested_types:
                requested_types.add("power")
            if "resistance" not in requested_types:
                requested_types.add("resistance")

            circuit_data = self.circuit_manager.get_circuit_values(cp.name_file)
            if not circuit_data:
                panel_id = int(cp.pannel_id)
                reason = "sem circuit_data no CircuitManager"
                if self._last_skip_reason.get(panel_id) != reason:
                    self._last_skip_reason[panel_id] = reason
                    self._trace(cp, f"skip: {reason} (name_file={cp.name_file})")
                continue

            target_data = circuit_data.get(target)
            if not target_data:
                panel_id = int(cp.pannel_id)
                reason = f"target '{target}' ausente em circuit_data"
                if self._last_skip_reason.get(panel_id) != reason:
                    self._last_skip_reason[panel_id] = reason
                    self._trace(cp, f"skip: {reason} chaves={list(circuit_data.keys())}")
                continue

            try:
                ans_v = float(target_data["voltage"]["value"])
                ans_i = float(target_data["current"]["value"])
                ans_p = float(target_data["power"]["value"])
            except Exception:
                panel_id = int(cp.pannel_id)
                reason = "dados de medicao invalidos em target_data"
                if self._last_skip_reason.get(panel_id) != reason:
                    self._last_skip_reason[panel_id] = reason
                    self._trace(cp, f"skip: {reason} payload={target_data}")
                continue

            self._last_skip_reason.pop(int(cp.pannel_id), None)
            ans_r = abs(ans_v / ans_i) if abs(ans_i) > 1e-12 else float("inf")

            all_ok = True
            check_details = []
            if "power" in requested_types:
                exp_p = float(expected["power"])
                ok_p = self._float_equals_percent(ans_p, exp_p, self.tolerance_percent)
                check_details.append(("P", ans_p, exp_p, ok_p))
                all_ok = all_ok and ok_p

            if "resistance" in requested_types:
                exp_r = float(expected["resistance"])
                ok_r = self._float_equals_percent(ans_r, exp_r, self.tolerance_percent)
                check_details.append(("R", ans_r, exp_r, ok_r))
                all_ok = all_ok and ok_r

            if "voltage" in requested_types:
                exp_v = float(expected["voltage"])
                ok_v = self._float_equals_percent(ans_v, exp_v, self.tolerance_percent)
                check_details.append(("V", ans_v, exp_v, ok_v))
                all_ok = all_ok and ok_v

            if "current" in requested_types:
                exp_i = float(expected["current"])
                ok_i = self._float_equals_percent(ans_i, exp_i, self.tolerance_percent)
                check_details.append(("I", ans_i, exp_i, ok_i))
                all_ok = all_ok and ok_i

            panel_id = int(cp.pannel_id)
            previous_state = self._last_validation_state.get(panel_id)
            if previous_state is None or previous_state != all_ok:
                self._last_validation_state[panel_id] = all_ok
                self._log(
                    f"Painel {cp.pannel_id}: medido P={ans_p:.3g}W V={ans_v:.3g}V I={ans_i:.3g}A R={ans_r:.3g} Ohm "
                    f"| esperado P={expected['power']:.3g}W V={expected['voltage']:.3g}V I={expected['current']:.3g}A "
                    f"RL={expected['rl']:.3g} Ohm -> {'OK' if all_ok else 'FAIL'}"
                )
                if not all_ok:
                    live_document = str(self._panel_json_path(panel_id))
                    r1_label_now, r1_value_now = self._read_component_value(live_document, str(target))
                    self._trace(
                        cp,
                        f"R1 no circuito atual: label={r1_label_now} valor={self._fmt_ohm(r1_value_now)} arquivo={live_document}",
                    )
                    for name, measured, exp, ok in check_details:
                        err = self._percent_error(float(measured), float(exp))
                        self._trace(
                            cp,
                            f"check {name}: medido={measured:.6g} esperado={exp:.6g} "
                            f"erro={err:.3f}% tol={self.tolerance_percent:.3f}% -> {'OK' if ok else 'FAIL'}",
                        )
                    self._trace(
                        cp,
                        "contexto: "
                        f"target={target} name_file={cp.name_file} requested={sorted(requested_types)} "
                        f"answer={expected.get('answer_label')} RL={self._fmt_ohm(expected.get('rl'))}",
                    )

            if all_ok:
                cp.action()
                self._last_validation_state.pop(panel_id, None)
