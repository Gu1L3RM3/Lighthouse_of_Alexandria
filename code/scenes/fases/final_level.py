from pathlib import Path

from core.components.animation_sprite import AnimateSprite
from core.components.freeze import Freeze
from core.components.dialogue import Dialogue
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.max_power_transfer_validator_system import MaxPowerTransferValidatorSystem
from core.systems.enemy_touch_game_over_system import EnemyTouchGameOverSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.light_system import LightSystem
from core.systems.phantom_ai_system import PhantomAISystem
from core.ui.widgets.stealth_timer_bar_widget import StealthTimerBarWidget
from entities.dialogue_area import DialogueArea
from entities.itens.control_pannel import ControlPannel
from entities.itens.crystal_invisibility_item import CrystalInvisibilityItem
from entities.itens.current_source_item import CurrentSourceItem
from entities.itens.resistor_item import ResistorItem
from entities.itens.voltage_source_item import VoutageSourceItem
from entities.npcs.arquimedes import Arquimedes
from scenes.fases.max_power_level_base import BaseMaxPowerLevel
from core.settings import path_in_circuitos, path_in_ltspice


class FinalLevel(BaseMaxPowerLevel):
    DEFAULT_PANEL_HOLD_SECONDS = 45.0
    FINAL_FADE_SECONDS = 0.8
    STORAGE_TYPE_BY_KIND = {
        "resistor": "Resistor",
        "current_source": "CurrentSource",
        "voltage_source": "VoutageSource",
    }

    def __init__(self, screen, level_path, tolerance_percent: float = 2.0):
        self.panel_timers: dict[int, float] = {}
        self.collected_components_by_area: dict[int, list[dict]] = {}
        self.crystal_respawn_queue: list[dict] = []
        self._base_hooks_bound = False
        self._final_hooks_bound = False
        self._won = False
        self.player_dead_by_enemy = False
        super().__init__(screen, level_path, tolerance_percent)

    def start(self):
        self.panel_timers.clear()
        self.collected_components_by_area.clear()
        self.crystal_respawn_queue.clear()
        self._won = False
        self.player_dead_by_enemy = False
        if hasattr(self, "phantom_ai_system"):
            self.phantom_ai_system.set_touch_triggered(False)
        if hasattr(self, "enemy_touch_game_over_system"):
            self.enemy_touch_game_over_system.triggered = False
        super().start()
        self._configure_final_dialogues()

    def end(self):
        self.panel_timers.clear()
        self.collected_components_by_area.clear()
        self.crystal_respawn_queue.clear()
        self._won = False
        super().end()

    def set_subscribes(self):
        if not self._base_hooks_bound:
            super().set_subscribes()
            self._base_hooks_bound = True
        if self._final_hooks_bound:
            return
        self.event_manager.subscribe("player_invisible_to_enemies_started", self.phantom_ai_system.on_crystal_collected)
        self.event_manager.subscribe("cancel_reaggro_after_invisibility", self.phantom_ai_system.on_flask_collected)
        self.event_manager.subscribe("player_touched_enemy", self.on_player_touched_enemy)
        self.event_manager.subscribe("resistor_collected", self._on_resistor_collected)
        self.event_manager.subscribe("current_source_collected", self._on_current_source_collected)
        self.event_manager.subscribe("voltage_source_collected", self._on_voltage_source_collected)
        self.event_manager.subscribe("crystal_invisibility_collected", self._on_crystal_collected)
        self._final_hooks_bound = True

    def set_systems(self):
        self.animation_system = AnimationSystem()
        self.area_trigger_system = AreaTriggerSystem()
        self.freeze_system = FreezeSystem()
        self.light_system = LightSystem(self.screen, self.camera, debug=False, enabled=True, ambient_alpha=0)
        self.phantom_ai_system = PhantomAISystem(self.tile_map)
        self.enemy_touch_game_over_system = EnemyTouchGameOverSystem()
        self.stealth_timer_widget = StealthTimerBarWidget(self.screen.get_size(), self.phantom_ai_system)
        self.ui_manager.add(self.stealth_timer_widget)
        self.circuit_validator_system = MaxPowerTransferValidatorSystem(
            level_path=self.level_path,
            tolerance_percent=self.tolerance_percent,
        )

        self.systems.update(
            [
                self.freeze_system,
                self.phantom_ai_system,
                self.path_following_system,
                self.enemy_touch_game_over_system,
                self.physics_system,
                self.animation_system,
                self.area_trigger_system,
                self.circuit_validator_system,
                self.render_system,
            ]
        )

    def update(self, dt):
        super().update(dt)
        if self._won:
            return
        self._update_panel_timers(dt)
        self._update_crystal_respawns(dt)

    def _configure_final_dialogues(self):
        lines = [
            "Arquimedes: Kevin, seu pai correu para o topo com o Coracao de Foton.",
            "Arquimedes: Ele quer apagar o farol para forcar a linha do tempo da sua avo.",
            "Arquimedes: Esta sala e o ultimo selo. Sao quatro paineis ativos ao mesmo tempo.",
            "Arquimedes: Cada painel resolvido dura pouco. Se o tempo acabar, ele reinicia.",
            "Arquimedes: Dica: em cada painel, foque no resistor alvo R1 e busque maxima transferencia.",
            "Arquimedes: Primeiro encontre o equivalente de Thevenin nos terminais da carga.",
            "Arquimedes: Regra-chave: para maxima potencia, ajuste RL para ficar aproximadamente igual a Rth.",
            "Arquimedes: O painel cobra potencia e resistencia. Confira os dois antes de fechar.",
            "Arquimedes: Estrategia: deixe componentes perto dos paineis e resolva em sequencia sem parar.",
            "Arquimedes: Se falharmos aqui, Alexandria cai antes do amanhecer.",
        ]

        for arquimedes in self.entity_mn.get_entities_by_class(Arquimedes):
            if not arquimedes.has(Dialogue):
                continue
            dialogue: Dialogue = arquimedes.get(Dialogue)
            dialogue.lines = lines[:]
            dialogue.active_status = True
            dialogue.auto_start = False
            dialogue.triggered = False

        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            if not area.has(Dialogue):
                continue
            dialogue: Dialogue = area.get(Dialogue)
            area.list_dialogue = lines[:]
            dialogue.lines = lines[:]
            dialogue.active_status = True
            dialogue.auto_start = False
            dialogue.triggered = False

    def _on_resistor_collected(self, event: dict):
        self._register_collected_component(event, "resistor")

    def _on_current_source_collected(self, event: dict):
        self._register_collected_component(event, "current_source")

    def _on_voltage_source_collected(self, event: dict):
        self._register_collected_component(event, "voltage_source")

    def _register_collected_component(self, event: dict, kind: str):
        area_id = int(event.get("area_id", -1))
        value = str(event.get("value", ""))
        spawn_x = float(event.get("spawn_x", 0))
        spawn_y = float(event.get("spawn_y", 0))
        if area_id < 0 or not value:
            return

        self.collected_components_by_area.setdefault(area_id, []).append(
            {
                "kind": kind,
                "area_id": area_id,
                "value": value,
                "x": spawn_x,
                "y": spawn_y,
            }
        )

    def _on_crystal_collected(self, event: dict):
        self.crystal_respawn_queue.append(
            {
                "remaining": float(event.get("respawn_delay", 20.0)),
                "x": float(event.get("spawn_x", 0)),
                "y": float(event.get("spawn_y", 0)),
                "duration": float(event.get("duration", 6.0)),
                "respawn_delay": float(event.get("respawn_delay", 20.0)),
            }
        )

    def _update_crystal_respawns(self, dt: float):
        still_waiting: list[dict] = []
        for entry in self.crystal_respawn_queue:
            entry["remaining"] -= dt
            if entry["remaining"] > 0:
                still_waiting.append(entry)
                continue

            props = {
                "duration": entry["duration"],
                "respawn_delay": entry["respawn_delay"],
                "tmx_file": self.tile_map.tmx_file,
            }
            crystal = CrystalInvisibilityItem(entry["x"], entry["y"], True, props)
            self.entity_mn.add_entity(crystal)

        self.crystal_respawn_queue = still_waiting

    def _update_panel_timers(self, dt: float):
        panels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        if not panels:
            return

        if all(panel.done for panel in panels):
            self._won = True
            self.scene_manager.start_fade("home_scene", self.FINAL_FADE_SECONDS)
            return

        for panel in panels:
            if panel.done and panel.pannel_id not in self.panel_timers:
                hold_time = float(getattr(panel, "solved_hold_seconds", self.DEFAULT_PANEL_HOLD_SECONDS))
                if hold_time <= 0:
                    hold_time = self.DEFAULT_PANEL_HOLD_SECONDS
                self.panel_timers[panel.pannel_id] = hold_time
            elif not panel.done:
                self.panel_timers.pop(panel.pannel_id, None)

        for panel in panels:
            if not panel.done:
                continue
            panel_id = panel.pannel_id
            self.panel_timers[panel_id] = self.panel_timers.get(panel_id, self.DEFAULT_PANEL_HOLD_SECONDS) - dt
            if self.panel_timers[panel_id] <= 0:
                self._reset_panel(panel)

    def _reset_panel(self, panel: ControlPannel):
        panel.done = False
        panel.panel_status.set_done(False)
        self.panel_timers.pop(panel.pannel_id, None)
        self._restore_panel_json(panel.pannel_id)
        self.circuit_manager.clear_circuit(panel.name_file)
        self._respawn_components_for_area(int(panel.component_for_area))

    def _restore_panel_json(self, panel_id: int):
        panel_name = f"pannel{panel_id}"
        json_base = path_in_circuitos(self.level_path)
        netlist_base = path_in_ltspice(self.level_path)

        edited_json = json_base / f"{panel_name}.json"
        solution_json = json_base / f"{panel_name}_solution.json"
        if solution_json.exists():
            try:
                edited_json.write_text(solution_json.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

        edited_net = netlist_base / f"{panel_name}.net"
        solution_net = netlist_base / f"{panel_name}_solution.net"
        if solution_net.exists():
            try:
                edited_net.write_text(solution_net.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

    def _respawn_components_for_area(self, area_id: int):
        collected = self.collected_components_by_area.pop(area_id, [])
        if not collected:
            return

        self.storage_circuit.reload_storage()
        for data in collected:
            self._spawn_component(data)
            self._remove_component_from_storage(data["kind"], data["value"])
        self.storage_circuit.save_eletric_storage()

    def _spawn_component(self, data: dict):
        kind = data["kind"]
        item_class = {
            "resistor": ResistorItem,
            "current_source": CurrentSourceItem,
            "voltage_source": VoutageSourceItem,
        }.get(kind)
        if item_class is None:
            return

        props = {
            "valor": data["value"],
            "area": str(data["area_id"]),
            "tmx_file": self.tile_map.tmx_file,
        }
        entity = item_class(data["x"], data["y"], True, props)
        self.entity_mn.add_entity(entity)

    def _remove_component_from_storage(self, kind: str, value: str):
        storage_type = self.STORAGE_TYPE_BY_KIND.get(kind)
        if not storage_type:
            return

        storage_data = self.storage_circuit.storage_circuit.get(storage_type, {})
        if storage_data.get(value, 0) <= 0:
            return
        self.storage_circuit.remove_component(storage_type, value)

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
