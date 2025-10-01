from core.settings import NODE_OPPOSITE, NODE_SPRITE_MAP, NODE_DEFAULT
from core.components.connectable import Connectable
from core.components.sprite import Sprite
from core.managers.resource_manager import ResourceManager
from entities.circuit_editor.eletric_components import Node
from core.ecs import Entity

class NodeManager:
    def __init__(self):
        self.nodes: list[Node] = []
        self.rm = ResourceManager.get()
        
    def add_node(self, node: Node):
        
        if isinstance(node, Node):
            self.nodes.append(node)
    def clear_all_nodes(self):
        self.nodes.clear()


    def remove_node(self, node: Node):
        if node in self.nodes:
            self.nodes.remove(node)

    def refresh_after_remove(self, entity, entities: list):
        
        if not isinstance(entity, Node):
            
            for node in self.nodes:
                self.update_nodes_around(node, entities)
            return
        self.remove_node(entity)
        for node in self.nodes:
            
            self.update_nodes_around(node, entities)



    def refresh_after_entity_rotated(self, entity, entities: list):
        if not isinstance(entity,Node):
            for node in self.nodes:
                self.update_nodes_around(node,entities)
            return
        
        self.update_nodes_around(entity, entities)
  


    def update_node_sprite(self, node: Node, connections: set[str]):
        spr: Sprite = node.get(Sprite)
        image_path = NODE_SPRITE_MAP.get(frozenset(connections), NODE_DEFAULT)
        spr.image = self.rm.load_image(image_path)
        spr.image_path =  image_path

    def find_neighbors(self, node: Node, entities: list[Entity]) -> dict[str, Entity]:
        neighbors = {}
        spr_node: Sprite = node.get(Sprite)
        node_rect = spr_node.rect

        for other in entities:
            if other is node or not other.has(Connectable):
                continue

            spr_other: Sprite = other.get(Sprite)
            other_rect = spr_other.rect
            conn_other :Connectable=other.get(Connectable)
            
            
            if node_rect.top == other_rect.bottom and node_rect.left == other_rect.left:
                if 'bottom'in conn_other.base_connections or 'top' in conn_other.base_connections or isinstance(other,Node):
                    neighbors["up"] = other
            elif node_rect.bottom == other_rect.top and node_rect.left == other_rect.left:
                if 'top' in conn_other.base_connections or isinstance(other,Node):
                    neighbors["down"] = other
            elif node_rect.left == other_rect.right and node_rect.top == other_rect.top:
                if 'right' in conn_other.base_connections or isinstance(other,Node):
                    neighbors["left"] = other
            elif node_rect.right == other_rect.left and node_rect.top == other_rect.top:
                if 'left' in conn_other.base_connections or isinstance(other,Node):
                    neighbors["right"] = other
        
        return neighbors

    def update_nodes_around(self, node: Node, entities: list[Entity]):
        
        if not isinstance(node, Node):
            return
        current_conn: Connectable = node.get(Connectable)
        neighbors = self.find_neighbors(node, entities)

        current_conn.base_connections = set(neighbors.keys())
        self.update_node_sprite(node, current_conn.base_connections)

        for direction, neighbor in neighbors.items():
            conn_neighbor: Connectable = neighbor.get(Connectable)
            conn_neighbor.base_connections.add(NODE_OPPOSITE[direction])

            if isinstance(neighbor, Node):
                self.update_node_sprite(neighbor, conn_neighbor.base_connections)

    def handle_new_entity(self, entity: Entity, entities: list[Entity]):
        if not isinstance(entity,Node):
            for node in self.nodes:
                self.update_nodes_around(node, entities + [entity])
            return
        
        self.add_node(entity)
        self.update_nodes_around(entity, entities)