from core.ecs import System
from core.components.area_trigger import AreaTrigger
from core.components.collider import Collider
from core.components.position import Position

class AreaTriggerSystem(System):

    def update(self, entity_mn, dt):
        itens = entity_mn.get_entities_with(AreaTrigger)
       
        player = entity_mn.get_player()
        col_player:Collider = player.get(Collider)
        pos_player:Position = player.get(Position)
        for item in itens:
            area_trigger :AreaTrigger = item.get(AreaTrigger)
            area_trigger.check_collision(
                player.id,
                col_player.get_rect(pos_player.x,pos_player.y))




            