from pytmx.util_pygame import load_pygame
import pytmx
from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.sprite import Sprite
from core.config import get_asset_path
from core.navigation import NavGrid, Pathfinder
from entities.npcs.npc_factory import NPCFactory
from core.components.npc_routine import NPCRoutine
class MapSystem:
    """
    LAYERS esperadas:
      - ground, ground2 (tiles de chão; ONLY ground2 é caminhável)
      - obj (tiles sólidos com Collider)
      - entities (Object layer com Player)
      - waypoints (Object layer com pontos nomeados)
      - npc (Object layer com NPCs + propriedades de rotina)
    """
    def __init__(self, tmx_file: str):
        self.tmx_path = get_asset_path("maps", tmx_file)
        self.tmx_data: pytmx.TiledMap = load_pygame(self.tmx_path, pixelalpha=True)

        self.tile_width  = self.tmx_data.tilewidth
        self.tile_height = self.tmx_data.tileheight
        self.map_width   = self.tmx_data.width  * self.tile_width
        self.map_height  = self.tmx_data.height * self.tile_height

        self.spawn_points: dict[str, tuple[int,int]] = {}
        self.waypoints: dict[str, tuple[int,int]] = {}  # nome -> (tx,ty)

    
        self.navgrid = NavGrid(self.tmx_data, self.tile_width, self.tile_height, walk_layer_name="ground2")
        self.pathfinder = Pathfinder(self.navgrid)

    
    def load_map(self, entities: list[Entity]):
        self._parse_entities_layer()
        self._parse_waypoints_layer()
        self._load_ground_layers(entities)
        self._load_obj_colliders(entities)
        self._load_npcs(entities)  

    def get_player_spawn(self) -> tuple[int,int]:
        return self.spawn_points.get("player", (0,0))

    def get_waypoint_tile(self, name: str) -> tuple[int,int] | None:
        return self.waypoints.get(name.lower())

    def _parse_entities_layer(self):
        for layer in self.tmx_data.layers:
            if isinstance(layer, pytmx.TiledObjectGroup) and layer.name and layer.name.lower() == "entities":
                for obj in layer:
                    if (obj.name or "").lower().startswith("player"):
                        self.spawn_points["player"] = (int(obj.x), int(obj.y))

    def _parse_waypoints_layer(self):
        # Coleta waypoints nomeados, convertendo obj.x/y (pixels) para tiles (tx,ty)
        for layer in self.tmx_data.layers:
            if isinstance(layer, pytmx.TiledObjectGroup) and layer.name and layer.name.lower() == "waypoints":
                for obj in layer:
                    name = (obj.name or "").lower()
                    if not name:
                        continue
                    tx = int(obj.x // self.tile_width)
                    ty = int(obj.y // self.tile_height)
                    self.waypoints[name] = (tx, ty)

    def _load_ground_layers(self, entities: list[Entity]):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name and layer.name.lower() in ("ground", "ground2"):
                for x, y, gid in layer:
                    if isinstance(gid, int) and gid != 0:
                        img = self.tmx_data.get_tile_image_by_gid(gid)
                        if img:
                            e = Entity()
                            e.add(Position(x*self.tile_width, y*self.tile_height), Sprite(img))
                            entities.append(e)

    def _load_obj_colliders(self, entities: list[Entity]):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name and layer.name.lower() == "obj":
                for x, y, gid in layer:
                    if isinstance(gid, int) and gid != 0:
                        img = self.tmx_data.get_tile_image_by_gid(gid)
                        e = Entity()
                        if img:
                            e.add(Sprite(img))
                        e.add(Position(x*self.tile_width, y*self.tile_height), Collider(self.tile_width, self.tile_height))
                        entities.append(e)

    def _load_npcs(self, entities: list[Entity]):
        """
        Lê a object layer 'npc'.
        Propriedades de rotina no Tiled (exemplos):
          route_9  = "sala"
          route_14 = "patio"
          route_18 = "casa"
        """
        for layer in self.tmx_data.layers:
            if isinstance(layer, pytmx.TiledObjectGroup) and layer.name and layer.name.lower() == "npc":
                for obj in layer:
                    npc_type = (obj.type or obj.name or "").lower()
                    x, y = int(obj.x), int(obj.y)
                    props = {k.lower(): v for k, v in (obj.properties or {}).items()}

                    # monta rotina por NOME do waypoint (depois o sistema converte para tiles)
                    schedule_by_name = {}
                    for k, v in props.items():
                        if k.startswith("route_"):
                            try:
                                hour = int(k.split("_", 1)[1])
                            except:
                                continue
                            if isinstance(v, str):
                                schedule_by_name[hour] = v.lower()

                    npc = NPCFactory.create(npc_type, x, y, props)
                    if npc:
                        
                        if schedule_by_name:
                            npc.add(NPCRoutine(schedule_by_name))
                        entities.append(npc)
