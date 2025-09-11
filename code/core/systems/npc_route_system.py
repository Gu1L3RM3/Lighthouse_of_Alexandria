from core.components.npc_routine import NPCRoutine
from core.components.path_follower import PathFollower
from core.components.position import Position
from core.components.freeze import Freeze
from core.managers.entity_manager import EntityManager
from core.managers.day_night_manager import DayNightManager
from core.map.tile_map import TileMap
from core.ecs import System
class NPCRouteSystem(System):
    
    def __init__(self, tile_map:TileMap, day_night_manager:DayNightManager):
        self.tile_map = tile_map
        self.dn  = day_night_manager

    def update(self, entity_mn:EntityManager,dt):

        cur_hour = int(self.dn.time_of_day)
        entities_with_routine=entity_mn.get_entities_with(NPCRoutine,Position)

        for e in entities_with_routine:
            if e.has(Freeze) and e.get(Freeze).active:
                continue

            routine: NPCRoutine = e.get(NPCRoutine)
            if routine.last_hour_checked == cur_hour:
                continue

            routine.last_hour_checked = cur_hour

            if cur_hour not in routine.schedule:
                continue

            wp_name = routine.schedule[cur_hour]
            goal_tile = self.tile_map.get_waypoint_tile(wp_name)
            
            if not goal_tile:
                continue

            pos: Position = e.get(Position)
            start_tile = (int(pos.x // self.tile_map.tile_width),
                          int(pos.y // self.tile_map.tile_height))
            path = self.tile_map.pathfinder.find_path(start_tile, goal_tile)
            if not path and e.has(PathFollower):
                e.remove(PathFollower)
                continue
            e.add(PathFollower(path,speed=50))

            
