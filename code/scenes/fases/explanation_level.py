from __future__ import annotations

import re
from pathlib import Path
import pygame

from pygame import Event, Surface

from core.settings import *
from scenes.base_scene import BaseScene
from core.components.dialogue import Dialogue
from entities.dialogue_area import DialogueArea
from entities.itens.key import Key
from entities.itens.old_paper import OldPaper
from entities.animated_tiles.door import Door
from core.components.area_trigger import AreaTrigger
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.freeze_system import FreezeSystem
from core.managers.attention_manager import AttentionManager
from core.managers.scene_manager import SceneManager
from core.ui.dialogue_interaction_hud_controller import DialogueInteractionHUDController
from core.ui.widgets.dialogue_image_sequence import DialogueImageSequenceWidget
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType


class BaseExplanationLevel(BaseScene):
    def __init__(
        self,
        screen: Surface,
        map_path: str,
        next_scene: str,
        scale: int = 2,
    ):
        self.map_path = map_path
        loader = TileMapLoader()
        self.tile_map = loader.load(f"fases/{map_path}.tmx")
        self.scale = scale

        super().__init__(
            screen,
            self.tile_map.map_width * self.scale,
            self.tile_map.map_height * self.scale,
        )

        self.map_renderer = MapRenderer(self.tile_map, self.camera, self.screen, self.scale)

        self.set_ui()
        self.set_map()
        self.set_systems()

        self.camera.scale = self.scale
        self.player = self.entity_mn.get_player()
        self.camera.follow = self.player

        self._disable_old_papers()

        self.key: Key | None = self._get_first_entity(Key)
        self.door: Door | None = self._get_first_entity(Door)
        if self.key:
            self.key.on_deactive()
        if self.door:
            self.door.next_scene = next_scene

        self.last_dialogue_name = self._get_last_dialogue_name()
        self.dialogue_image_sequences = self.get_dialogue_image_sequences()
        self._warned_missing_explanation_images: set[str] = set()
        self._validate_dialogue_image_sequences()
        self._active_dialogue_image_widget: DialogueImageSequenceWidget | None = None
        self.attention_manager = AttentionManager(self.entity_mn)
        self.dialogue_hud = DialogueInteractionHUDController(
            self.entity_mn,
            self.dialog_system,
            self.interaction_key_widget,
        )

    def set_ui(self):
        top_button_gap = 20
        top_button_step = 142 + top_button_gap
        menu_x = self.screen.get_width() - 92
        help_x = menu_x - top_button_step
        idle = pygame.transform.scale(self.resources.load_image("buttons/short.png"), (142, 78))
        pressed = pygame.transform.scale(self.resources.load_image("buttons/short_pressed.png"), (142, 78))
        self.menu_button = Button(
            init_surface=idle,
            surface_pressed=pressed,
            pos_center=(menu_x, 44),
            click_type=ClickType.AFTER_RELEASED,
            action=lambda: SceneManager.get().open_menu(0.35),
            text="MENU",
            font_size=11,
            color_text=(245, 230, 170),
        )
        self.help_button = Button(
            init_surface=idle.copy(),
            surface_pressed=pressed.copy(),
            pos_center=(help_x, 44),
            click_type=ClickType.AFTER_RELEASED,
            action=lambda: SceneManager.get().open_help(0.35),
            text="HELP",
            font_size=11,
            color_text=(245, 230, 170),
        )
        self.ui_manager.add(self.menu_button, self.help_button)
        self.interaction_key_widget = InteractionKeyWidget(self.screen.get_size(), label="ENTRAR")
        self.ui_manager.add(self.interaction_key_widget)

    def set_map(self):
        spawner = MapEntitySpawner()
        spawner.spawn_entities(self.tile_map, self.entity_mn)
        self.player = self.entity_mn.get_player()
        self.physics_system.cache_static_colliders(self.entity_mn)

    def set_systems(self):
        self.animation_system = AnimationSystem()
        self.area_trigger_system = AreaTriggerSystem()
        self.freeze_system = FreezeSystem()

        self.systems.update(
            [
                self.freeze_system,
                self.physics_system,
                self.animation_system,
                self.area_trigger_system,
                self.render_system,
            ]
        )

    def start(self):
        self.event_manager.post({"type": "release_freeze"})
        self.set_subscribes()

    def set_subscribes(self):
        self.event_manager.subscribe("request_freeze", self.freeze_system.request_freeze)
        self.event_manager.subscribe("release_freeze", self.freeze_system.release_freeze)
        self.event_manager.subscribe("dialogue_end", self.attention_manager.set_attention_position_after_event)
        self.event_manager.subscribe("dialogue_end", self.attention_manager.set_dialogue_area_after_event)
        self.event_manager.subscribe("dialogue_end", self._activate_key_if_last_dialogue)
        self.event_manager.subscribe("dialogue_start", self._start_dialogue_image_sequence)
        self.event_manager.subscribe("dialogue_end", self._stop_dialogue_image_sequence)
        self.event_manager.subscribe("kill_entity", self.kill_entity_event)

        if self.door:
            self.event_manager.subscribe("get_key", self.door.open)

    def _disable_old_papers(self):
        old_papers = self.entity_mn.get_entities_by_class(OldPaper)
        for paper in old_papers:
            trigger = paper.get(AreaTrigger)
            if trigger:
                trigger.active = False

    def _get_last_dialogue_name(self) -> str | None:
        dialogues = self.entity_mn.get_entities_by_class(DialogueArea)
        indices: list[int] = []
        for area in dialogues:
            match = re.match(r"dialog_(\d+)$", area.name)
            if match:
                indices.append(int(match.group(1)))

        if not indices:
            return None

        return f"dialog_{max(indices)}"

    def _get_first_entity(self, cls):
        entities = self.entity_mn.get_entities_by_class(cls)
        return entities[0] if entities else None

    def get_dialogue_image_sequences(self) -> dict:
        return {}

    def _extract_dialogue_media_entry(self, media_entry) -> tuple[list[str], list[str]]:
        if isinstance(media_entry, dict):
            images = list(media_entry.get("images", []))
            captions = list(media_entry.get("captions", []))
        else:
            images = list(media_entry or [])
            captions = []

        images = [str(path) for path in images if path]
        captions = [str(text) for text in captions]
        return images, captions

    def _normalize_dialogue_media(
        self,
        dialogue: Dialogue,
        image_paths: list[str],
        captions: list[str],
    ) -> tuple[list[str], list[str]]:
        if not image_paths:
            return [], []

        target_len = max(1, len(dialogue.lines))
        if len(image_paths) < target_len:
            image_paths.extend([image_paths[-1]] * (target_len - len(image_paths)))
        elif len(image_paths) > target_len:
            image_paths = image_paths[:target_len]

        if len(captions) < target_len:
            captions.extend([""] * (target_len - len(captions)))
        elif len(captions) > target_len:
            captions = captions[:target_len]

        return image_paths, captions

    def _warn_missing_explanation_image(self, relative_path: str):
        if relative_path in self._warned_missing_explanation_images:
            return
        self._warned_missing_explanation_images.add(relative_path)
        print(f"[BaseExplanationLevel] Imagem de explicacao nao encontrada: {relative_path}")

    def _validate_dialogue_image_sequences(self):
        for dialogue_name, media_entry in self.dialogue_image_sequences.items():
            image_paths, captions = self._extract_dialogue_media_entry(media_entry)
            if not image_paths:
                print(
                    f"[BaseExplanationLevel] Sequencia vazia em {self.map_path}::{dialogue_name}"
                )
                continue
            if captions and len(captions) != len(image_paths):
                print(
                    f"[BaseExplanationLevel] Legendas e imagens com tamanhos diferentes em "
                    f"{self.map_path}::{dialogue_name} ({len(captions)} vs {len(image_paths)})."
                )
            for relative_path in image_paths:
                full_path = Path(ASSETS_DIR) / "images" / relative_path
                if not full_path.exists():
                    self._warn_missing_explanation_image(relative_path)

    def _start_dialogue_image_sequence(self, event):
        entity = event.get("entity")
        if not isinstance(entity, DialogueArea):
            return

        media_entry = self.dialogue_image_sequences.get(entity.name)
        image_paths, captions = self._extract_dialogue_media_entry(media_entry)
        if not image_paths:
            return

        dialogue: Dialogue = entity.get(Dialogue)
        image_paths, captions = self._normalize_dialogue_media(dialogue, image_paths, captions)
        self._active_dialogue_image_widget = DialogueImageSequenceWidget(
            dialogue_component=dialogue,
            image_paths=image_paths,
            captions=captions,
        )
        self.ui_manager.add(self._active_dialogue_image_widget)

    def _stop_dialogue_image_sequence(self, _event):
        if not self._active_dialogue_image_widget:
            return
        if self._active_dialogue_image_widget in self.ui_manager.widgets:
            self.ui_manager.remove(self._active_dialogue_image_widget)
        self._active_dialogue_image_widget = None

    def _activate_key_if_last_dialogue(self, event):
        if not self.key or not self.last_dialogue_name:
            return

        dialogue = event.get("entity")
        if not isinstance(dialogue, DialogueArea):
            return

        if dialogue.name != self.last_dialogue_name:
            return

        self.key.on_active()

    def kill_entity_event(self, event):
        self.entity_mn.remove_entity_by_id(event["id"])

    def process_input(self, events: list[Event]):
        for event in events:
            self.ui_manager.handle_event(event)
        self._handle_door_interaction(events)
        self.player.input(events)

    def _handle_door_interaction(self, events: list[Event]):
        if not self.door or not self.player:
            return
        if not self.door.can_player_interact(self.player):
            return
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == KEY_DIALOG:
                self.door.try_enter(self.player)
                self.interaction_key_widget.set_visible(False)
                break

    def update(self, dt: float):
        can_door_interact = self.door.can_player_interact(self.player) if self.door and self.player else False
        self.dialogue_hud.update(self.player, extra_interaction=can_door_interact)
        self.dialog_system.update(self.entity_mn, self.player, dt)
        self.update_systems(dt)
        self.ui_manager.update(dt)

    def render(self):
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale)
        self.ui_manager.draw(self.screen)
