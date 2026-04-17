from pathlib import Path
import pygame
import json

from core.components.animation_sprite import AnimateSprite
from core.components.freeze import Freeze
from core.components.dialogue import Dialogue
from core.components.label_component import LabelComponent
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.circuit_validators.max_power_transfer_validator_system import MaxPowerTransferValidatorSystem
from core.systems.enemy_touch_game_over_system import EnemyTouchGameOverSystem
from core.systems.freeze_system import FreezeSystem
from core.systems.phantom_ai_system import PhantomAISystem
from core.systems.spider_web_system import SpiderWebSystem
from core.ui.widgets.stealth_timer_bar_widget import StealthTimerBarWidget
from entities.dialogue_area import DialogueArea
from entities.itens.control_pannel import ControlPannel
from entities.itens.crystal_invisibility_item import CrystalInvisibilityItem
from entities.itens.current_source_item import CurrentSourceItem
from entities.itens.resistor_item import ResistorItem
from entities.itens.voltage_source_item import VoutageSourceItem
from core.components.position import Position
from core.components.sprite import Sprite
from entities.npcs.arquimedes import Arquimedes
from scenes.fases.max_power_level_base import BaseMaxPowerLevel
from core.settings import (
    FINAL_LEVEL_DEFAULT_PANEL_HOLD_SECONDS,
    FINAL_LEVEL_FINAL_FADE_SECONDS,
    FINAL_LEVEL_STORAGE_TYPE_BY_KIND,
    path_in_circuitos,
    path_in_ltspice,
)


