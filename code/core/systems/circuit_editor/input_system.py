import pygame
from pygame import Rect
from pathlib import Path
from core.circuit_tools.serialization_manager import SerializationManager
from core.ecs import System, Entity
from core.managers.entity_manager import EntityManager
from entities.circuit_editor.eletric_components import *
from entities.circuit_editor.edit_components import *
from core.components.position import Position
from core.components.dropped import Dropped
from core.components.always_on_top import AlwaysOnTop
from core.components.sprite import Sprite
from core.components.label_component import LabelComponent
from core.managers.node_manager import NodeManager
from core.circuit_tools.storage_circuit_manager import StorageCircuitManager
from core.circuit_tools.lt_spice_generate import LtSpiceGenerate
from core.circuit_tools.solve_circuit import CircuitSolver
from core.managers.circuit_manager import CircuitManager
from typing import Type


class InputSystem(System):
    def __init__(self,
                 entity_manager: EntityManager,
                 grid_rects: list[Rect],
                 node_mn:NodeManager,
                 file:str,
             
                 storage_manager:StorageCircuitManager,
                 debug_mode:bool,
                 ):

        super().__init__()
        Path("circuitos").mkdir(exist_ok=True)
        Path("ltspice").mkdir(exist_ok=True)

        self.file_list =  file.split('/')
        self.file = self.file_list[-1]

        level = Path(*self.file_list[:-1])

        self.full_file = file  # ex: "generic_levels_3/fase_3/pannel1"
        self.json_file = str(level / f"{self.file}.json")

        filename_only = Path(self.file).name
                 

        self.net_file      = str(Path("ltspice") / level / f"{filename_only}.net")
        self.lt_spice_file = str(Path("ltspice") / level / f"{filename_only}.asc")
        self.show_mouse = True
        self.select_mode = False
        self.brush: Entity | None = None
        self.active_tool: str | None = None
        self.entity_manager = entity_manager
        self.node_manager   = node_mn
        self.grid_rects = grid_rects
        self.storage_manager=storage_manager

        self.debug_mode= debug_mode
        self.angle_deg=90


    def set_brush(self, brush_type: str | None ,value:str|None=None):
        if self.brush:
            self.entity_manager.remove_entity(self.brush)
            self.brush = None
        self.active_tool=brush_type

        brush_map = {
            "Resistor": Resistor,
            "wire": Wire,
            "gnd": Ground,
            "CurrentSource": CurrentSource,
            "VoutageSource": VoutageSource,
            "node":Node,
            "select": Select,
            "rotate": Rotate,
            "delete": Delete,
        }

        cls = brush_map.get(brush_type)
        if not cls:
            raise Exception(f"Invalid brush type: {brush_type}")

        x, y = pygame.mouse.get_pos()
        entity: Entity = self.set_label(cls,x,y,value)
        
        entity.add(AlwaysOnTop())

        

        self.entity_manager.add_entity(entity)
        self.brush = entity
        self.show_mouse = False
    def set_label(self, obj: Type[Entity], x, y, value: str) -> Entity:
        if obj not in {Resistor, CurrentSource, VoutageSource}:
            return obj(x, y)

        entities = self.entity_manager.get_entities_by_class(obj)

        # Coleta todos os IDs já usados para este tipo de componente
        used_ids = set()
        for e in entities:
            label: LabelComponent = e.get(LabelComponent)
            if label and label.name:
                try:
                    # nome é do tipo "R1", "V2", "I3" — extrai o número
                    used_ids.add(int(''.join(filter(str.isdigit, label.name))))
                except ValueError:
                    pass

        # Menor inteiro positivo não usado
        new_id = 1
        while new_id in used_ids:
            new_id += 1

        return obj(x, y, id=new_id, value=value)
    def update(self, entity_manager, dt):
        self.update_brush_position()
    def can_change(self,target:Entity):
        dropped:Dropped=target.get(Dropped)
        if dropped.can_dropped:
            return True
        return False
    def select_entity(self):
        if not isinstance(self.brush, Select):
            return

        target = self.entity_manager.check_collision(self.brush)
        if not target:
            return
        
        if not self.can_change(target):
            return

        if self.brush:
            self.entity_manager.remove_entity(self.brush)
            self.brush = None

        target.add(AlwaysOnTop())
        self.entity_manager.add_entity(target)
        self.brush = target
        self.show_mouse = False
        self.select_mode = True

        
        label :LabelComponent=target.get(LabelComponent)
        self.storage_manager.add_component(target.__class__.__name__,label.value) 


    def delete_entity(self):
        if not isinstance(self.brush, Delete):
            return

        target = self.entity_manager.check_collision(self.brush)
        if not target:
            return
        if not self.can_change(target):
            return
        self.entity_manager.remove_entity(target)
        entities=self.entity_manager.get_entities()
        self.node_manager.refresh_after_remove(target,entities)
        if not target.has(LabelComponent):
            return
        label :LabelComponent=target.get(LabelComponent)
        self.storage_manager.add_component(target.__class__.__name__,label.value)    
    def clear_all(self):
        if self.debug_mode:
            for entity in self.entity_manager.get_entities_with(Dropped,
                                                                ):
                self.entity_manager.remove_entity(entity)
                if entity.has(LabelComponent):
                    label:LabelComponent = entity.get(LabelComponent)
                    self.storage_manager.add_component(entity.__class__.__name__,label.value)
            return
                
                
        for entity in self.entity_manager.get_entities_with(Dropped,
                                                            filter=lambda e: self.can_change(e)):
            self.entity_manager.remove_entity(entity)
            if entity.has(LabelComponent):
                label:LabelComponent = entity.get(LabelComponent)
                self.storage_manager.add_component(entity.__class__.__name__,label.value)
            
    

        
        self.storage_manager.set_completly_storage()
    def rotate_brush(self):
        if not self.brush or not self.brush.has(Connectable):
            return
        spr:Sprite = self.brush.get(Sprite)
        con:Connectable = self.brush.get(Connectable)
        con.set_connections(self.angle_deg)

        spr.rotate(self.angle_deg)
    def rotate_entity(self):
        if not isinstance(self.brush, Rotate):
            return

        target = self.entity_manager.check_collision(self.brush)
        if not target:
            return

        sprite: Sprite = target.get(Sprite)
        connectable: Connectable = target.get(Connectable)

        
        sprite.rotate(self.angle_deg)
        connectable.set_connections(self.angle_deg)

        entities = self.entity_manager.get_entities()
        self.node_manager.refresh_after_entity_rotated(target, entities)


    def handle_canvas_actions(self):
        self.drop_entity()
        self.delete_entity()
        self.rotate_entity()
        self.select_entity()
    def change_name_component(self):
        if not self.brush.has(LabelComponent):
            return

        label: LabelComponent = self.brush.get(LabelComponent)
        
        prefix = label.name[0]         
        number_part = label.name[1:]    
        try:
            number = int(number_part) + 1
        except ValueError:
            number = 1  

        label.name = f"{prefix}{number}"

    def drop_entity(self):
        if not self.brush or not self.brush.has(Dropped):
            return

        entities = self.entity_manager.get_entities()
        entities.remove(self.brush)

        rects = [e.get(Sprite).rect for e in entities if e.has(Sprite)]
        sprite: Sprite = self.brush.get(Sprite)
        if sprite.rect.collidelist(rects) != -1:
            return

        new_entity = self.brush.copy()
        new_entity.remove(AlwaysOnTop)
        self.entity_manager.add_entity(new_entity)
        self.change_name_component()
        
        self.node_manager.handle_new_entity(new_entity, entities)

        if self.brush.has(LabelComponent):
            label :LabelComponent=self.brush.get(LabelComponent)
            has_component =self.storage_manager.remove_component(self.brush.__class__.__name__,label.value) 
            if not has_component:
                self.exit_current_tool()
                return
            
        if not self.select_mode:
            return
        self.select_mode = False

        if self.active_tool == "select":
            self.set_brush("select")




        
    def exit_current_tool(self, set_mouse: bool = True):
        if self.brush:
            self.entity_manager.remove_entity(self.brush)
            self.brush = None

        if set_mouse:
            self.show_mouse = True
            pygame.mouse.set_visible(True)

    def update_brush_position(self):
        if not self.brush:
            return

        pos: Position = self.brush.get(Position)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for rect in self.grid_rects:
            if rect.collidepoint((mouse_x, mouse_y)):
                pos.xy = rect.topleft
                return
    def set_voltage_current_resistors(self,):
        resistors = self.entity_manager.get_entities_by_class(Resistor)
        for resistor in resistors:
            label:LabelComponent = resistor.get(LabelComponent)
            label.voltage = str(self.resistor_results[label.name]['voltage']['label'])
            label.current = str(self.resistor_results[label.name]['current']['label'])


    def solve_circuit(self):
        try:
            circuit_solver= CircuitSolver(self.net_file)
            self.resistor_results = circuit_solver.get_resistor_results()
            self.total_values = circuit_solver.get_total_values()
            CircuitManager.get().add_circuit_values(self.full_file,self.resistor_results)
            CircuitManager.get().add_total_values(self.full_file,self.total_values)
            self.set_voltage_current_resistors()

            return True
        except Exception as e:
            print(f"Cannot solve circuit {e}")
            return False

    def _is_debug_mode(self):
        if not self.debug_mode:
            return
        entities_with_dropped = self.entity_manager.get_entities_with(Dropped)
        for entity in entities_with_dropped:
            dropped:Dropped=entity.get(Dropped)
            dropped.can_dropped=False

    def save_circuit(self):
        self.exit_current_tool()
        self._is_debug_mode()
        entities_to_save = self.entity_manager.get_entities()
        
        SerializationManager.save_entities_to_json(entities_to_save,self.json_file)
        LtSpiceGenerate(self.json_file,self.net_file,self.lt_spice_file,self.entity_manager).run()
        self.storage_manager.save_eletric_storage()
        self.solve_circuit()
        

    def load_circuit(self):
        self.entity_manager.clear_all_entities(excepts=[self.brush]) 
        self.node_manager.clear_all_nodes()
        loaded_entities = SerializationManager.load_entities_from_json(self.json_file)
        for entity in loaded_entities:
            self.entity_manager.add_entity(entity)
            self.node_manager.add_node(entity)
