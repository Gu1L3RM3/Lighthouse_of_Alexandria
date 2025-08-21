import pygame
from ui.widgets.widget import Widget
from pygame import Surface

class UIManager:
    def __init__(self):
        self.widgets :list[Widget]= []

    def add(self, widget: Widget):
        self.widgets.append(widget)

    def update(self, dt):
        for w in self.widgets:
            w.update(dt)

    def draw(self, surface:Surface):
        for w in self.widgets:
            
            w.draw(surface)

    def handle_event(self, event:pygame.event.Event):
        for w in self.widgets:
            
            w.handle_event(event)
