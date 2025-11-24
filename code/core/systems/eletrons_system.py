from core.ecs import System
from core.map.tile_map import TileMap
from core.components.path_follower import PathFollower
from core.components.position import Position
from entities.animate_circuit.circuit_components import Eletron

class EletronSystem(System):
    def __init__(self, tile_map: TileMap):
        super().__init__()
        self.tile_map = tile_map
        self.wp_names = ['goal_1', 'goal_2']
        self.current_goal_index = {}  
        self.initialized = set()      

    def update(self, entity_mn, dt):
        eletrons: list[Eletron] = entity_mn.get_entities_by_class(Eletron)

        for eletron in eletrons:
            pos: Position = eletron.get(Position)

            if eletron not in self.initialized:
                start_tile = (
                    int(pos.x // self.tile_map.tile_width),
                    int(pos.y // self.tile_map.tile_height)
                )

                goal1 = self.tile_map.get_waypoint_tile(self.wp_names[0])
                goal2 = self.tile_map.get_waypoint_tile(self.wp_names[1])

                dist1 = abs(goal1[0] - start_tile[0]) + abs(goal1[1] - start_tile[1])
                dist2 = abs(goal2[0] - start_tile[0]) + abs(goal2[1] - start_tile[1])

                if dist1 <= dist2:
                    self.current_goal_index[eletron] = 0  # começa indo para goal_1
                else:
                    self.current_goal_index[eletron] = 1  # começa indo para goal_2

                goal_tile = self.tile_map.get_waypoint_tile(
                    self.wp_names[self.current_goal_index[eletron]]
                )
                path = self.tile_map.pathfinder.find_path(start_tile, goal_tile)
                eletron.add(PathFollower(path, speed=80))

                self.initialized.add(eletron)
                continue

            if eletron.has(PathFollower):
                path_follower: PathFollower = eletron.get(PathFollower)

                if not path_follower.done:
                    continue

                self.current_goal_index[eletron] = 1 - self.current_goal_index[eletron]
                next_goal_name = self.wp_names[self.current_goal_index[eletron]]

                start_tile = (
                    int(pos.x // self.tile_map.tile_width),
                    int(pos.y // self.tile_map.tile_height)
                )
                goal_tile = self.tile_map.get_waypoint_tile(next_goal_name)

                path = self.tile_map.pathfinder.find_path(start_tile, goal_tile)
                eletron.add(PathFollower(path, speed=100))
