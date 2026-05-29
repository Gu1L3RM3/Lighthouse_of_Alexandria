from entities.enemies.enemy_factory import EnemyFactory
from entities.enemies.phantom_enemy import PhantomEnemy
from core.components.position import Position
from core.ecs import System
from core.settings import GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS, GENERIC_LEVEL_GHOST_RESPAWN_SECONDS


class GenericLevelGhostSystem(System):
    def __init__(self, scene):
        self.scene = scene

    def update(self, entity_manager, dt: float):
        _ = entity_manager
        self.update_ghost_respawns(dt)
        self.update_ghost_rebirth_effects(dt)

    def capture_initial_ghost_spawn_templates(self):
        self.scene._ghost_spawn_templates.clear()
        self.scene._ghost_entity_to_spawn_key.clear()
        routes = self.extract_enemy_routes_from_map()

        enemy_layer = None
        for layer in self.scene.tile_map.tmx_data.objectgroups:
            if (layer.name or "").lower() == "enemies":
                enemy_layer = layer
                break
        if enemy_layer is None:
            return

        spawn_index = 0
        for obj in enemy_layer:
            props = {k.lower(): v for k, v in (obj.properties or {}).items()}
            enemy_type = (obj.type or props.get("enemy_type") or obj.name or "spider").lower()
            if enemy_type != "phantom":
                continue

            route_id = str(props.get("route_id", "")).lower().strip()
            route = routes.get(route_id) if route_id else None
            if route:
                start_tile = (
                    int(obj.x // self.scene.tile_map.tile_width),
                    int(obj.y // self.scene.tile_map.tile_height),
                )
                if route[0] != start_tile:
                    route = [start_tile, *route]

            spawn_key = f"phantom_spawn_{spawn_index}"
            spawn_index += 1
            self.scene._ghost_spawn_templates[spawn_key] = {
                "enemy_type": enemy_type,
                "x": float(obj.x),
                "y": float(obj.y),
                "props": dict(props),
                "route": [tuple(tile) for tile in (route or [])],
                "pending_respawn": False,
                "active_entity_id": None,
            }

        self.bind_existing_ghost_entities_to_templates()

    def extract_enemy_routes_from_map(self) -> dict[str, list[tuple[int, int]]]:
        routes: dict[str, list[tuple[int, tuple[int, int]]]] = {}
        for layer in self.scene.tile_map.tmx_data.objectgroups:
            if (layer.name or "").lower() != "enemy_routes":
                continue
            for obj in layer:
                properties = {k.lower(): v for k, v in (obj.properties or {}).items()}
                route_id = str(properties.get("route_id") or obj.name or "").lower().strip()
                if not route_id:
                    continue
                order = int(properties.get("order", 0))
                tile_point = (
                    int(obj.x // self.scene.tile_map.tile_width),
                    int(obj.y // self.scene.tile_map.tile_height),
                )
                routes.setdefault(route_id, []).append((order, tile_point))

        normalized_routes: dict[str, list[tuple[int, int]]] = {}
        for route_id, points in routes.items():
            ordered_points = sorted(points, key=lambda p: p[0])
            normalized_routes[route_id] = [tile for _, tile in ordered_points]
        return normalized_routes

    def bind_existing_ghost_entities_to_templates(self):
        self.scene._ghost_entity_to_spawn_key.clear()
        for template in self.scene._ghost_spawn_templates.values():
            template["pending_respawn"] = False
            template["active_entity_id"] = None

        ghosts: list[PhantomEnemy] = self.scene.entity_mn.get_entities_by_class(PhantomEnemy)
        unmatched_ghosts = list(ghosts)

        for spawn_key, template in self.scene._ghost_spawn_templates.items():
            target_x = float(template["x"])
            target_y = float(template["y"])
            chosen = None
            chosen_dist = None
            for ghost in unmatched_ghosts:
                if not ghost.has(Position):
                    continue
                pos: Position = ghost.get(Position)
                dist_sq = ((float(pos.x) - target_x) ** 2) + ((float(pos.y) - target_y) ** 2)
                if chosen is None or dist_sq < chosen_dist:
                    chosen = ghost
                    chosen_dist = dist_sq
            if chosen is None:
                continue
            template["active_entity_id"] = chosen.id
            self.scene._ghost_entity_to_spawn_key[chosen.id] = spawn_key
            unmatched_ghosts.remove(chosen)

    def queue_ghost_respawn_by_entity_id(
        self,
        entity_id: int,
        death_x: float | None = None,
        death_y: float | None = None,
    ):
        spawn_key = self.scene._ghost_entity_to_spawn_key.pop(entity_id, None)
        if spawn_key is None:
            for key, template in self.scene._ghost_spawn_templates.items():
                if template.get("active_entity_id") == entity_id:
                    spawn_key = key
                    break
        if spawn_key is None and death_x is not None and death_y is not None:
            # Fallback: se o vinculo foi perdido por alguma transicao de cena,
            # escolhe o spawn de fantasma mais proximo da morte.
            nearest_key = None
            nearest_dist = None
            for key, template in self.scene._ghost_spawn_templates.items():
                if template.get("pending_respawn", False):
                    continue
                tx = float(template.get("x", 0.0))
                ty = float(template.get("y", 0.0))
                dist_sq = ((float(death_x) - tx) ** 2) + ((float(death_y) - ty) ** 2)
                if nearest_key is None or dist_sq < nearest_dist:
                    nearest_key = key
                    nearest_dist = dist_sq
            spawn_key = nearest_key
        if spawn_key is None:
            return
        template = self.scene._ghost_spawn_templates.get(spawn_key)
        if not template:
            return
        if template.get("pending_respawn", False):
            return
        template["active_entity_id"] = None
        template["pending_respawn"] = True
        self.scene.ghost_respawn_queue.append(
            {
                "spawn_key": spawn_key,
                "remaining": float(GENERIC_LEVEL_GHOST_RESPAWN_SECONDS),
                "respawn_x": None,
                "respawn_y": None,
            }
        )

    def spawn_ghost_from_template(self, spawn_key: str, respawn_x: float | None = None, respawn_y: float | None = None):
        template = self.scene._ghost_spawn_templates.get(spawn_key)
        if not template:
            return
        props = dict(template.get("props", {}))
        route = [tuple(tile) for tile in template.get("route", [])]
        spawn_x = float(template.get("x", 0.0)) if respawn_x is None else float(respawn_x)
        spawn_y = float(template.get("y", 0.0)) if respawn_y is None else float(respawn_y)
        enemy = EnemyFactory.create(
            enemy_type=str(template.get("enemy_type", "phantom")),
            x=spawn_x,
            y=spawn_y,
            props=props,
            route=route,
        )
        self.scene.entity_mn.add_entity(enemy)
        template["pending_respawn"] = False
        template["active_entity_id"] = enemy.id
        self.scene._ghost_entity_to_spawn_key[enemy.id] = spawn_key

    def start_ghost_rebirth_effect(self, spawn_key: str, respawn_x: float | None = None, respawn_y: float | None = None):
        template = self.scene._ghost_spawn_templates.get(spawn_key)
        if not template:
            return
        spawn_x = float(template.get("x", 0.0)) if respawn_x is None else float(respawn_x)
        spawn_y = float(template.get("y", 0.0)) if respawn_y is None else float(respawn_y)
        self.scene.ghost_rebirth_effects.append(
            {
                "spawn_key": spawn_key,
                "x": spawn_x,
                "y": spawn_y,
                "elapsed": 0.0,
                "duration": float(GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS),
            }
        )

    def update_ghost_respawns(self, dt: float):
        if not self.scene.ghost_respawn_queue:
            return
        still_waiting = []
        for entry in self.scene.ghost_respawn_queue:
            entry["remaining"] -= dt
            if entry["remaining"] > 0:
                still_waiting.append(entry)
                continue
            self.start_ghost_rebirth_effect(
                str(entry.get("spawn_key", "")),
                respawn_x=entry.get("respawn_x"),
                respawn_y=entry.get("respawn_y"),
            )
        self.scene.ghost_respawn_queue = still_waiting

    def update_ghost_rebirth_effects(self, dt: float):
        if not self.scene.ghost_rebirth_effects:
            return
        still_animating = []
        for effect in self.scene.ghost_rebirth_effects:
            effect["elapsed"] += dt
            duration = max(0.001, float(effect.get("duration", GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS)))
            if effect["elapsed"] < duration:
                still_animating.append(effect)
                continue
            self.spawn_ghost_from_template(
                str(effect.get("spawn_key", "")),
                respawn_x=effect.get("x"),
                respawn_y=effect.get("y"),
            )
            self.scene.audio_manager.play_sfx("sfx/light_on.wav", volume=0.82)
        self.scene.ghost_rebirth_effects = still_animating
