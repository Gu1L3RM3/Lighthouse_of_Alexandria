import pygame

from core.managers.resource_manager import ResourceManager
from core.components.dialogue import Dialogue
from core.ui.widgets.widget import Widget


class DialogueImageSequenceWidget(Widget):
    def __init__(
        self,
        dialogue_component: Dialogue,
        image_paths: list[str],
        captions: list[str] | None = None,
        max_size: tuple[int, int] | None = None,
        top_margin: int = 24,
    ):
        super().__init__()
        self.dialogue = dialogue_component
        self.top_margin = top_margin
        self.images: list[pygame.Surface] = []
        self.captions = list(captions or [])
        self.rm = ResourceManager.get()
        self.badge_font = self.rm.load_font("PressStart2P-Regular.ttf", 10)
        self.caption_font = self.rm.load_font("PressStart2P-Regular.ttf", 10)

        if max_size is None:
            display = pygame.display.get_surface()
            if display:
                width, height = display.get_size()
                max_w = min(760, max(420, int(width * 0.56)))
                max_h = min(360, max(220, int(height * 0.34)))
                self.max_size = (max_w, max_h)
            else:
                self.max_size = (620, 320)
        else:
            self.max_size = max_size

        self._load_images(image_paths)
        self._normalize_caption_count()
        self._wrapped_captions = [
            self._wrap_text(caption, self.caption_font, max(60, self.max_size[0] - 24))
            for caption in self.captions
        ]

    def _load_images(self, image_paths: list[str]):
        for rel_path in image_paths:
            self.images.append(self._load_one_image(rel_path))

    def _normalize_caption_count(self):
        if len(self.captions) < len(self.images):
            self.captions.extend([""] * (len(self.images) - len(self.captions)))
        elif len(self.captions) > len(self.images):
            self.captions = self.captions[: len(self.images)]

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        raw = str(text or "").strip()
        if not raw:
            return []

        words = raw.split(" ")
        lines: list[str] = []
        current = ""
        for word in words:
            if not word:
                continue
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
                continue

            if current:
                lines.append(current)
                current = ""

            if font.size(word)[0] <= max_width:
                current = word
                continue

            chunk = ""
            for ch in word:
                test_chunk = chunk + ch
                if font.size(test_chunk)[0] <= max_width:
                    chunk = test_chunk
                else:
                    if chunk:
                        lines.append(chunk)
                    chunk = ch
            current = chunk

        if current:
            lines.append(current)
        return lines

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
        short_path = rel_path if len(rel_path) <= 54 else f"...{rel_path[-51:]}"
        text = font.render(f"Imagem nao encontrada: {short_path}", True, (240, 90, 90))
        text_rect = text.get_rect(center=(self.max_size[0] // 2, self.max_size[1] // 2))
        surf.blit(text, text_rect)
        return surf

    def update(self, dt):
        _ = dt

    def _draw_slide_badge(self, surface: pygame.Surface, frame_rect: pygame.Rect, index: int):
        badge_text = f"{index + 1}/{len(self.images)}"
        badge = self.badge_font.render(badge_text, True, (214, 198, 156))
        badge_rect = badge.get_rect(topright=(frame_rect.right - 12, frame_rect.top + 10))
        bg_rect = badge_rect.inflate(12, 8)
        pygame.draw.rect(surface, (26, 32, 48, 220), bg_rect, border_radius=6)
        pygame.draw.rect(surface, (160, 188, 232, 220), bg_rect, 1, border_radius=6)
        surface.blit(badge, badge_rect)

    def _draw_caption(self, surface: pygame.Surface, frame_rect: pygame.Rect, index: int):
        if index >= len(self._wrapped_captions):
            return

        lines = self._wrapped_captions[index]
        if not lines:
            return

        line_h = self.caption_font.get_linesize()
        padding = 8
        available_h = surface.get_height() - (frame_rect.bottom + 16) - 8
        max_lines = (available_h - (padding * 2)) // max(1, line_h)
        if max_lines <= 0:
            return

        lines = lines[:max_lines]
        caption_h = (line_h * len(lines)) + (padding * 2)
        caption_rect = pygame.Rect(frame_rect.left, frame_rect.bottom + 10, frame_rect.width, caption_h)
        pygame.draw.rect(surface, (10, 16, 30, 228), caption_rect, border_radius=8)
        pygame.draw.rect(surface, (130, 172, 236, 220), caption_rect, 1, border_radius=8)

        y = caption_rect.top + padding
        for line in lines:
            txt = self.caption_font.render(line, True, (225, 220, 202))
            surface.blit(txt, (caption_rect.left + 10, y))
            y += line_h

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
        self._draw_slide_badge(surface, frame_rect, index)
        self._draw_caption(surface, frame_rect, index)
