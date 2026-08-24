from __future__ import annotations

from core.components.connectable import Connectable
from core.components.position import Position
from core.components.sprite import Sprite
from core.ecs import Entity
from core.managers.resource_manager import ResourceManager
from core.settings import CELL_SIZE, NODE_DEFAULT, NODE_SPRITE_MAP
from entities.circuit_editor.eletric_components import Node


GridPosition = tuple[int, int]


class NodeManager:
    """Maintains derived node sprites using a local spatial index."""

    def __init__(self):
        self.nodes: list[Node] = []
        self.rm = ResourceManager.get()
        self._entities_by_position: dict[GridPosition, set[Entity]] = {}
        self._position_by_entity: dict[int, GridPosition] = {}

    @staticmethod
    def _position(entity: Entity) -> GridPosition:
        position: Position = entity.get(Position)
        return int(position.x), int(position.y)

    @staticmethod
    def _rect(entity: Entity) -> tuple[int, int, int, int]:
        x, y = NodeManager._position(entity)
        sprite: Sprite = entity.get(Sprite)
        width, height = sprite.image.get_size()
        return x, y, width, height

    def _index(self, entity: Entity) -> None:
        if not entity.has(Position) or not entity.has(Sprite) or not entity.has(Connectable):
            return
        position = self._position(entity)
        self._entities_by_position.setdefault(position, set()).add(entity)
        self._position_by_entity[entity.id] = position
        if isinstance(entity, Node) and entity not in self.nodes:
            self.nodes.append(entity)

    def _unindex(self, entity: Entity) -> None:
        position = self._position_by_entity.pop(entity.id, None)
        if position is not None:
            entities = self._entities_by_position.get(position)
            if entities is not None:
                entities.discard(entity)
                if not entities:
                    del self._entities_by_position[position]
        if isinstance(entity, Node) and entity in self.nodes:
            self.nodes.remove(entity)

    def rebuild(self, entities: list[Entity]) -> None:
        self.nodes.clear()
        self._entities_by_position.clear()
        self._position_by_entity.clear()
        for entity in entities:
            self._index(entity)
        for node in tuple(self.nodes):
            self.update_nodes_around(node)

    def add_node(self, node: Node) -> None:
        if isinstance(node, Node) and node not in self.nodes:
            self.nodes.append(node)

    def clear_all_nodes(self) -> None:
        self.nodes.clear()
        self._entities_by_position.clear()
        self._position_by_entity.clear()

    def remove_node(self, node: Node) -> None:
        self._unindex(node)

    def _nearby_nodes(self, entity: Entity) -> set[Node]:
        x, y = self._position(entity)
        nearby: set[Node] = set()
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                position = (x + dx * CELL_SIZE, y + dy * CELL_SIZE)
                nearby.update(
                    candidate
                    for candidate in self._entities_by_position.get(position, ())
                    if isinstance(candidate, Node)
                )
        return nearby

    def refresh_after_remove(self, entity: Entity, entities: list[Entity]) -> None:
        if entity.id not in self._position_by_entity:
            self.rebuild(entities + [entity])
        affected = self._nearby_nodes(entity)
        self._unindex(entity)
        for node in affected:
            if node in self.nodes:
                self.update_nodes_around(node)

    def refresh_after_entity_rotated(self, entity: Entity, entities: list[Entity]) -> None:
        if entity.id not in self._position_by_entity:
            self.rebuild(entities)
        for node in self._nearby_nodes(entity):
            self.update_nodes_around(node)

    def update_node_sprite(self, node: Node, connections: set[str]) -> None:
        sprite: Sprite = node.get(Sprite)
        image_path = NODE_SPRITE_MAP.get(frozenset(connections), NODE_DEFAULT)
        sprite.image = self.rm.load_image(image_path)
        sprite.image_path = image_path

    def _local_candidates(self, node: Node) -> set[Entity]:
        x, y = self._position(node)
        candidates: set[Entity] = set()
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                candidates.update(self._entities_by_position.get((x + dx * CELL_SIZE, y + dy * CELL_SIZE), ()))
        return candidates

    def find_neighbors(self, node: Node, entities: list[Entity] | None = None) -> dict[str, Entity]:
        neighbors: dict[str, Entity] = {}
        node_left, node_top, node_width, node_height = self._rect(node)
        node_right = node_left + node_width
        node_bottom = node_top + node_height
        candidates = entities if entities is not None else self._local_candidates(node)

        for other in candidates:
            if other is node or not other.has(Connectable) or not other.has(Position) or not other.has(Sprite):
                continue
            left, top, width, height = self._rect(other)
            right = left + width
            bottom = top + height
            connections: Connectable = other.get(Connectable)

            if node_top == bottom and node_left == left:
                if {"bottom", "top"} & connections.base_connections or isinstance(other, Node):
                    neighbors["up"] = other
            elif node_bottom == top and node_left == left:
                if "top" in connections.base_connections or isinstance(other, Node):
                    neighbors["down"] = other
            elif node_left == right and node_top == top:
                if "right" in connections.base_connections or isinstance(other, Node):
                    neighbors["left"] = other
            elif node_right == left and node_top == top:
                if "left" in connections.base_connections or isinstance(other, Node):
                    neighbors["right"] = other
        return neighbors

    def update_nodes_around(self, node: Node, entities: list[Entity] | None = None) -> None:
        if not isinstance(node, Node):
            return
        connections = set(self.find_neighbors(node, entities))
        node.get(Connectable).base_connections = connections
        self.update_node_sprite(node, connections)

    def handle_new_entity(self, entity: Entity, entities: list[Entity]) -> None:
        if not self._position_by_entity and entities:
            self.rebuild(entities)
        self._index(entity)
        affected = self._nearby_nodes(entity)
        if isinstance(entity, Node):
            affected.add(entity)
        for node in affected:
            self.update_nodes_around(node)
