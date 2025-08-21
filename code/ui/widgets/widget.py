import pygame
from abc import ABC, abstractmethod
from pygame import Rect , Surface


class Widget(ABC):
    _next_id=1
    def __init__(self):
        self.id:int=Widget._next_id
        Widget._next_id+=1
    @abstractmethod
    def draw(self,surface:Surface):
        pass
    @abstractmethod
    def update(self,dt):
        pass
    def handle_events(self,event:pygame.event.Event):
        pass


    


    

