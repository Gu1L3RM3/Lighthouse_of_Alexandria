from pygame import Rect


class BoardView:
    """Fits the circuit board (world pixels, fixed cell size) into the free area of the screen.

    Circuits were authored on large screens; on 1280x720 the board is drawn smaller so no column
    hides under the sidebar. The scale gives whole-pixel cells, so the pixel art stays crisp,
    and never enlarges the board.
    """

    def __init__(self, origin: tuple[int, int], cell_size: int, cols: int, min_rows: int, free_area: Rect):
        self.origin = origin
        self.cell_size = cell_size
        self.cols = cols
        self.cell_on_screen = min(cell_size, free_area.width // cols, free_area.height // min_rows)
        self.scale = self.cell_on_screen / cell_size
        self.rows = max(min_rows, free_area.height // self.cell_on_screen)
        self.screen_rect = Rect(
            free_area.left,
            free_area.top,
            self.cols * self.cell_on_screen,
            self.rows * self.cell_on_screen,
        )

    @property
    def camera_offset(self) -> tuple[float, float]:
        """Shift that RenderSystem's camera applies after scaling world rects by `scale`."""
        return (
            self.screen_rect.left - self.origin[0] * self.scale,
            self.screen_rect.top - self.origin[1] * self.scale,
        )

    def to_world(self, screen_pos) -> tuple[float, float]:
        return (
            (screen_pos[0] - self.screen_rect.left) / self.scale + self.origin[0],
            (screen_pos[1] - self.screen_rect.top) / self.scale + self.origin[1],
        )

    def to_screen(self, world_pos) -> tuple[int, int]:
        return (
            round((world_pos[0] - self.origin[0]) * self.scale + self.screen_rect.left),
            round((world_pos[1] - self.origin[1]) * self.scale + self.screen_rect.top),
        )

    def to_screen_rect(self, world_rect: Rect) -> Rect:
        left, top = self.to_screen(world_rect.topleft)
        return Rect(left, top, round(world_rect.width * self.scale), round(world_rect.height * self.scale))

    def world_cells(self) -> list[Rect]:
        return [
            Rect(self.origin[0] + col * self.cell_size, self.origin[1] + row * self.cell_size, self.cell_size, self.cell_size)
            for col in range(self.cols)
            for row in range(self.rows)
        ]
