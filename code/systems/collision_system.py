from typing import List,Tuple
from pygame import Rect
from core.ecs import System,Entity
from core.components.position import Position
from core.components.collider import Collider
from core.event_manager import EventManager
from itertools import combinations
#TODO: Layers de Colisão
class CollisionSystem(System):
    def __init__(self):
        super().__init__()
        self.event_manager=EventManager.get()
    def update(self, entities:List[Entity], dt:float):
        collidables=[
            (
                e,
                e.get(Collider).get_rect(
                    e.get(Position).x,
                    e.get(Position).y,
                )
            )
            for e in entities
            if e.has(Position) and e.has(Collider)
        ]
        # combinations gera tuplas de  (i,j) sendo i!=j  , evita duplicatas
        for (e1,rect1), (e2,rect2) in combinations(collidables,2):
            if rect1.colliderect(rect2):
                event={
                    'type':'collision',
                    'entities':(e1,e2),
                    'rects':(rect1,rect2)

                }
                self.event_manager.post(event)

        

        
        