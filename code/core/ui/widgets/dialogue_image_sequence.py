import pygame

from core.managers.resource_manager import ResourceManager
from core.components.dialogue import Dialogue
from core.ui.widgets.widget import Widget


class DialogueImageSequenceWidget(Widget):
    def __init__(
        self,
        dialogue_component: Dialogue,
        image_paths: list[str],
        max_size: tuple[int, int] = (620, 320),
        top_margin: int = 24,
    ):
        super().__init__()
        self.dialogue = dialogue_component
        self.max_size = max_size
        self.top_margin = top_margin
        self.images: list[pygame.Surface] = []
        self.rm = ResourceManager.get()

        self._load_images(image_paths)

    def _load_images(self, image_paths: list[str]):
        for rel_path in image_paths:
            self.images.append(self._load_one_image(rel_path))

    def _load_one_image(self, rel_path: str) -> pygame.Surface:
        try:
            surface = self.rm.load_image(rel_path)
        except Exception:
            return self._placeholder_surface(rel_path)
        return self._fit_surface(surface)

    def _fit_surface(self, surface: pygame.Surface) -> pygame.Surface:
        w, h = surface.get_size()
        max_w, max_h = self.max_size

        if w <= max_w and h <= max_h:
            return surface

        scale = min(max_w / max(1, w), max_h / max(1, h))
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        return pygame.transform.smoothscale(surface, new_size)

    def _placeholder_surface(self, rel_path: str) -> pygame.Surface:
        surf = pygame.Surface(self.max_size)
        surf.fill((22, 22, 32))
        border = surf.get_rect()
        pygame.draw.rect(surf, (220, 220, 220), border, 2)

        font = pygame.font.SysFont(None, 22)
        text = font.render(f"Imagem nao encontrada: {rel_path}", True, (240, 90, 90))
        text_rect = text.get_rect(center=(self.max_size[0] // 2, self.max_size[1] // 2))
        surf.blit(text, text_rect)
        return surf

    def update(self, dt):
        _ = dt

    def draw(self, surface: pygame.Surface):
        if not self.dialogue.active or not self.images:
            return

        index = min(self.dialogue.current_index, len(self.images) - 1)
        image = self.images[index]
        image_rect = image.get_rect(center=(surface.get_width() // 2, self.top_margin + image.get_height() // 2))

        frame_rect = image_rect.inflate(16, 16)
        pygame.draw.rect(surface, (10, 16, 30), frame_rect, border_radius=8)
        pygame.draw.rect(surface, (180, 210, 255), frame_rect, 2, border_radius=8)
        surface.blit(image, image_rect)
