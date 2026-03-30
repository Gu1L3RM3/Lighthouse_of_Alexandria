import pygame
from pygame import Surface
import re

from core.settings import *
from scenes.base_scene import BaseScene
from entities.dialogue_area import DialogueArea
from entities.itens.old_paper import OldPaper
from core.components.area_trigger import AreaTrigger
from core.components.position import Position
from core.components.collider import Collider
from core.components.dialogue import Dialogue
from core.ui.widgets.fps_widget import FPSWidget
from core.ui.widgets.alert_dialog import AlertDialog
from core.map.tile_map_loader import TileMapLoader
from core.map.map_entity_spawner import MapEntitySpawner
from core.map.map_renderer import MapRenderer
from core.systems.animation_system import AnimationSystem
from core.systems.area_trigger_system import AreaTriggerSystem
from core.systems.freeze_system import FreezeSystem
from core.managers.attention_manager import AttentionManager
from core.managers.scene_manager import SceneManager
from core.managers.audio_manager import AudioManager
from core.ui.dialogue_interaction_hud_controller import DialogueInteractionHUDController
from core.ui.widgets.interaction_key_widget import InteractionKeyWidget
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType


class HomeAfterScene(BaseScene):
    def __init__(self, screen: Surface):
        loader = TileMapLoader()
        self.tile_map = loader.load("house_after.tmx")
        self.scale = 2
        super().__init__(screen, self.tile_map.map_width * self.scale, self.tile_map.map_height * self.scale)

        self.map_renderer = MapRenderer(self.tile_map, self.camera, self.screen, self.scale)
        fps = FPSWidget()
        self.ui_manager.add(fps)
        self.interaction_key_widget = InteractionKeyWidget(self.screen.get_size(), label="ENTRAR")
        self.ui_manager.add(self.interaction_key_widget)
        self._set_hud_buttons()
        self.set_map()

        self.animation_system = AnimationSystem()
        self.area_trigger_system = AreaTriggerSystem()
        self.freeze_system = FreezeSystem()

        self.camera.scale = self.scale
        self.camera.follow = self.player
        self.old_paper_activated = False

        self.systems.update(
            [
                self.freeze_system,
                self.physics_system,
                self.animation_system,
                self.area_trigger_system,
                self.render_system,
            ]
        )
        self.attention_manager = AttentionManager(self.entity_mn)
        self.dialogue_hud = DialogueInteractionHUDController(
            self.entity_mn,
            self.dialog_system,
            self.interaction_key_widget,
        )
        self.scene_manager = SceneManager.get()
        self.audio_manager = AudioManager.get()

    def _set_hud_buttons(self):
        help_x = self.screen.get_width() - 92
        idle = pygame.transform.scale(self.resources.load_image("buttons/short.png"), (142, 78))
        pressed = pygame.transform.scale(self.resources.load_image("buttons/short_pressed.png"), (142, 78))
        self.help_button = Button(
            init_surface=idle,
            surface_pressed=pressed,
            pos_center=(help_x, 44),
            click_type=ClickType.AFTER_RELEASED,
            action=lambda: SceneManager.get().open_help(0.35),
            text="HELP",
            font_size=11,
            color_text=(245, 230, 170),
        )
        self.ui_manager.add(self.help_button)

    def start(self):
        pygame.mouse.set_visible(True)
        self.set_subscribes()

    def set_subscribes(self):
        self.event_manager.subscribe("request_freeze", self.freeze_system.request_freeze)
        self.event_manager.subscribe("release_freeze", self.freeze_system.release_freeze)

        self.event_manager.subscribe("dialogue_end", self.attention_manager.set_attention_position_after_event)
        self.event_manager.subscribe("dialogue_end", self._advance_dialogue_sequence)
        self.event_manager.subscribe("dialogue_end", self.set_old_paper)
        self.event_manager.subscribe("open_old_paper", self.open_old_paper)
        self.event_manager.subscribe("close_old_paper", self.after_close_old_paper)

    def _advance_dialogue_sequence(self, event):
        entity = event.get("entity")
        if not isinstance(entity, DialogueArea):
            return

        current_dialogue: Dialogue = entity.get(Dialogue)
        current_dialogue.active_status = False

        match = re.match(r"dialog_(\d+)$", entity.name or "")
        if not match:
            return

        next_name = f"dialog_{int(match.group(1)) + 1}"

        for area in self.entity_mn.get_entities_by_class(DialogueArea):
            dialogue: Dialogue = area.get(Dialogue)
            dialogue.active_status = area.name == next_name

    def after_close_old_paper(self, event):
        _ = event
        self.event_manager.post({"type": "release_freeze"})
        self.audio_manager.play_sfx("sfx/paper_close.wav", volume=0.85)
        self.scene_manager.start_fade("ending_thanks_credits", 0.8)

    def set_old_paper(self, event):
        dialogue: DialogueArea = event.get("entity")
        if not isinstance(dialogue, DialogueArea):
            return
        if self.old_paper_activated:
            return
        if not re.match(r"dialog_\d+$", dialogue.name or ""):
            return

        old_papers = self.entity_mn.get_entities_by_class(OldPaper)
        if not old_papers:
            return
        self.old_paper: OldPaper = old_papers[0]
        self.old_paper.on_active()
        area_trigger: AreaTrigger = self.old_paper.get(AreaTrigger)
        # Home after usa interacao por tecla E; evita abrir automaticamente ao encostar.
        area_trigger.on_entered = self._noop_old_paper_auto_open
        self.old_paper_activated = True

    def open_old_paper(self, event):
        _ = event
        self.event_manager.post({"type": "request_freeze", "type_request": "teste"})
        self.audio_manager.play_sfx("sfx/paper_open.wav", volume=0.9)

        def close_old_paper(widget):
            self.ui_manager.remove(widget)
            self.event_manager.post({"type": "close_old_paper"})

        paper: Surface = self.resources.load_image("letters/letter_4.png")
        alert_dialog = AlertDialog(
            title="",
            surface=paper,
            on_close=close_old_paper,
        )
        self.ui_manager.add(alert_dialog)

    def set_map(self):
        spawner = MapEntitySpawner()
        spawner.spawn_entities(self.tile_map, self.entity_mn)

        self.player = self.entity_mn.get_player()
        self.physics_system.cache_static_colliders(self.entity_mn)

    def _noop_old_paper_auto_open(self, entity):
        _ = entity

    def _can_old_paper_interact(self):
        if not hasattr(self, "old_paper") or not self.old_paper:
            return False
        if not self.player or not self.player.has(Position) or not self.player.has(Collider):
            return False
        if not self.old_paper.has(AreaTrigger) or not self.old_paper.has(Position):
            return False

        trigger: AreaTrigger = self.old_paper.get(AreaTrigger)
        if not trigger.active:
            return False

        paper_pos: Position = self.old_paper.get(Position)
        player_pos: Position = self.player.get(Position)
        player_rect = self.player.get(Collider).get_rect(player_pos.x, player_pos.y)
        paper_rect = trigger.get_rect(paper_pos.x, paper_pos.y)
        return player_rect.colliderect(paper_rect)

    def _handle_old_paper_interaction(self, events):
        if not self._can_old_paper_interact():
            return
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == KEY_DIALOG:
                self.audio_manager.play_sfx("sfx/interact_confirm.wav", volume=0.85)
                self.event_manager.post({"type": "open_old_paper"})
                self.interaction_key_widget.set_visible(False)
                break

    def process_input(self, events):
        for event in events:
            self.ui_manager.handle_event(event)
        self._handle_old_paper_interaction(events)
        self.player.input(events)

    def update(self, dt):
        self.dialogue_hud.update(self.player, extra_interaction=self._can_old_paper_interact())
        self.dialog_system.update(self.entity_mn, self.player, dt)

        self.update_systems(dt)
        self.ui_manager.update(dt)

    def render(self):
        self.screen.fill(BLACK)
        self.map_renderer.draw()
        self.render_system.draw(scale=self.scale)
        self.ui_manager.draw(self.screen)
