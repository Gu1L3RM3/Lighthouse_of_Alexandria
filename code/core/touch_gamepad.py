import pygame

from core.ui.prompt_ui import get_prompt_style

# Layout is authored for the 1280x720 web canvas and scaled to the real screen.
REFERENCE_SIZE = (1280, 720)
DPAD_RADIUS = 120
DPAD_DEADZONE = 22
# A finger counts toward an axis when that axis is at least this share of the other one: gives 8 directions.
DIAGONAL_RATIO = 0.5
FACE_BUTTON_RADIUS = 40
# Gap kept between the prompt strip and the pad controls around it; the strip hugs the bottom edge
# so it stays clear of menus that reach low (the main menu's Exit button).
PROMPT_AREA_MARGIN = 12
PROMPT_AREA_BOTTOM_MARGIN = 4

# (center, size) in reference pixels; actions mirror the SDL2 controller mapping in InputManager.
# No shoulder or stick buttons: on touch, tapping the editor's tool menu directly does their job.
CONTROL_LAYOUT = {
    "dpad": ((170, 560), (DPAD_RADIUS * 2, DPAD_RADIUS * 2)),
    "a": ((1120, 630), (FACE_BUTTON_RADIUS * 2, FACE_BUTTON_RADIUS * 2)),
    "b": ((1200, 550), (FACE_BUTTON_RADIUS * 2, FACE_BUTTON_RADIUS * 2)),
    "x": ((1040, 550), (FACE_BUTTON_RADIUS * 2, FACE_BUTTON_RADIUS * 2)),
    "y": ((1120, 470), (FACE_BUTTON_RADIUS * 2, FACE_BUTTON_RADIUS * 2)),
    "back": ((570, 36), (110, 40)),
    "start": ((710, 36), (110, 40)),
}
CONTROL_ACTIONS = {
    "a": ("confirm", "interact"),
    "b": ("back",),
    "x": ("bomb",),
    "y": ("open_editor",),
    "back": ("help",),
    "start": ("pause",),
}
FACE_BUTTONS = ("a", "b", "x", "y")
MOUSE_EVENTS = (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION)

# Night-sky palette from the main menu, translucent so the level stays readable underneath.
IDLE_FILL = (15, 20, 42, 110)
PRESSED_FILL = (235, 180, 92, 200)
OUTLINE = (245, 230, 170, 150)
OUTLINE_WIDTH = 3
# Buttons wear their prompt-chip colours (A green, B red...), so "A confirm" on screen points at the green A.
BUTTON_IDLE_ALPHA = 150
BUTTON_OUTLINE_ALPHA = 210
BUTTON_PRESSED_ALPHA = 230


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


