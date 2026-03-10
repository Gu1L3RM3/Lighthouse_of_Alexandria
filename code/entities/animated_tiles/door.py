from pygame import Rect
from core.ecs import Entity
from core.managers.resource_manager import ResourceManager
from core.managers.scene_manager import SceneManager
from core.managers.audio_manager import AudioManager
from core.components.position import Position
from core.components.collider import Collider
from core.components.animation_sprite import AnimateSprite
from core.components.sprite import Sprite
from core.components.light_component import LightComponent
from entities.player import Player


class Door(Entity):
    def __init__(self,x,y,props=None):
        super().__init__()
        self.props = props or {}
        self.next_scene = self.props.get('next_scene', '')
        self.animations =  ResourceManager.get().load_sprite_sheet('door',(48,32))
        # Area local de interação em torno da porta aberta.
        self.interaction_area = Rect(-8, -8, 64, 48)
        self.is_open = False

        self.add(
            AnimateSprite(
                self.animations
            ),
            Position(x,y),
        )

    def active_door(self):
        self.is_open = True

    def get_interaction_rect(self) -> Rect:
        pos: Position = self.get(Position)
        area = self.interaction_area.copy()
        area.topleft = (int(pos.x + self.interaction_area.x), int(pos.y + self.interaction_area.y))
        return area

    def can_player_interact(self, player: Player) -> bool:
        if not self.is_open or not player or not player.has(Position) or not player.has(Collider):
            return False
        player_pos: Position = player.get(Position)
        player_col = player.get(Collider).get_rect(player_pos.x, player_pos.y)
        return player_col.colliderect(self.get_interaction_rect())

    def try_enter(self, player: Player):
        if not self.can_player_interact(player):
            return
        SceneManager.get().start_fade(self.next_scene)

    def open(self,event):
        _ = event
        if self.is_open:
            return
        AudioManager.get().play_sfx("sfx/door_open.wav", volume=0.92)
        animate_sprite:AnimateSprite= self.get(AnimateSprite)
        self.add(
            Sprite(
                self.animations['idle'][0]
            ),
            LightComponent(),


        ),
        animate_sprite.play("idle",loop=False,on_finish=self.active_door)


