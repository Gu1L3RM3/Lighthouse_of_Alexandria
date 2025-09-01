from pytmx.util_pygame import load_pygame
import pytmx
import pygame
from core.navigation import NavGrid, Pathfinder
from core.managers.entity_manager import EntityManager
from entities.npcs.npc_factory import NPCFactory
from core.components.npc_routine import NPCRoutine
from core.managers.resource_manager import ResourceManager
from core.ecs import Entity
from core.components.collider import Collider
from core.components.position import Position
from core.components.sprite import Sprite
class MapSystem:
    """
    Otimizado para performance:
    - Tiles de chão são pré-renderizados em uma Surface
    - Tiles sólidos apenas colliders (sem entidades extras para cada tile)
    - Apenas NPCs e player são entidades dinâmicas
    """

    def __init__(self, tmx_file: str):
        self.resource_mn=ResourceManager.get()
        self.tmx_path = self.resource_mn.get_asset_path("maps", tmx_file)
        self.tmx_data: pytmx.TiledMap = load_pygame(self.tmx_path, pixelalpha=True)
        self.tile_width, self.tile_height = self.tmx_data.tilewidth, self.tmx_data.tileheight
        self.map_width = self.tmx_data.width * self.tile_width
        self.map_height = self.tmx_data.height * self.tile_height

        self.spawn_points: dict[str, tuple[int, int]] = {}
        self.waypoints: dict[str, tuple[int, int]] = {}

        self.navgrid = NavGrid(self.tmx_data, self.tile_width, self.tile_height, walk_layer_name="ground2")
        self.pathfinder = Pathfinder(self.navgrid)

        # Superfícies pré-renderizadas
        self.ground_surface = pygame.Surface((self.map_width, self.map_height)).convert_alpha()
        self.ground_surface.fill((0,0,0,0))

        # Lista de colliders sólidos
        self.solid_colliders: list[pygame.Rect] = []

    def load_map(self, entity_mn: EntityManager):
        self._parse_entities_layer()
        self._parse_waypoints_layer()
        self._pre_render_ground_layers()
        self._load_obj_colliders(entity_mn)
        self._load_npcs(entity_mn)

    def get_player_spawn(self) -> tuple[int, int]:
        return self.spawn_points.get("player", (0, 0))
    
    def get_waypoint_tile(self, name: str) -> tuple[int, int] | None:
        """
        Retorna as coordenadas de tile de um waypoint pelo nome.
        """
        return self.waypoints.get(name.lower())

    def get_player_spawn(self) -> tuple[int, int]:
        """
        Retorna a posição inicial do player (em pixels)
        """
        return self.spawn_points.get("player", (0, 0))

    # ---------------- Layer Parsing ----------------
    def _parse_entities_layer(self):
        for layer in self._iter_layers("entities", pytmx.TiledObjectGroup):
            for obj in layer:
                if (obj.name or "").lower().startswith("player"):
                    self.spawn_points["player"] = (int(obj.x), int(obj.y))

    def _parse_waypoints_layer(self):
        for layer in self._iter_layers("waypoints", pytmx.TiledObjectGroup):
            for obj in layer:
                name = (obj.name or "").lower()
                if not name: continue
                tx, ty = int(obj.x // self.tile_width), int(obj.y // self.tile_height)
                self.waypoints[name] = (tx, ty)

    # ---------------- Ground Tiles ----------------
    def _pre_render_ground_layers(self):
        for layer in self._iter_visible_layers(("ground", "ground2"), pytmx.TiledTileLayer):
            for x, y, gid in layer:
                img = self.tmx_data.get_tile_image_by_gid(gid)
                if img:
                    self.ground_surface.blit(img, (x * self.tile_width, y * self.tile_height))

    # ---------------- Object Colliders ----------------
    def _load_obj_colliders(self, entity_mn:EntityManager):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name and layer.name.lower() == "obj":
                for x, y, gid in layer:
                    if isinstance(gid, int) and gid != 0:
                        img = self.tmx_data.get_tile_image_by_gid(gid)
                        e = Entity()
                        if img:
                            e.add(Sprite(img))
                        e.add(Position(x*self.tile_width, y*self.tile_height), Collider(self.tile_width, self.tile_height))
                        entity_mn.add_entity(e)




    # ---------------- NPCs ----------------
    def _load_npcs(self, entity_mn: EntityManager):
        for layer in self._iter_layers("npc", pytmx.TiledObjectGroup):
            for obj in layer:
                npc_type = (obj.type or obj.name or "").lower()
                x, y = int(obj.x), int(obj.y)
                props = {k.lower(): v for k, v in (obj.properties or {}).items()}

                schedule = {
                    int(k.split("_", 1)[1]): v.lower()
                    for k, v in props.items()
                    if k.startswith("route_") and isinstance(v, str)
                    and k.split("_", 1)[1].isdigit()
                }

                npc = NPCFactory.create(npc_type, x, y, props)
                if schedule:
                    npc.add(NPCRoutine(schedule))
                entity_mn.add_entity(npc)

    # ---------------- Layer Iterators ----------------
    def _iter_layers(self, names: str | tuple[str, ...], layer_type):
        if isinstance(names, str):
            names = (names,)
        names = tuple(n.lower() for n in names)
        for layer in self.tmx_data.layers:
            if isinstance(layer, layer_type) and layer.name and layer.name.lower() in names:
                yield layer

    def _iter_visible_layers(self, names: str | tuple[str, ...], layer_type):
        for layer in self._iter_layers(names, layer_type):
            if getattr(layer, "visible", True):
                yield layer
