from core.ecs import Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.dropped import Dropped
from core.components.connectable import Connectable
from core.components.label_component import LabelComponent
from core.managers.resource_manager import ResourceManager
from core.settings import FONT,LABEL_OFFSET

class Resistor(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/resistor.png"
        surf=rm.load_image(img_path)
        labels = [
            {
                'text': 'R1', 
                'color': 'black', 
                'base_offset': (0, -LABEL_OFFSET) 
            },
            {
                'text': '10kΩ', 
                'color': 'blue', 
                'base_offset': (0, LABEL_OFFSET)
            }
        ]
        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            LabelComponent(labels,FONT),
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
            Connectable({'up','down','left','right'}),
            Dropped(),
        )

        

class VoutageSource(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/voltage_source.png"
        surf=rm.load_image(img_path)
        labels = [
            {
                'text': 'V1', 
                'color': 'black', 
                'base_offset': (0, -LABEL_OFFSET) 
            },
            {
                'text': '12V', 
                'color': 'blue', 
                'base_offset': (0, LABEL_OFFSET)
            }
        ]
        
        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            LabelComponent(labels,FONT),
            Connectable({'left','right'}),

            Dropped(),
           
        )

class CurrentSource(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/current_source.png"
        surf=rm.load_image(img_path)
        labels = [
            {
                'text': 'I1', 
                'color': 'black', 
                'base_offset': (0, -LABEL_OFFSET) 
            },
            {
                'text': '5A', 
                'color': 'blue', 
                'base_offset': (0, LABEL_OFFSET)
            }
        ]

        self.add(
            Position(x,y),
            Sprite(surf,image_path=img_path),
            LabelComponent(labels,FONT),
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
            Sprite(surf,img_path),
            Connectable({'up'}),
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