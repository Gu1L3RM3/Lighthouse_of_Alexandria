from pygame import Rect
from core.ecs import Entity
from core.managers.resource_manager import ResourceManager
from core.managers.scene_manager import SceneManager
from core.components.position import Position
from core.components.animation_sprite import AnimateSprite
from core.components.sprite import Sprite
from core.components.area_trigger import AreaTrigger
from core.components.always_on_top import AlwaysOnTop
from core.components.light_component import LightComponent
class Door(Entity):
    def __init__(self,x,y,props=None):
        super().__init__()
        self.props = props or {}
        self.next_scene = self.props.get('next_scene', '')
        self.animations =  ResourceManager.get().load_sprite_sheet('door',(48,32))
        
        
        trigger_area:Rect = Rect(x,y,50,50)

        
        

        self.add(
            AnimateSprite(
                self.animations
            ),
            Position(x,y),
            AreaTrigger(
                trigger_area,
                once=True,
                active=False,
                on_entered=self.enter
                

            ),
            
            AlwaysOnTop()
        )


    def enter(self,id):
        SceneManager.get().start_fade(self.next_scene)
        
    def active_door(self):
        area_trigger:AreaTrigger = self.get(AreaTrigger)
        area_trigger.active=True
    

    def open(self,event):
        animate_sprite:AnimateSprite= self.get(AnimateSprite)
        self.add(
            Sprite(
                self.animations['idle'][0]
            ),
            LightComponent(),


        ),
        animate_sprite.play("idle",loop=False,on_finish=self.active_door)


