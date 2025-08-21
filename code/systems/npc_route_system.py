from core.components.npc_routine import NPCRoutine
from core.components.path_follower import PathFollower
from core.components.position import Position
from core.components.freeze import Freeze

class NPCRouteSystem:
    """
    Verifica a hora (DayNightManager) e gera um PathFollower
    do tile atual até o waypoint agendado (nome -> tile via MapSystem).
    """
    def __init__(self, map_system, day_night_manager):
        self.map = map_system
        self.dn  = day_night_manager

    def update(self, entities):
        cur_hour = int(self.dn.time_of_day)

        for e in entities:
            if not e.has(NPCRoutine) or not e.has(Position):
                continue
            if e.has(Freeze) and e.get(Freeze).active:
                continue

            routine: NPCRoutine = e.get(NPCRoutine)
            if routine.last_hour_checked == cur_hour:
                continue

            routine.last_hour_checked = cur_hour

            if cur_hour not in routine.schedule:
                continue

            wp_name = routine.schedule[cur_hour]
            goal_tile = self.map.get_waypoint_tile(wp_name)
            if not goal_tile:
                continue

            pos: Position = e.get(Position)
            start_tile = (int(pos.x // self.map.tile_width), int(pos.y // self.map.tile_height))
            path = self.map.pathfinder.find_path(start_tile, goal_tile)
            if path and len(path) > 1:
                # first node é o tile atual — mantém para suavizar parada
                e.add(PathFollower(path, speed=50))
            else:
                # já está no destino
                if e.has(PathFollower):
                    e.remove(PathFollower)
