from pygame import Surface
from core.ui.widgets.widget import Widget
from core.ui.widgets.gesture_detector import GestureDetector
from core.ui.widgets.text import Text

class Button(Widget):
    def __init__(self,
                 gesture_detector: GestureDetector,
                 init_surface: Surface,
                 surface_pressed: Surface,
                 pos_center: tuple[int, int],
                 text: Text | None = None,
                 draw_gesture_detector: bool = False,
                 ):
        self.gesture_detector = gesture_detector
        self.text = text
        self.init_surface = init_surface
        self.surface_pressed = surface_pressed
        self.current_surf = self.init_surface
        self.pos_center = pos_center
        self._rect = self.current_surf.get_rect(center=self.pos_center)
        self.draw_gesture_detector = draw_gesture_detector
    def update(self, dt):
        self.gesture_detector.update(dt)

        self.current_surf = self.init_surface
        if self.gesture_detector.is_pressed:
            self.current_surf = self.surface_pressed
        
        self._rect = self.current_surf.get_rect(center=self.pos_center)
        
        self.gesture_detector.rect.center = self._rect.center
        if self.text:
            self.text.rect.center = self._rect.center

    def draw(self, surface):
        surface.blit(self.current_surf, self._rect)
        if self.text:
            self.text.draw(surface)
        if self.draw_gesture_detector:
            self.gesture_detector.draw(surface)