class TouchGamepad:
    """On-screen gamepad for touch screens; InputManager reads it like a physical controller."""

    def __init__(self, screen_size: tuple[int, int]):
        self.screen_size = screen_size
        scale_x = screen_size[0] / REFERENCE_SIZE[0]
        scale_y = screen_size[1] / REFERENCE_SIZE[1]
        self._size_scale = min(scale_x, scale_y)
        self.controls: dict[str, pygame.Rect] = {}
        for name, (center, size) in CONTROL_LAYOUT.items():
            rect = pygame.Rect(0, 0, round(size[0] * self._size_scale), round(size[1] * self._size_scale))
            rect.center = (round(center[0] * scale_x), round(center[1] * scale_y))
            self.controls[name] = rect
        self.active = False
        # Scenes that need the whole screen (the circuit editor) switch the pad off.
        self.enabled = True
        self._finger_controls: dict[int, str] = {}
        self._dpad_finger_pos: tuple[float, float] | None = None
        self._dpad_finger: int | None = None

    @property
    def direction(self) -> tuple[int, int]:
        if self._dpad_finger_pos is None:
            return (0, 0)
        center = self.controls["dpad"].center
        dx = self._dpad_finger_pos[0] - center[0]
        dy = self._dpad_finger_pos[1] - center[1]
        if dx * dx + dy * dy < (DPAD_DEADZONE * self._size_scale) ** 2:
            return (0, 0)
        x = _sign(dx) if abs(dx) >= DIAGONAL_RATIO * abs(dy) else 0
        y = _sign(dy) if abs(dy) >= DIAGONAL_RATIO * abs(dx) else 0
        return (x, y)

    @property
    def pressed_actions(self) -> set[str]:
        actions: set[str] = set()
        for control in self._finger_controls.values():
            actions.update(CONTROL_ACTIONS.get(control, ()))
        return actions

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Updates the pad; True means the event belongs to the pad and must not reach the game."""
        if not self.enabled:
            return False
        if event.type == pygame.KEYDOWN and not getattr(event, "synthetic_controller", False):
            self._deactivate()
            return False
        if event.type in MOUSE_EVENTS:
            # Browsers and SDL turn touches into mouse events too; drop the ones landing on a control.
            return self.active and self._control_at(event.pos) is not None
        if event.type == pygame.FINGERDOWN:
            self.active = True
            self._press(event.finger_id, self._finger_pos(event))
            return True
        if event.type == pygame.FINGERMOTION:
            if event.finger_id == self._dpad_finger:
                self._dpad_finger_pos = self._finger_pos(event)
            return True
        if event.type == pygame.FINGERUP:
            self._release(event.finger_id)
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, label_for) -> None:
        """label_for(action) returns the button caption, so it matches the on-screen prompts."""
        pressed = set(self._finger_controls.values())
        self._draw_dpad(surface)
        for name, actions in CONTROL_ACTIONS.items():
            self._draw_button(surface, font, name, label_for(actions[0]), name in pressed)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self._release_all()

    def prompt_area(self) -> pygame.Rect:
        """The bottom strip between the d-pad and the face buttons, where prompts stay readable."""
        left = self.controls["dpad"].right + PROMPT_AREA_MARGIN
        right = self.controls["x"].left - PROMPT_AREA_MARGIN
        top = self.controls["y"].top
        bottom = self.screen_size[1] - PROMPT_AREA_BOTTOM_MARGIN
        return pygame.Rect(left, top, right - left, bottom - top)

    def control_at_finger(self, event: pygame.event.Event) -> str | None:
        return self._control_at(self._finger_pos(event))

    def _press(self, finger_id: int, pos: tuple[float, float]) -> None:
        control = self._control_at(pos)
        if control is None:
            return
        self._finger_controls[finger_id] = control
        if control == "dpad":
            self._dpad_finger = finger_id
            self._dpad_finger_pos = pos

    def _release(self, finger_id: int) -> None:
        self._finger_controls.pop(finger_id, None)
        if finger_id == self._dpad_finger:
            self._dpad_finger = None
            self._dpad_finger_pos = None

    def _deactivate(self) -> None:
        self.active = False
        self._release_all()

    def _release_all(self) -> None:
        self._finger_controls.clear()
        self._dpad_finger = None
        self._dpad_finger_pos = None

    def _finger_pos(self, event: pygame.event.Event) -> tuple[float, float]:
        return (event.x * self.screen_size[0], event.y * self.screen_size[1])

    def _control_at(self, pos) -> str | None:
        for name, rect in self.controls.items():
            if rect.collidepoint(pos):
                return name
        return None

    def _draw_dpad(self, surface: pygame.Surface) -> None:
        rect = self.controls["dpad"]
        arm = rect.width // 3
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        dx, dy = self.direction
        arms = {
            (-1, 0): pygame.Rect(0, arm, arm, arm),
            (1, 0): pygame.Rect(arm * 2, arm, arm, arm),
            (0, -1): pygame.Rect(arm, 0, arm, arm),
            (0, 1): pygame.Rect(arm, arm * 2, arm, arm),
        }
        cross = [pygame.Rect(0, arm, arm * 3, arm), pygame.Rect(arm, 0, arm, arm * 3)]
        for part in cross:
            pygame.draw.rect(overlay, IDLE_FILL, part, border_radius=4)
        for (ax, ay), part in arms.items():
            if (ax and ax == dx) or (ay and ay == dy):
                pygame.draw.rect(overlay, PRESSED_FILL, part, border_radius=4)
        for part in cross:
            pygame.draw.rect(overlay, OUTLINE, part, OUTLINE_WIDTH, border_radius=4)
        surface.blit(overlay, rect.topleft)

    def _draw_button(self, surface, font, name, label, is_pressed) -> None:
        rect = self.controls[name]
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        local = overlay.get_rect()
        background, border, label_color = get_prompt_style(label)
        if is_pressed:
            fill, label_color = (*border, BUTTON_PRESSED_ALPHA), background
        else:
            fill = (*background, BUTTON_IDLE_ALPHA)
        outline = (*border, BUTTON_OUTLINE_ALPHA)
        if name in FACE_BUTTONS:
            radius = local.width // 2
            pygame.draw.circle(overlay, fill, local.center, radius)
            pygame.draw.circle(overlay, outline, local.center, radius, OUTLINE_WIDTH)
        else:
            pygame.draw.rect(overlay, fill, local, border_radius=6)
            pygame.draw.rect(overlay, outline, local, OUTLINE_WIDTH, border_radius=6)
        text = font.render(label, True, label_color)
        overlay.blit(text, text.get_rect(center=local.center))
        surface.blit(overlay, rect.topleft)
