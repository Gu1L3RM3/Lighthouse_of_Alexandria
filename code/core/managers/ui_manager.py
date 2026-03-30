import pygame
from core.ui.widgets.widget import Widget
from pygame import Surface
from core.ui.widgets.alert_dialog import AlertDialog

class UIManager:
    def __init__(self):
        self.widgets :list[Widget]= []

    def add(self, *widget: Widget):
        for w in widget:
            self.widgets.append(w)

    def update(self, dt):
        modal = self._get_top_modal()
        if modal is not None:
            modal.update(dt)
            return
        for w in self.widgets:
            w.update(dt)

    def draw(self, surface:Surface):
        modal = self._get_top_modal()
        if modal is not None:
            for w in self.widgets:
                if w is modal:
                    continue
                w.draw(surface)
            modal.draw(surface)
            return
        for w in self.widgets:
            
            w.draw(surface)
    def remove(self,widget:Widget):
        self.widgets.remove(widget)
    def clear(self):
        self.widgets.clear()
    def handle_event(self, event:pygame.event.Event):
        modal = self._get_top_modal()
        if modal is not None:
            modal.handle_events(event)
            return
        for w in self.widgets:
            w.handle_events(event)

    def _get_top_modal(self):
        for widget in reversed(self.widgets):
            if isinstance(widget, AlertDialog):
                return widget
        return None
