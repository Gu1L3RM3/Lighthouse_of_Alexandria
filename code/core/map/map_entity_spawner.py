import pytmx
from core.ecs import Entity
from core.components.collider import Collider
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.npc_routine import NPCRoutine
from entities.npcs.npc_factory import NPCFactory
from entities.enemies.enemie import Enemie
from core.managers.entity_manager import EntityManager
from core.map.tile_map import TileMap

class MapEntitySpawner:
    def spawn_entities(self, tilemap: TileMap, entity_mn: EntityManager):

        for layer in tilemap.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name and layer.name.lower() == "obj":
                for x, y, gid in layer:
                    if isinstance(gid, int) and gid != 0:
                        img = tilemap.tmx_data.get_tile_image_by_gid(gid)
                        e = Entity()
                        if img:
                            e.add(Sprite(img))
                        e.add(Position(x * tilemap.tile_width, y * tilemap.tile_height), Collider(tilemap.tile_width, tilemap.tile_height))
                        entity_mn.add_entity(e)

        for layer in self._iter_layers(tilemap, "npc", pytmx.TiledObjectGroup):
            for obj in layer:
                npc_type = (obj.type or obj.name or "").lower()
                x, y = int(obj.x), int(obj.y)
                props = {k.lower(): v for k, v in (obj.properties or {}).items()}

                schedule = {
                    int(k.split("_", 1)[1]): v.lower()
                    for k, v in props.items()
                    if k.startswith("route_") and isinstance(v, str) and k.split("_", 1)[1].isdigit()
                }

                npc = NPCFactory.create(npc_type, x, y, props)
                if schedule:
                    npc.add(NPCRoutine(schedule))
                entity_mn.add_entity(npc)

        for layer in self._iter_layers(tilemap, "enemies", pytmx.TiledObjectGroup):
            for obj in layer:
                enemie = Enemie(obj.x, obj.y)
                entity_mn.add_entity(enemie)

    def _iter_layers(self, tilemap: TileMap, names: str | tuple[str, ...], layer_type):
        if isinstance(names, str):
            names = (names,)
        names = tuple(n.lower() for n in names)
        for layer in tilemap.tmx_data.layers:
            if isinstance(layer, layer_type) and layer.name and layer.name.lower() in names:
                yield layer
