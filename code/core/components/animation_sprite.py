from pygame import Surface
from core.ecs import Component
from typing import Dict,List

class AnimateSprite(Component):
    def __init__(self,animations:Dict[str,List[Surface]],fps:int=8,loop:bool = True):
        self.animations=animations
        self.fps=fps
        self.loop=loop

        self.current_animation = None
        self.current_frame=0
        self.time_acc=0.0
        self.image=None
        self.done=False
    def play(self):
        pass
        