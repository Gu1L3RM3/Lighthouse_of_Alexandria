import pytmx
from core.ecs                     import Entity

from core.components.collider     import Collider
from core.components.position     import Position
from core.components.sprite       import Sprite

from core.managers.entity_manager import EntityManager
from core.map.tile_map            import TileMap
from core.map.spawners.spawn      import *
from typing                       import  Dict


class MapEntitySpawner:
    def __init__(self):
        self._spawners: Dict[str, EntitySpawner] = {}
        self._register_default_spawners()

    def _register_default_spawners(self):
        self.register_spawner("circuito",CircuitSpawner())
        self.register_spawner("npc", NPCSpawner())
        self.register_spawner("enemies", EnemySpawner())
        self.register_spawner("areas_dialog",DialogueAreaSpawner())
        self.register_spawner("attention_point",AttetionSpawner())
        self.register_spawner("itens",ItemSpawner())
        self.register_spawner("door",DoorSpawner())
        self.register_spawner("player",PlayerSpawn())
        self.register_spawner("fall_ground",FallGroundSpawner())
        self.register_spawner("iron_gate",IronGateSpawner())

    def register_spawner(self, layer_name: str, spawner: EntitySpawner):
        self._spawners[layer_name.lower()] = spawner

    def spawn_entities(self, tilemap: TileMap, entity_mn: EntityManager):
        
        for layer in tilemap.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name and layer.name.lower() == "obj":
                self._spawn_from_tile_layer(layer, tilemap, entity_mn)
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name and layer.name.lower() == "obj2":
                self._spawn_from_tile_layer(layer, tilemap, entity_mn)

        for layer in tilemap.tmx_data.objectgroups:
            layer_name = (layer.name or "").lower()
            spawner = self._spawners.get(layer_name)
            if spawner and isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    spawner.spawn(obj, entity_mn, tilemap)

                    


    def _spawn_from_tile_layer(self, layer: pytmx.TiledTileLayer, tilemap: TileMap, entity_mn: EntityManager):
        for x, y, gid in layer:
            if isinstance(gid, int) and gid != 0:
                img = tilemap.tmx_data.get_tile_image_by_gid(gid)
                e = Entity()
                if img:
                    e.add(Sprite(img))
                e.add(Position(x * tilemap.tile_width, y * tilemap.tile_height),
                      Collider(tilemap.tile_width, tilemap.tile_height))
                entity_mn.add_entity(e)