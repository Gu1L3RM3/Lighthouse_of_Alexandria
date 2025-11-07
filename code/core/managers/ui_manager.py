import pygame
from core.ui.widgets.widget import Widget
from pygame import Surface

class UIManager:
    def __init__(self):
        self.widgets :list[Widget]= []

    def add(self, *widget: Widget):
        for w in widget:
            self.widgets.append(w)

    def update(self, dt):
        for w in self.widgets:
            w.update(dt)

    def draw(self, surface:Surface):
        for w in self.widgets:
            
            w.draw(surface)
    def remove(self,widget:Widget):
        self.widgets.remove(widget)
    def clear(self):
        self.widgets.clear()
    def handle_event(self, event:pygame.event.Event):
        for w in self.widgets:
            w.handle_events(event)