class FinalLevel(BaseMaxPowerLevel):
    DEFAULT_PANEL_HOLD_SECONDS = FINAL_LEVEL_DEFAULT_PANEL_HOLD_SECONDS
    FINAL_FADE_SECONDS = FINAL_LEVEL_FINAL_FADE_SECONDS
    STORAGE_TYPE_BY_KIND = dict(FINAL_LEVEL_STORAGE_TYPE_BY_KIND)

    def __init__(self, screen, level_path, tolerance_percent: float = 2.0):
        self.panel_timers: dict[int, float] = {}
        self.collected_components_by_area: dict[int, list[dict]] = {}
        self.initial_components_by_area: dict[int, list[dict]] = {}
        self.crystal_respawn_queue: list[dict] = []
        self._panel_timer_font = None
        self._base_hooks_bound = False
        self._final_hooks_bound = False
        self._won = False
        self.player_dead_by_enemy = False
        super().__init__(screen, level_path, tolerance_percent)
        self._panel_timer_font = pygame.font.SysFont("consolas", 12, bold=True)

    def start(self):
        preserve_runtime = bool(getattr(self, "_preserve_runtime_state_on_next_start", False))
        if not preserve_runtime:
            self.panel_timers.clear()
            self.collected_components_by_area.clear()
            self.initial_components_by_area.clear()
            self.crystal_respawn_queue.clear()
        self._won = False
        self.player_dead_by_enemy = False
        if hasattr(self, "phantom_ai_system"):
            self.phantom_ai_system.set_touch_triggered(False)
        if hasattr(self, "enemy_touch_game_over_system"):
            self.enemy_touch_game_over_system.triggered = False
        super().start()
        self._snapshot_initial_components()
        self._configure_final_dialogues()

    def end(self):
        if self._should_skip_progress_reset_on_end():
            return
        self.panel_timers.clear()
        self.collected_components_by_area.clear()
        self.initial_components_by_area.clear()
        self.crystal_respawn_queue.clear()
        self._won = False
        super().end()

    def set_subscribes(self):
        # Scene transitions clear EventManager listeners. Rebind on every start.
        super().set_subscribes()

        self.event_manager.unsubscribe("player_invisible_to_enemies_started", self.phantom_ai_system.on_crystal_collected)
        self.event_manager.unsubscribe("cancel_reaggro_after_invisibility", self.phantom_ai_system.on_flask_collected)
        self.event_manager.unsubscribe("player_touched_enemy", self.on_player_touched_enemy)
        self.event_manager.unsubscribe("resistor_collected", self._on_resistor_collected)
        self.event_manager.unsubscribe("current_source_collected", self._on_current_source_collected)
        self.event_manager.unsubscribe("voltage_source_collected", self._on_voltage_source_collected)
        self.event_manager.unsubscribe("crystal_invisibility_collected", self._on_crystal_collected)
        self.event_manager.unsubscribe("panel_solved", self._on_final_panel_solved_gain_bombs)

        self.event_manager.subscribe("player_invisible_to_enemies_started", self.phantom_ai_system.on_crystal_collected)
        self.event_manager.subscribe("cancel_reaggro_after_invisibility", self.phantom_ai_system.on_flask_collected)
        self.event_manager.subscribe("player_touched_enemy", self.on_player_touched_enemy)
        self.event_manager.subscribe("resistor_collected", self._on_resistor_collected)
        self.event_manager.subscribe("current_source_collected", self._on_current_source_collected)
        self.event_manager.subscribe("voltage_source_collected", self._on_voltage_source_collected)
        self.event_manager.subscribe("crystal_invisibility_collected", self._on_crystal_collected)
        self.event_manager.subscribe("panel_solved", self._on_final_panel_solved_gain_bombs)

    def set_systems(self):
        self.animation_system = AnimationSystem()
        self.area_trigger_system = AreaTriggerSystem()
        self.freeze_system = FreezeSystem()
        self.phantom_ai_system = PhantomAISystem(self.tile_map)
        self.spider_web_system = SpiderWebSystem()
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
                self.spider_web_system,
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

    def render(self):
        super().render()
        self._draw_panel_timers_overlay()

    def _draw_panel_timers_overlay(self):
        panels: list[ControlPannel] = self.entity_mn.get_entities_by_class(ControlPannel)
        if not panels:
            return

        for panel in panels:
            if not panel.done:
                continue

            panel_id = panel.pannel_id
            remaining = float(self.panel_timers.get(panel_id, 0.0))
            hold_time = float(getattr(panel, "solved_hold_seconds", self.DEFAULT_PANEL_HOLD_SECONDS))
            if hold_time <= 0:
                hold_time = self.DEFAULT_PANEL_HOLD_SECONDS

            ratio = max(0.0, min(1.0, remaining / hold_time))
            if not panel.has(Sprite):
                continue
            spr = panel.get(Sprite)

            scaled_rect = pygame.Rect(
                int(spr.rect.x * self.scale),
                int(spr.rect.y * self.scale),
                int(spr.rect.width * self.scale),
                int(spr.rect.height * self.scale),
            )
            draw_rect = self.camera.apply(scaled_rect)

            bar_w = max(38, int(draw_rect.width * 1.2))
            bar_h = max(6, int(5 * self.scale))
            bar_x = int(draw_rect.centerx - bar_w / 2)
            bar_y = int(draw_rect.top - (10 + bar_h))

            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            fill_w = int(bar_w * ratio)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)

            if ratio > 0.55:
                fill_color = (82, 201, 112)
            elif ratio > 0.25:
                fill_color = (236, 188, 79)
            else:
                fill_color = (222, 87, 87)

            pygame.draw.rect(self.screen, (18, 18, 20), bg_rect, border_radius=3)
            if fill_w > 0:
                pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=3)
            pygame.draw.rect(self.screen, (230, 230, 230), bg_rect, width=1, border_radius=3)

            # Mantem apenas a barra de progresso visual (sem label de tempo).

    def _configure_final_dialogues(self):
        lines = [
    "Arquimedes: Kevin, seu pai correu para o topo com o Coração de Fóton.",
    "Arquimedes: Ele quer apagar o farol para forçar a linha do tempo da sua avó.",
    "Arquimedes: Esta sala é o último selo. São quatro painéis ativos ao mesmo tempo.",
    "Arquimedes: Cada painel resolvido dura pouco. Se o tempo acabar, ele reinicia.",
    "Arquimedes: Dica: em cada painel, foque no resistor alvo R1 e busque máxima transferência.",
    "Arquimedes: Primeiro encontre o equivalente de Thévenin nos terminais da carga.",
    "Arquimedes: Regra-chave: para máxima potência, ajuste RL para ficar aproximadamente igual a Rth.",
    "Arquimedes: O painel cobra potência e resistência. Confira os dois antes de fechar.",
    "Arquimedes: Estratégia: deixe componentes perto dos painéis e resolva em sequência sem parar.",
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
        super()._register_collected_component(event, kind)

        try:
            area_id = int(event.get("area_id", -1))
        except (TypeError, ValueError):
            area_id = -1
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

    def _on_final_panel_solved_gain_bombs(self, event: dict):
        _ = event
        reward_amount = 2
        self.bomb_manager.max_bombs += reward_amount
        self.bomb_manager.remaining_bombs += reward_amount
        self.audio_manager.play_sfx("sfx/electric_pickup.wav", volume=0.84)

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
            self.scene_manager.start_fade("ending_lighthouse", self.FINAL_FADE_SECONDS)
            return

        # Remove timers de paineis atualmente "errados".
        for panel in panels:
            if not panel.done:
                self.panel_timers.pop(panel.pannel_id, None)

        solved_panels = [panel for panel in panels if panel.done]
        if not solved_panels:
            return

        # Novo comportamento da fase final:
        # quando um novo painel e resolvido, o timer dele inicia
        # e os timers dos outros paineis resolvidos voltam ao valor cheio.
        newly_solved = [panel for panel in solved_panels if panel.pannel_id not in self.panel_timers]
        if newly_solved:
            for panel in solved_panels:
                self.panel_timers[panel.pannel_id] = self._panel_hold_time(panel)
            return

        expired_panels: list[ControlPannel] = []
        for panel in solved_panels:
            panel_id = panel.pannel_id
            current = self.panel_timers.get(panel_id, self._panel_hold_time(panel))
            current -= dt
            self.panel_timers[panel_id] = current
            if current <= 0:
                expired_panels.append(panel)

        for panel in expired_panels:
            self._reset_panel(panel)

    def _panel_hold_time(self, panel: ControlPannel) -> float:
        hold_time = float(getattr(panel, "solved_hold_seconds", self.DEFAULT_PANEL_HOLD_SECONDS))
        if hold_time <= 0:
            hold_time = self.DEFAULT_PANEL_HOLD_SECONDS
        return hold_time

    def _reset_panel(self, panel: ControlPannel):
        area_id = int(panel.component_for_area)
        panel_id = int(panel.pannel_id)
        panel.done = False
        panel.panel_status.set_done(False)
        self.panel_timers.pop(panel_id, None)
        # Ordem obrigatoria: devolver itens ao mapa e retirar do storage antes do reroll.
        self._respawn_components_for_area(area_id, panel_id)
        self._restore_panel_json(panel_id)
        self.circuit_manager.clear_circuit(panel.name_file)
        self._reroll_panel_area(area_id, panel_id)

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

    def _respawn_components_for_area(self, area_id: int, panel_id: int | None = None):
        collected = self.collected_components_by_area.pop(area_id, [])
        used_on_panel = self._extract_dropped_components_from_panel(panel_id, area_id) if panel_id else []
        slots = self.initial_components_by_area.get(int(area_id), [])
        if not slots:
            return

        value_pool_by_kind: dict[str, list[str]] = {}
        for data in collected + used_on_panel:
            kind = str(data.get("kind", ""))
            value = str(data.get("value", ""))
            if not kind or not value:
                continue
            value_pool_by_kind.setdefault(kind, []).append(value)

        to_respawn: list[dict] = []
        for slot in slots:
            kind = str(slot.get("kind", ""))
            if not kind:
                continue
            pool = value_pool_by_kind.get(kind, [])
            restored_value = pool.pop(0) if pool else str(slot.get("value", ""))
            to_respawn.append(
                {
                    "kind": kind,
                    "area_id": int(area_id),
                    "value": restored_value,
                    "x": float(slot.get("x", 0.0)),
                    "y": float(slot.get("y", 0.0)),
                }
            )

        if not to_respawn:
            return

        # Reset deterministico da area: remove os itens atuais e recria todos os slots.
        self._remove_area_items_from_map(area_id)
        self.storage_circuit.reload_storage()
        for data in to_respawn:
            self._spawn_component(data)
            self._remove_component_from_storage(data["kind"], data["value"])
        self.storage_circuit.save_eletric_storage()

    def _remove_area_items_from_map(self, area_id: int):
        for cls in (ResistorItem, CurrentSourceItem, VoutageSourceItem):
            for entity in list(self.entity_mn.get_entities_by_class(cls)):
                if int(getattr(entity, "area_id", -1)) != int(area_id):
                    continue
                self.entity_mn.remove_entity(entity)

    def _reroll_panel_area(self, area_id: int, panel_id: int):
        area_resistors: list[ResistorItem] = [
            item for item in self.entity_mn.get_entities_by_class(ResistorItem)
            if int(item.area_id) == int(area_id)
        ]
        new_resistor_values = self.circuit_manager.random_list_resistors(len(area_resistors)) if area_resistors else []
        for idx, resistor_item in enumerate(area_resistors):
            if idx >= len(new_resistor_values):
                break
            new_value = str(new_resistor_values[idx])
            resistor_item.value = new_value
            if resistor_item.has(LabelComponent):
                resistor_item.get(LabelComponent).value = new_value

        resistors_payload = {
            int(area_id): [str(item.value) for item in area_resistors]
        }
        sources_payload: dict[int, dict[str, list[str]]] = {}

        for voltage_item in self.entity_mn.get_entities_by_class(VoutageSourceItem):
            if int(voltage_item.area_id) != int(area_id):
                continue
            sources_payload.setdefault(int(area_id), {}).setdefault("voltage", []).append(str(voltage_item.value))

        for current_item in self.entity_mn.get_entities_by_class(CurrentSourceItem):
            if int(current_item.area_id) != int(area_id):
                continue
            sources_payload.setdefault(int(area_id), {}).setdefault("current", []).append(str(current_item.value))

        self.event_manager.post(
            {
                "type": "set_solutions",
                "panel_ids": [int(panel_id)],
                "resistors": resistors_payload,
                "sources": sources_payload,
            }
        )

    def _snapshot_initial_components(self):
        # Snapshot imutavel dos slots de itens vindo do TMX da fase.
        # Isso evita perder referencias quando a cena e recarregada com itens ja coletados.
        self.initial_components_by_area = {}
        kind_by_name = {
            "resistor": "resistor",
            "current_source": "current_source",
            "voltage_source": "voltage_source",
        }

        tmx_data = getattr(self.tile_map, "tmx_data", None)
        if tmx_data is None:
            return

        for layer in getattr(tmx_data, "objectgroups", []):
            if str(getattr(layer, "name", "")).lower() != "itens":
                continue
            for obj in layer:
                obj_name = str(getattr(obj, "name", "")).lower()
                kind = kind_by_name.get(obj_name)
                if not kind:
                    continue

                props = getattr(obj, "properties", {}) or {}
                try:
                    area_id = int(props.get("area", -1))
                except Exception:
                    area_id = -1
                if area_id < 0:
                    continue

                value = str(props.get("valor", ""))
                self.initial_components_by_area.setdefault(area_id, []).append(
                    {
                        "kind": kind,
                        "area_id": area_id,
                        "value": value,
                        "x": float(getattr(obj, "x", 0.0)),
                        "y": float(getattr(obj, "y", 0.0)),
                    }
                )

    def _get_missing_components_for_area(self, area_id: int) -> list[dict]:
        expected = self.initial_components_by_area.get(area_id, [])
        if not expected:
            return []
        return [data for data in expected if not self._is_component_present_on_map(data)]

    @staticmethod
    def _component_key(data: dict) -> tuple:
        return (
            str(data.get("kind", "")),
            int(data.get("area_id", -1)),
            round(float(data.get("x", 0.0)), 3),
            round(float(data.get("y", 0.0)), 3),
        )

    @staticmethod
    def _map_entity_type_to_kind(entity_type: str) -> str | None:
        return {
            "Resistor": "resistor",
            "CurrentSource": "current_source",
            "VoutageSource": "voltage_source",
        }.get(str(entity_type))

    def _extract_dropped_components_from_panel(self, panel_id: int, area_id: int) -> list[dict]:
        panel_json = path_in_circuitos(self.level_path, f"pannel{panel_id}.json")
        if not panel_json.exists():
            return []
        try:
            entities = json.loads(panel_json.read_text(encoding="utf-8"))
        except Exception:
            return []

        dropped_components: list[dict] = []
        for entity in entities:
            kind = self._map_entity_type_to_kind(entity.get("entity_type", ""))
            if not kind:
                continue
            components = entity.get("components", [])
            dropped = next((c for c in components if c.get("type") == "Dropped"), None)
            if not dropped or not bool(dropped.get("can_dropped", False)):
                continue
            label = next((c for c in components if c.get("type") == "LabelComponent"), None)
            if not label or not label.get("value"):
                continue
            restored = self._allocate_respawn_slot(area_id, kind, str(label.get("value")))
            if restored:
                dropped_components.append(restored)
        return dropped_components

    def _allocate_respawn_slot(self, area_id: int, kind: str, value: str) -> dict | None:
        expected = self.initial_components_by_area.get(int(area_id), [])
        missing = [data for data in expected if data.get("kind") == kind and not self._is_component_present_on_map(data)]
        if not missing:
            return None

        # Prioriza slot que ja tinha o mesmo valor; se nao houver, usa o primeiro faltando.
        selected = next((data for data in missing if str(data.get("value")) == str(value)), missing[0])
        return {
            "kind": kind,
            "area_id": int(area_id),
            "value": str(value),
            "x": float(selected.get("x", 0.0)),
            "y": float(selected.get("y", 0.0)),
        }

    def _is_component_present_on_map(self, data: dict) -> bool:
        kind = data.get("kind")
        area_id = int(data.get("area_id", -1))
        x = round(float(data.get("x", 0.0)), 3)
        y = round(float(data.get("y", 0.0)), 3)

        class_by_kind = {
            "resistor": ResistorItem,
            "current_source": CurrentSourceItem,
            "voltage_source": VoutageSourceItem,
        }
        cls = class_by_kind.get(kind)
        if cls is None:
            return False

        for entity in self.entity_mn.get_entities_by_class(cls):
            if int(getattr(entity, "area_id", -1)) != area_id:
                continue
            if not entity.has(Position):
                continue
            pos: Position = entity.get(Position)
            if round(float(pos.x), 3) == x and round(float(pos.y), 3) == y:
                return True
        return False

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
