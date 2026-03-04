from core.ecs import System
from core.map.tile_map import TileMap
from core.components.path_follower import PathFollower
from core.components.position import Position
from core.components.electron_flow import ElectronFlow
from entities.animate_circuit.circuit_components import Eletron


class EletronSystem(System):
    def __init__(self, tile_map: TileMap):
        super().__init__()
        self.tile_map = tile_map
        self.initialized = set()
        self.route_recovery_threshold = max(self.tile_map.tile_width, self.tile_map.tile_height) * 1.75
        self.goal_a = self.tile_map.get_waypoint_tile("goal_1")
        self.goal_b = self.tile_map.get_waypoint_tile("goal_2")
        self.directed_cycle = self._build_directed_cycle()

    def _clamp_tile(self, tx: int, ty: int) -> tuple[int, int]:
        max_x = self.tile_map.tmx_data.width - 1
        max_y = self.tile_map.tmx_data.height - 1
        return (
            max(0, min(tx, max_x)),
            max(0, min(ty, max_y)),
        )

    def _start_tile_from_pos(self, pos: Position) -> tuple[int, int]:
        tx = int(pos.x // self.tile_map.tile_width)
        ty = int(pos.y // self.tile_map.tile_height)
        return self._clamp_tile(tx, ty)

    def _build_directed_cycle(self) -> list[tuple[int, int]]:
        if self.goal_a is None or self.goal_b is None:
            return []

        goal_a = self._clamp_tile(self.goal_a[0], self.goal_a[1])
        goal_b = self._clamp_tile(self.goal_b[0], self.goal_b[1])

        leg_ab = self.tile_map.pathfinder.find_path(goal_a, goal_b)
        if not leg_ab:
            return []

        blocked = set(leg_ab[1:-1])
        leg_ba = self.tile_map.pathfinder.find_path(goal_b, goal_a, blocked_tiles=blocked)
        if not leg_ba:
            leg_ba = self.tile_map.pathfinder.find_path(goal_b, goal_a)
            if not leg_ba:
                return []

        cycle = leg_ab + leg_ba[1:]
        if len(cycle) > 1 and cycle[0] == cycle[-1]:
            cycle = cycle[:-1]
        return cycle

    def _nearest_cycle_index(self, tile: tuple[int, int]) -> int:
        if not self.directed_cycle:
            return 0
        best_idx = 0
        best_dist = float("inf")
        for i, point in enumerate(self.directed_cycle):
            dist = abs(point[0] - tile[0]) + abs(point[1] - tile[1])
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        return best_idx

    def _build_cycle_path_from_index(self, start_idx: int) -> list[tuple[int, int]]:
        if not self.directed_cycle:
            return []
        rotated = self.directed_cycle[start_idx:] + self.directed_cycle[:start_idx]
        rotated.append(rotated[0])
        return rotated

    def _build_recovery_path(self, start_tile: tuple[int, int], cycle_idx: int) -> list[tuple[int, int]]:
        if not self.directed_cycle:
            return []
        target_tile = self.directed_cycle[cycle_idx]
        to_cycle = self.tile_map.pathfinder.find_path(start_tile, target_tile)
        if not to_cycle:
            return self._build_cycle_path_from_index(cycle_idx)
        cycle_path = self._build_cycle_path_from_index(cycle_idx)
        return to_cycle + cycle_path[1:]

    def _set_follow_path(self, eletron: Eletron, path: list[tuple[int, int]], speed: float):
        if not path:
            return
        eletron.add(
            PathFollower(
                path,
                speed=speed,
                tile_size=self.tile_map.tile_width,
                loop=True,
            )
        )

    def _is_off_route(self, pos: Position, path_follower: PathFollower) -> bool:
        if not path_follower.collision_rects:
            return False
        center = pos.center_pos()
        next_rect = path_follower.collision_rects[0]
        dx = abs(next_rect.centerx - center.x)
        dy = abs(next_rect.centery - center.y)
        return dx > self.route_recovery_threshold or dy > self.route_recovery_threshold

    def update(self, entity_mn, dt):
        eletrons: list[Eletron] = entity_mn.get_entities_by_class(Eletron)
        if not self.directed_cycle:
            return

        for eletron in eletrons:
            pos: Position = eletron.get(Position)
            flow: ElectronFlow = eletron.get(ElectronFlow)
            flow.update(dt)

            current_tile = self._start_tile_from_pos(pos)
            cycle_idx = self._nearest_cycle_index(current_tile)

            if eletron not in self.initialized:
                init_path = self._build_recovery_path(current_tile, cycle_idx)
                self._set_follow_path(eletron, init_path, speed=flow.current_speed)
                self.initialized.add(eletron)
                continue

            if not eletron.has(PathFollower):
                restart_path = self._build_recovery_path(current_tile, cycle_idx)
                self._set_follow_path(eletron, restart_path, speed=flow.current_speed)
                continue

            path_follower: PathFollower = eletron.get(PathFollower)
            path_follower.speed = flow.current_speed

            if self._is_off_route(pos, path_follower):
                recovery_path = self._build_recovery_path(current_tile, cycle_idx)
                self._set_follow_path(eletron, recovery_path, speed=flow.current_speed)
