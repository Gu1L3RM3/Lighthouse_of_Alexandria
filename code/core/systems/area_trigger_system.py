from core.ecs import System
from core.components.area_trigger import AreaTrigger
from core.components.collider import Collider
from core.components.position import Position
from utils.spatial_hash import SpatialHash

class AreaTriggerSystem(System):

    def __init__(self, cell_size=64):
        self.spatial = SpatialHash(cell_size)

    def update(self, entity_mn, dt):
        entities_with_area = entity_mn.get_entities_with(AreaTrigger)
        entities_with_collider = entity_mn.get_entities_with(Collider)
        self.spatial.clear()

        for e in entities_with_area:
            area = e.get(AreaTrigger)
            pos = e.get(Position)
            rect = area.area
            self.spatial.insert(e, rect)

        for entity in entities_with_collider:
            col = entity.get(Collider)
            pos = entity.get(Position)
            
            col_rect = col.get_rect(pos.x, pos.y)

            nearby = self.spatial.query(col_rect)

            for trigger_entity, trigger_rect in nearby:
                trigger = trigger_entity.get(AreaTrigger)

                if abs(trigger_rect.centerx - col_rect.centerx) > trigger_rect.width + 80:
                    continue
                if abs(trigger_rect.centery - col_rect.centery) > trigger_rect.height + 80:
                    continue



                trigger.check_collision(entity, col_rect)
