from core.ecs import Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.dropped import Dropped
from core.components.connectable import Connectable
from core.components.label_component import LabelComponent
from core.managers.resource_manager import ResourceManager
from core.settings import FONT

class Resistor(Entity):
    def __init__(self,x,y,id,value:str):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/resistor.png"
        surf=rm.load_image(img_path)

        name = f'R{id}'

        

        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            LabelComponent(name,value,FONT),
            Connectable({'left','right'}),
            Dropped(),
           
        )

class Node(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/node/node_all.png"
        surf=rm.load_image(img_path)

        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            Connectable({'top','bottom','left','right'}),
            Dropped(),
        )

        

class VoltageSource(Entity):
    def __init__(self,x,y,id,value:str="10"):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/voltage_source.png"
        surf=rm.load_image(img_path)

        name=f'V{id}'
        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            LabelComponent(name,value,FONT),
            Connectable({'left','right'}),
            Dropped(),
           
        )

class CurrentSource(Entity):
    def __init__(self,x,y,id,value:str="10"):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/current_source.png"
        surf=rm.load_image(img_path)

        name = f'I{id}'
        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            LabelComponent(name,value,FONT),
            Connectable({'left','right'}),
            Dropped(),
           
        )

class Ground(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/gnd.png"
        surf=rm.load_image(img_path)

        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            Connectable({'top'}),
            Dropped(),
           
        )
        
class Wire(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/wire.png"
        surf=rm.load_image(img_path)
        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            Connectable({'left','right'}),
            Dropped(),
           
        )
