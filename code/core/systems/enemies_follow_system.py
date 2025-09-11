from core.ecs import System, Entity
from core.components.player_follower import PlayerFollower
from core.components.position import Position
from core.components.velocity import Velocity
from core.components.freeze import Freeze
from core.components.path_follower import PathFollower
from core.managers.entity_manager import EntityManager
from core.managers.time_manager import TimeManager
from entities.player import Player
from core.map.tile_map import TileMap
class EnemiesFollowSystem(System):
    def __init__(self, tile_map: TileMap):
        super().__init__()
        self.tile_map = tile_map
        self.timer = TimeManager()

    def _can_update_path(self, entity: Entity, interval: float) -> bool:
        time_name = f"set_path_{entity.id}"
        if self.timer.ready(time_name):  
            self.timer.set(time_name, interval)  
            return True
        return False

    def update(self, entity_mn: EntityManager, dt):
        entities_with_follow_player = entity_mn.get_entities_with(
            PlayerFollower, Position, Velocity
        )
        player: Player = entity_mn.get_player()

        for e in entities_with_follow_player:
            if e.has(Freeze) and e.get(Freeze).active:
                continue

            player_pos: Position = player.get(Position)
            goal_tile = self.tile_map.get_tile_from_position(player_pos)
            if not goal_tile:
                continue

            pos: Position = e.get(Position)
            start_tile = self.tile_map.get_tile_from_position(pos)

            player_follower: PlayerFollower = e.get(PlayerFollower)

            if not self._can_update_path(e, player_follower.interval_to_update):
                continue  

            path = self.tile_map.pathfinder.find_path(start_tile, goal_tile)

            if not path or len(path)<=1:
                if e.has(PathFollower): e.remove(PathFollower)
                continue

            if not e.has(PathFollower):
                e.add(PathFollower(path,speed=player_follower.speed))
                continue
            pf:PathFollower=e.get(PathFollower)
            pf.set_path(path)

