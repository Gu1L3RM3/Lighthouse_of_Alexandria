from core.ecs import System
from core.components.position import Position
from core.components.velocity import Velocity


class MovementSystem(System):
    def update(self, entities, dt):
        for e in entities:
            if e.has(Position) and e.has(Velocity):
                pos:Position=e.get(Position)
                vel:Velocity=e.get(Velocity)
                
                pos.pos+=vel.vel*dt
