from random import sample
from pathlib import Path

from pygame import Surface

from core.settings import *
from core.components.label_component import LabelComponent
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.thevenin_norton_validator_system import TheveninNortonValidatorSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.phantom_ai_system import PhantomAISystem
from core.systems.enemy_touch_game_over_system import EnemyTouchGameOverSystem
from core.systems.spider_web_system import SpiderWebSystem
from core.ui.widgets.stealth_timer_bar_widget import StealthTimerBarWidget
from core.components.animation_sprite import AnimateSprite
from core.components.freeze import Freeze
from core.localization.story_dialogue_catalog import StoryDialogueCatalog
from core.managers.language_service import LanguageService
from entities.dialogue_area import DialogueArea
from entities.itens.control_pannel import ControlPannel
from entities.itens.current_source_item import CurrentSourceItem
from entities.itens.old_paper import OldPaper
from entities.itens.resistor_item import ResistorItem
from entities.itens.voltage_source_item import VoltageSourceItem
from scenes.fases.generic_levels import BaseGenericLevel


class GenericLevel6(BaseGenericLevel):
    VOLTAGE_POOL = list(MAP_VOLTAGE_SOURCE_POOL)
    CURRENT_POOL = list(MAP_CURRENT_SOURCE_POOL)

    def __init__(self, screen: Surface, level_path: str, tolerance_percent: float = 2.0):
        self.tolerance_percent = tolerance_percent
        self.can_reset_pannels = True
        self.player_dead_by_enemy = False
        self.debug_panel_logs = True
        super().__init__(screen, level_path)

    def _log(self, message: str):
        if self.debug_panel_logs:
            print(f"[fase_6][level] {message}")

    def start(self):
        self.scene_manager.scene_preview = Path(self.level_path).stem
        self.player_dead_by_enemy = False
        self.phantom_ai_system.set_touch_triggered(False)
        self.enemy_touch_game_over_system.triggered = False
        if self.can_reset_pannels:
            self._reset_panels_runtime_state()
            self.circuit_manager.clear_phase(self.level_path)
            self.clear_all_pannels_json()
            self.can_reset_pannels = False

        self.set_subscribes()
        self.set_components_for_solutions()

        old_paper_list = self.entity_mn.get_entities_by_class(OldPaper)
        if old_paper_list:
            self.old_paper: OldPaper = old_paper_list[0]
            self.old_paper.on_active()

    def set_components_for_solutions(self):
        if not self.can_set_resistors:
            return

        self.can_set_resistors = False
        self.storage_circuit.remove_all_components()
        self._log("randomizando itens do mapa e calculando alvos Thevenin/Norton")
        resistors_per_area = self._assign_resistors_for_areas()
        sources_per_area = self._assign_sources_for_areas()
        self._post_solutions_event(resistors_per_area, sources_per_area)

    def _assign_resistors_for_areas(self) -> dict[int, list[str]]:
        resistors_items: list[ResistorItem] = self.entity_mn.get_entities_by_class(ResistorItem)
        resistor_values = self.circuit_manager.random_list_resistors(len(resistors_items))
        resistors_per_area: dict[int, list[str]] = {}

        for index, resistor_item in enumerate(resistors_items):
            value = resistor_values[index]
            label: LabelComponent = resistor_item.get(LabelComponent)
            if label:
                label.value = value
            resistor_item.value = value
            resistors_per_area.setdefault(resistor_item.area_id, []).append(value)

        return resistors_per_area

    def _assign_sources_for_areas(self) -> dict[int, dict[str, list[str]]]:
        voltage_items: list[VoltageSourceItem] = self.entity_mn.get_entities_by_class(VoltageSourceItem)
        current_items: list[CurrentSourceItem] = self.entity_mn.get_entities_by_class(CurrentSourceItem)

        voltage_values = self._build_random_values(self.VOLTAGE_POOL, len(voltage_items))
        current_values = self._build_random_values(self.CURRENT_POOL, len(current_items))

        sources_per_area: dict[int, dict[str, list[str]]] = {}

        for index, source_item in enumerate(voltage_items):
            value = voltage_values[index]
            label: LabelComponent = source_item.get(LabelComponent)
            if label:
                label.value = value
            source_item.value = value
            sources_per_area.setdefault(source_item.area_id, {}).setdefault("voltage", []).append(value)

        for index, source_item in enumerate(current_items):
            value = current_values[index]
            label: LabelComponent = source_item.get(LabelComponent)
            if label:
                label.value = value
            source_item.value = value
            sources_per_area.setdefault(source_item.area_id, {}).setdefault("current", []).append(value)

        return sources_per_area

    def _build_random_values(self, pool: list[str], amount: int) -> list[str]:
        values = sample(pool, k=min(len(pool), amount))
        while len(values) < amount:
            remaining = amount - len(values)
            values += sample(pool, k=min(len(pool), remaining))
        return values

    def _post_solutions_event(self, resistors_per_area: dict[int, list[str]], sources_per_area: dict[int, dict[str, list[str]]]):
        self._log("postando evento set_solutions")
        self.event_manager.post({"type": "set_solutions", "resistors": resistors_per_area, "sources": sources_per_area})

    def end(self):
        if self._should_skip_progress_reset_on_end():
            return
        self.storage_circuit.remove_all_components()
        self.storage_circuit.save_eletric_storage()
        self.clear_all_pannels_json()
        self.can_reset_pannels = True
        self.circuit_manager.clear_phase(self.level_path)

    def clear_all_pannels_json(self):
        amount_pannels = len(self.entity_mn.get_entities_by_class(ControlPannel))
        for i in range(amount_pannels):
            panel_name = f"pannel{i + 1}"
            json_base = path_in_circuitos(self.level_path)

            edited_json = json_base / f"{panel_name}.json"
            solution_json = json_base / f"{panel_name}_solution.json"
            if solution_json.exists():
                try:
                    edited_json.write_text(solution_json.read_text(encoding="utf-8"), encoding="utf-8")
                except OSError:
                    pass

    def set_systems(self):
        self.animation_system = AnimationSystem()
        self.area_trigger_system = AreaTriggerSystem()
        self.freeze_system = FreezeSystem()
        self.phantom_ai_system = PhantomAISystem(self.tile_map)
        self.spider_web_system = SpiderWebSystem()
        self.enemy_touch_game_over_system = EnemyTouchGameOverSystem()
        self.stealth_timer_widget = StealthTimerBarWidget(self.screen.get_size(), self.phantom_ai_system)
        self.ui_manager.add(self.stealth_timer_widget)

        self.circuit_validator_system = TheveninNortonValidatorSystem(level_path=self.level_path, tolerance_percent=self.tolerance_percent)

        self.systems.update(
            [
                self.freeze_system,
                self.phantom_ai_system,
                self.path_following_system,
                self.spider_web_system,
                self.enemy_touch_game_over_system,
                self.physics_system,
                self.animation_system,
                self.area_trigger_system,
                self.circuit_validator_system,
                self.render_system,
            ]
        )

    def set_subscribes(self):
        self.event_manager.subscribe("set_solutions", lambda event: self.circuit_validator_system.set_solutions(event, self.entity_mn))
        self.event_manager.subscribe("solutions_done", self.set_dialogue)
        self.event_manager.subscribe("player_invisible_to_enemies_started", self.phantom_ai_system.on_crystal_collected)
        self.event_manager.subscribe("cancel_reaggro_after_invisibility", self.phantom_ai_system.on_flask_collected)
        self.event_manager.subscribe("player_touched_enemy", self.on_player_touched_enemy)
        self.common_subscribes()

    def on_player_touched_enemy(self, event):
        _ = event
        if self.player_dead_by_enemy:
            return
        self.player_dead_by_enemy = True
        self.phantom_ai_system.set_touch_triggered(True)
        player = self.entity_mn.get_player()
        if not player:
            self.death_flow_manager.handle_player_death()
            return

        if player.has(Freeze):
            player.get(Freeze).active = True

        if player.has(AnimateSprite):
            anim: AnimateSprite = player.get(AnimateSprite)
            dir_name = "front"
            if hasattr(player, "_get_dir_name") and hasattr(player, "old_direction"):
                dir_name = player._get_dir_name(player.old_direction)
            anim.play(
                f"death_{dir_name}",
                reset=True,
                loop=False,
                on_finish=lambda: self.death_flow_manager.handle_player_death(),
            )
            return

        self.death_flow_manager.handle_player_death()

    def set_dialogue(self, event):
        _ = event
        dialogues = self.entity_mn.get_entities_by_class(DialogueArea)
        if not dialogues:
            return
        dialogue_area: DialogueArea = dialogues[0]
        catalog = StoryDialogueCatalog(LanguageService.get().get_current_language())

        text_list = []
        pannels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)

        for pannel in pannels:
            solution_values = pannel.solution_value
            if not isinstance(solution_values, dict):
                continue

            expected = solution_values.get("expected", {})
            mode = solution_values.get("mode")
            source_kind = expected.get("source_kind")
            if mode not in ("thevenin", "norton") or source_kind not in ("voltage", "current"):
                continue

            text_list.append(catalog.get_level6_panel_hint(pannel.pannel_id, mode))

        if text_list:
            dialogue_area.add_dialogue_text(text_list)
