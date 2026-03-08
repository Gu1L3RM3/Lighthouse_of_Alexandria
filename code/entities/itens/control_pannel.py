import pygame
from pygame import Rect
from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.animation_sprite import AnimateSprite
from core.components.sprite import Sprite
from core.components.light_component import LightComponent
from core.components.panel_status import PanelStatus
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from core.components.always_on_top import AlwaysOnTop
from entities.player import Player
from entities.itens.item import Item
from scenes.circuit_editor import CircuitEditor
class ControlPannel(Item):
    def __init__(self,x,y,active,props):
        super().__init__(x,y,active,props)
        self.rm =  ResourceManager.get()
        self.event_manager =  EventManager.get()
        self.animations = self.rm.load_sprite_sheet("control_pannel",(32,32),trim_transparent=False)

        self.done = False
        


        self.animate = AnimateSprite(self.animations)

        # Area de interação local (melhorada): mais larga e levemente acima do painel.
        self.interaction_area = Rect(-12, -10, 56, 56)

        self.solution_value =  None
        self.active =  active
        self.panel_status = PanelStatus(is_active=self.active, is_done=self.done)
        self.pannel_id  = props['pannel_id']
        self.solution_type =  props['type_solution']
        self.target_component =  props['target_component']
        self.component_for_area = int(props['component_for_area'])
        self.name_file =f"{props['tmx_file']}/pannel{self.pannel_id}"
        self.stealth_bonus_duration = float(props.get("stealth_bonus_duration", 4.0))
        self.solved_hold_seconds = float(props.get("solved_hold_seconds", 45.0))
        stealth_enabled_raw = props.get("stealth_bonus_enabled", True)
        if isinstance(stealth_enabled_raw, str):
            stealth_enabled_raw = stealth_enabled_raw.strip().lower() in ("1", "true", "yes", "on")
        self.stealth_bonus_enabled = bool(stealth_enabled_raw)
        
        self.action_type =f"pannel_{props['action']}{self.pannel_id}" 
        
        self.add(
            Position(x,y),
            AlwaysOnTop(),
            self.animate,
            Sprite(self.animations['idle'][0]),
            LightComponent(),
            self.panel_status,
        )
        self.animate.play('idle')

  

    def action(self):
        self.event_manager.post({'type':self.action_type})
        if self.stealth_bonus_enabled and self.stealth_bonus_duration > 0:
            self.event_manager.post({
                "type": "player_invisible_to_enemies_started",
                "duration": self.stealth_bonus_duration,
                "source": "control_pannel",
                "pannel_id": self.pannel_id,
            })
        self.done = True
        self.panel_status.set_done(True)

        

    
    def get_interaction_rect(self) -> Rect:
        pos: Position = self.get(Position)
        area = self.interaction_area.copy()
        area.topleft = (int(pos.x + self.interaction_area.x), int(pos.y + self.interaction_area.y))
        return area

    def can_player_interact(self, player: Player) -> bool:
        self.panel_status.set_active(self.active)
        if not self.active or not player or not player.has(Position) or not player.has(Collider):
            return False
        player_pos: Position = player.get(Position)
        player_col = player.get(Collider).get_rect(player_pos.x, player_pos.y)
        return player_col.colliderect(self.get_interaction_rect())

    def open_circuit_editor(self):
        from core.managers.scene_manager import SceneManager
        SceneManager.get().active_scene = CircuitEditor(pygame.display.get_surface(), file=self.name_file)

    def on_collect(self, entity: Entity):
        _ = entity
            
            

