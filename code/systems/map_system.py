from pytmx.util_pygame import load_pygame
import pytmx
from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.sprite import Sprite
from core.config import get_asset_path
from entities.npcs.npc_factory import NPCFactory

class MapSystem:
    def __init__(self, tmx_file: str):
        self.tmx_path = get_asset_path("maps", tmx_file)
        self.tmx_data: pytmx.TiledMap = load_pygame(self.tmx_path, pixelalpha=True)
        self.spawn_points = {}

        self.tile_width = self.tmx_data.tilewidth
        self.tile_height = self.tmx_data.tileheight
        self.map_width = self.tmx_data.width * self.tile_width
        self.map_height = self.tmx_data.height * self.tile_height

        

    def load_map(self, entities: list[Entity]):
        self._parse_objects()
        self._load_ground_layers(entities)
        self._load_obj_colliders(entities)
        self._load_npcs(entities)

    def get_player_spawn(self):
        return self.spawn_points.get("player", (0, 0))

    def _parse_objects(self):
        """Lê a camada 'Player' para definir pontos de spawn."""
        for layer in self.tmx_data.layers:
            if isinstance(layer, pytmx.TiledObjectGroup) and layer.name.lower() == "entities":
                for obj in layer:
                    if obj.name.lower().startswith("player"):
                        self.spawn_points["player"] = (obj.x, obj.y)

    def _load_ground_layers(self, entities: list[Entity]):
        """Carrega camadas de chão: 'ground' e 'ground2'."""
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name.lower() in ("ground", "ground2"):
                for x, y, gid in layer:
                    if isinstance(gid, int) and gid != 0:
                        image = self.tmx_data.get_tile_image_by_gid(gid)
                        if image:
                            e = Entity()
                            e.add(
                                Position(x * self.tile_width, y * self.tile_height),
                                Sprite(image)
                            )
                            entities.append(e)


    def _load_obj_colliders(self, entities: list[Entity]):
        """Carrega a camada 'obj' como blocos sólidos."""
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name.lower() == "obj":
                for x, y, gid in layer:
                    if isinstance(gid, int) and gid != 0:
                        image = self.tmx_data.get_tile_image_by_gid(gid)
                        if image:
                            e = Entity()
                            e.add(
                                Position(x * self.tile_width, y * self.tile_height),
                                Sprite(image),
                                Collider(self.tile_width, self.tile_height)
                            )
                            entities.append(e)

    def _load_npcs(self,entities:list[Entity]):
        for layer in self.tmx_data.layers:
            if hasattr(layer,"name") and layer.name.lower() == "npc":
                for obj in layer:
                    npc_type =obj.name.lower()
                    if npc_type:
                        npc = NPCFactory.create(npc_type,obj.x,obj.y,obj.properties)
                        entities.append(npc)
