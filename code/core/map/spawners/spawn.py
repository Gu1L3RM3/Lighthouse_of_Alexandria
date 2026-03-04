import pytmx
import json
from typing import Type
from entities.animated_tiles.door import Door
from entities.animated_tiles.fall_ground import FallGround
from entities.animated_tiles.iron_gate import IronGate
from entities.player import Player
from entities.enemies.enemy_factory import EnemyFactory
from entities.dialogue_area import DialogueArea
from entities.attention_point import AttentionPoint
from entities.itens.item import Item
from entities.itens.old_paper import OldPaper
from entities.itens.key import Key
from entities.itens.control_pannel import ControlPannel
from entities.itens.resistor_item import ResistorItem
from entities.itens.voltage_source_item import VoutageSourceItem
from entities.itens.current_source_item import CurrentSourceItem
from entities.itens.crystal_invisibility_item import CrystalInvisibilityItem
from entities.itens.anti_reaggro_flask_item import AntiReaggroFlaskItem
from entities.animate_circuit.circuit_components import *
from entities.npcs.npc_factory import NPCFactory
from core.components.npc_routine import NPCRoutine
from core.managers.entity_manager import EntityManager
from core.map.tile_map import TileMap
from abc import ABC,abstractmethod
from typing import Type

class EntitySpawner(ABC):
    """
    Define a interface para qualquer classe que possa criar entidades a partir de um objeto de mapa.
    Qualquer spawner concreto DEVE implementar o método spawn.
    """
    @abstractmethod
    def spawn(self, obj: pytmx.TiledObject, entity_mn: EntityManager, tilemap: TileMap):
        pass


class ItemSpawner(EntitySpawner):
    def __init__(self):
        super().__init__()  
        self.itens: dict[str, Type[Item]] = {
            'old_paper': OldPaper,
            'key': Key,
            'control_pannel':ControlPannel,
            'resistor':ResistorItem,
            'voltage_source':VoutageSourceItem,
            'current_source':CurrentSourceItem,
            'crystal_invisibility': CrystalInvisibilityItem,
            'anti_reaggro_flask': AntiReaggroFlaskItem,
        }
     

    def spawn(self, obj, entity_mn: "EntityManager", tilemap):

        properties = obj.properties.copy()
        properties['tmx_file'] = tilemap.tmx_file
        

        active = obj.properties.get('active_status', True)

        item_class = self.itens.get(obj.name)
        if item_class is None:
            ValueError(f"Tipo de item '{obj.name}' não reconhecido em ItemSpawner.")
            return
        item: Item = item_class(
            obj.x,
            obj.y,
            active,
            properties,
            
        )

        entity_mn.add_entity(item)


class FallGroundSpawner(EntitySpawner):
    def spawn(self, obj, entity_mn, tilemap):
        fall_ground = FallGround(obj.x,obj.y)
        entity_mn.add_entity(fall_ground)

class IronGateSpawner(EntitySpawner):
    def spawn(self, obj, entity_mn, tilemap):
        iron_gate = IronGate(obj.x,obj.y,props=obj.properties)
        entity_mn.add_entity(iron_gate)


class CircuitSpawner(EntitySpawner):
    def __init__(self):
        self.components= {
            'eletron':Eletron,
            'voltage_source':VoltageSource,
            'resistor':Resistor,
            'light':Light
        }
    def spawn(self, obj, entity_mn, tilemap):
        component =  self.components.get(obj.name)
        entity_mn.add_entity(component(obj.x,obj.y))


class DialogueAreaSpawner(EntitySpawner):
    def spawn(self, obj, entity_mn, tilemap):
        list_dialogue = obj.properties["dialogo"].split(";")
        active_status: bool = obj.properties["active_status"]
        auto_start = bool(obj.properties.get("auto_start", False))
        stealth_bonus_duration = float(obj.properties.get("stealth_bonus_duration", 4.0))
        stealth_bonus_enabled = obj.properties.get("stealth_bonus_enabled", True)
        stealth_bonus_once = obj.properties.get("stealth_bonus_once", True)

        dialogue_area = DialogueArea(
            obj.x,obj.y,
            obj.width,
            obj.height,
            list_dialogue,
            obj.name,
            active_status,
            auto_start=auto_start,
            stealth_bonus_enabled=stealth_bonus_enabled,
            stealth_bonus_duration=stealth_bonus_duration,
            stealth_bonus_once=stealth_bonus_once,

        )
        entity_mn.add_entity(dialogue_area)

class DoorSpawner(EntitySpawner):
    def spawn(self, obj, entity_mn, tilemap):
        if obj.name !='door':
            return
        entity_mn.add_entity(Door(obj.x, obj.y, obj.properties))
        
class AttetionSpawner(EntitySpawner):

    def spawn(self, obj, entity_mn, tilemap):
        
        
        list_positions = self.get_list_positions(obj.properties['positions'])
        
        entity_mn.add_entity(
            AttentionPoint(
                obj.x,obj.y,
                list_positions
            )

        )
    def get_list_positions(self,positions:str)->list[tuple[int,int]]:
        
        dicionaries = json.loads(positions)
        list_positions=[(int(dict['x']),int(dict['y'])) for dict in dicionaries]
        return list_positions

    
        
            

 

class NPCSpawner(EntitySpawner):
    
    def spawn(self, obj: pytmx.TiledObject, entity_mn: EntityManager, tilemap: TileMap):
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
class PlayerSpawn(EntitySpawner):
    def spawn(self, obj, entity_mn, tilemap):
        player = Player(obj.x,obj.y)
        entity_mn.add_entity(player)

class EnemySpawner(EntitySpawner):
    def __init__(self):
        self._route_cache: dict[str, dict[str, list[tuple[int, int]]]] = {}

    def spawn(self, obj: pytmx.TiledObject, entity_mn: EntityManager, tilemap: TileMap):
        routes = self._get_routes(tilemap)
        props = {k.lower(): v for k, v in (obj.properties or {}).items()}
        enemy_type = (obj.type or props.get("enemy_type") or obj.name or "spider").lower()
        route_id = str(props.get("route_id", "")).lower().strip()

        route = routes.get(route_id) if route_id else None
        if route:
            start_tile = (
                int(obj.x // tilemap.tile_width),
                int(obj.y // tilemap.tile_height),
            )
            if route[0] != start_tile:
                route = [start_tile, *route]

        enemy = EnemyFactory.create(enemy_type, obj.x, obj.y, props=props, route=route)
        entity_mn.add_entity(enemy)

    def _get_routes(self, tilemap: TileMap) -> dict[str, list[tuple[int, int]]]:
        cache_key = tilemap.tmx_file
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]

        routes: dict[str, list[tuple[int, tuple[int, int]]]] = {}
        for layer in tilemap.tmx_data.objectgroups:
            if (layer.name or "").lower() != "enemy_routes":
                continue
            for obj in layer:
                properties = {k.lower(): v for k, v in (obj.properties or {}).items()}
                route_id = str(properties.get("route_id") or obj.name or "").lower().strip()
                if not route_id:
                    continue
                order = int(properties.get("order", 0))
                tile_point = (
                    int(obj.x // tilemap.tile_width),
                    int(obj.y // tilemap.tile_height),
                )
                routes.setdefault(route_id, []).append((order, tile_point))

        normalized_routes: dict[str, list[tuple[int, int]]] = {}
        for route_id, points in routes.items():
            ordered_points = sorted(points, key=lambda p: p[0])
            normalized_routes[route_id] = [tile for _, tile in ordered_points]

        self._route_cache[cache_key] = normalized_routes
        return normalized_routes
