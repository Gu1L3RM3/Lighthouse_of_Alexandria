from __future__ import annotations  

from entities.weapons.weapon import Weapon
from core.components.position import Position
from core.components.animation_sprite import AnimateSprite
from pygame import Vector2
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.managers.entity_manager import EntityManager

class Sword(Weapon):
    def attack(self, position: Position, old_direction: Vector2, entity_mn: EntityManager):
        player = entity_mn.get_player()
        

        dir_name = player._get_dir_name(old_direction)
        anim_name = f"attack_{dir_name}"

        anim: AnimateSprite = player.get(AnimateSprite)
        
            
        anim.play(anim_name, loop=False, on_finish=lambda: self._return_to_idle(player, dir_name))

    def _return_to_idle(self, player, dir_name: str):
        anim: AnimateSprite = player.get(AnimateSprite)
        
        anim.play(f"idle_{dir_name}", loop=True)

