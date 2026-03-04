from pygame import Rect
from entities.itens.item import Item
from core.components.area_trigger import AreaTrigger
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.always_on_top import AlwaysOnTop
from core.components.label_component import LabelComponent
from core.components.light_component import LightComponent
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from entities.player import Player
from core.settings import FONT

class VoutageSourceItem(Item):
    def __init__(self, x, y, active,props):
        super().__init__(x, y, active,props)
        self.value = props['valor']
        self.area_id =  int(props.get('area', -1))
        self.img =  ResourceManager.get().load_image("eletric_components/voltage_source.png",size=(32,32))
        self.em =  EventManager.get()
        self.area_trigger = Rect(0,0,32,32)
        self.add(
            Position(x,y),
            AreaTrigger(self.area_trigger,active=active,on_entered=self.on_collect),
            Sprite(self.img),
            LabelComponent(f'V',self.value,FONT,font_size=10,offset_y=16),
            AlwaysOnTop(),
            LightComponent()
        )
    def on_active(self):
        area_trigger:AreaTrigger =  self.get(AreaTrigger)
        area_trigger.active = True
    
    def on_collect(self, entity):
        if not isinstance(entity,Player):
            return
        self.em.post(events={'type':'voltage_source_collected','value':self.value})
        self.em.post(events={'type':'kill_entity','id':self.id})
