from pygame import Rect
from core.ecs import Entity
from core.components.collider import Collider
from core.components.position import Position
from core.components.sprite import Sprite
from core.managers.resource_manager import ResourceManager
from core.components.area_trigger import AreaTrigger
from core.components.velocity import Velocity
from core.components.tags import EletronTag
from core.components.always_on_top import AlwaysOnTop
from core.components.light_component import LightComponent
from core.components.electron_flow import ElectronFlow
from core.components.dynamic_collision import DynamicCollision
class Eletron(Entity):
    def __init__(self,x,y):
        super().__init__()
        img = ResourceManager.get().load_image('circuit_components/eletron.png')
        spr =  Sprite(img)

        self.add(
            Position(x,y),
            spr,
            Collider(16,16),
            EletronTag(),
            Velocity(),
            LightComponent(),
            ElectronFlow(),
            DynamicCollision(enabled=False),
            )
        

class VoltageSource(Entity):
    def __init__(self,x,y):
        super().__init__()
        img = ResourceManager.get().load_image('circuit_components/voltage_source.png')
        spr =  Sprite(img)
        trigger_rect = spr.rect.inflate(12, 12)
        self.add(
            Position(x,y),
            AreaTrigger(trigger_rect,on_entered=self.on_enter),
            AlwaysOnTop(),
            spr,

            )
    def on_enter(self,entity:Entity):
        if not entity.has(EletronTag):
            return
        if entity.has(ElectronFlow):
            flow: ElectronFlow = entity.get(ElectronFlow)
            flow.boost()


class Resistor(Entity):
    def __init__(self,x,y):
        super().__init__()
        img = ResourceManager.get().load_image('circuit_components/resistor.png')
        spr =  Sprite(img)
        trigger_rect = spr.rect.inflate(10, 8)

        self.add(
            Position(x,y),
            AreaTrigger(trigger_rect,on_entered=self.on_enter),
            spr,
            AlwaysOnTop()

            )
    def on_enter(self,entity:Entity):
        if not entity.has(EletronTag):
            return
        if entity.has(ElectronFlow):
            flow: ElectronFlow = entity.get(ElectronFlow)
            flow.brake()


class Light(Entity):
    def __init__(self,x,y):
        super().__init__()
        self.light_off = ResourceManager.get().load_image("circuit_components/lamp_off.png")
        self.light_on  = ResourceManager.get().load_image("circuit_components/lamp_on.png")
        spr = Sprite(self.light_off)
        self.area =Rect(x,y,32,32)
        self.add(
           spr,
           Position(x,y),
           AreaTrigger(spr.rect,on_entered=self.on_enter,on_exit=self.on_exit),
           AlwaysOnTop(),
        )
    def on_enter(self,entity:Entity):
        if entity.has(EletronTag):
            spr :Sprite=self.get(Sprite)
            spr.image = self.light_on
            
    def on_exit(self,entity:Entity):
        if entity.has(EletronTag):
            spr :Sprite=self.get(Sprite)
            spr.image = self.light_off
