import pygame

from core.settings import WEB_RESOLUTION

# Browsers fire an emulated mouse click shortly after a tap; buttons ignore the mouse for this long.
EMULATED_MOUSE_WINDOW_MS = 600


class TouchPoints:
    """Fingers currently on the screen, in screen pixels, for widgets that poll input each frame.

    A tap that starts and ends inside one frame stays pressed until the next frame,
    so polling widgets never miss it.
    """

    _instance = None

    def __init__(self, screen_size: tuple[int, int] = WEB_RESOLUTION, clock=pygame.time.get_ticks):
        self.screen_size = screen_size
        self._clock = clock
        self._fingers: dict[int, tuple[int, int]] = {}
        self._down_this_frame: set[int] = set()
        self._lift_next_frame: set[int] = set()
        self._released: list[tuple[int, int]] = []
        self._last_touch_ms: int | None = None
        self._last_position: tuple[int, int] | None = None
        # Counts frames so widgets can tell "shown last frame" from "just shown".
        self.frame = 0

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = TouchPoints()
        return cls._instance

    def begin_frame(self) -> None:
        self.frame += 1
        self._released = [self._fingers.pop(finger_id) for finger_id in self._lift_next_frame if finger_id in self._fingers]
        self._lift_next_frame.clear()
        self._down_this_frame.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type not in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            return
        self._last_touch_ms = self._clock()
        pos = (round(event.x * self.screen_size[0]), round(event.y * self.screen_size[1]))
        if event.type == pygame.FINGERDOWN:
            self._fingers[event.finger_id] = pos
            self._down_this_frame.add(event.finger_id)
            self._last_position = pos
            return
        if event.finger_id not in self._fingers:
            return
        self._last_position = pos
        if event.type == pygame.FINGERMOTION:
            self._fingers[event.finger_id] = pos
        elif event.finger_id in self._down_this_frame:
            self._fingers[event.finger_id] = pos
            self._lift_next_frame.add(event.finger_id)
        else:
            self._released.append(pos)
            del self._fingers[event.finger_id]

    def pressed_positions(self) -> list[tuple[int, int]]:
        return list(self._fingers.values())

    def started_positions(self) -> list[tuple[int, int]]:
        """Where fingers touched down this frame."""
        return [self._fingers[finger_id] for finger_id in self._down_this_frame if finger_id in self._fingers]

    def released_positions(self) -> list[tuple[int, int]]:
        """Where fingers were lifted this frame: a button released under one counts as clicked."""
        return list(self._released)

    def last_position(self) -> tuple[int, int] | None:
        """Where the most recent finger is or was lifted: the pointer of a touch screen."""
        return self._last_position

    def touched_recently(self) -> bool:
        return self._last_touch_ms is not None and self._clock() - self._last_touch_ms < EMULATED_MOUSE_WINDOW_MS
