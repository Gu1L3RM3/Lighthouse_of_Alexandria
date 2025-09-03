from core.ecs import Component


class PlayerFollower(Component):
    def __init__(self,interval_to_update:float,speed:int=20):
        self.interval_to_update=interval_to_update
        self.speed =  speed
        