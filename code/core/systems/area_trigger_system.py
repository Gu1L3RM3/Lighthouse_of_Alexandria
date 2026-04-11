from core.ecs import System
from core.components.area_trigger import AreaTrigger
from core.components.collider import Collider
from core.components.position import Position
from core.components.velocity import Velocity
from utils.spatial_hash import SpatialHash

class AreaTriggerSystem(System):

    def __init__(self, cell_size=64):
        self.static_spatial = SpatialHash(cell_size)
        self.dynamic_spatial = SpatialHash(cell_size)
        self._static_rebuild_interval = 0.25
        self._static_rebuild_acc = self._static_rebuild_interval

    def _rebuild_static_spatial(self, static_triggers):
        self.static_spatial.clear()
        for e in static_triggers:
            area = e.get(AreaTrigger)
            if not area.active:
                continue
            pos = e.get(Position)
            rect = area.get_rect(pos.x, pos.y)
            self.static_spatial.insert(e, rect)

    def update(self, entity_mn, dt):
        entities_with_area = entity_mn.get_entities_with(AreaTrigger, Position)
        # Only dynamic colliders need continuous trigger checks. This skips static
        # world geometry colliders and cuts the hot loop significantly.
        entities_with_collider = entity_mn.get_entities_with(Collider, Position, Velocity)

        dynamic_triggers = [e for e in entities_with_area if e.has(Velocity)]
        static_triggers = [e for e in entities_with_area if not e.has(Velocity)]

        self._static_rebuild_acc += max(0.0, float(dt))
        if self._static_rebuild_acc >= self._static_rebuild_interval:
            self._static_rebuild_acc = 0.0
            self._rebuild_static_spatial(static_triggers)

        self.dynamic_spatial.clear()
        for e in dynamic_triggers:
            area = e.get(AreaTrigger)
            if not area.active:
                continue
            pos = e.get(Position)
            rect = area.get_rect(pos.x, pos.y)
            self.dynamic_spatial.insert(e, rect)

        for entity in entities_with_collider:
            col = entity.get(Collider)
            pos = entity.get(Position)
            
            col_rect = col.get_rect(pos.x, pos.y)
            nearby = self.static_spatial.query(col_rect)
            nearby.extend(self.dynamic_spatial.query(col_rect))

            for trigger_entity, trigger_rect in nearby:
                trigger = trigger_entity.get(AreaTrigger)

                if abs(trigger_rect.centerx - col_rect.centerx) > trigger_rect.width + 80:
                    continue
                if abs(trigger_rect.centery - col_rect.centery) > trigger_rect.height + 80:
                    continue



                trigger.check_collision(entity, col_rect, trigger_rect)
