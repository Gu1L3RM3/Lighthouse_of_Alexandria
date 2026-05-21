import pygame
from pygame import Event, Surface

from scenes.base_scene import BaseScene
from scenes.help_content import get_help_page_copy, get_help_sections
from core.settings import BLACK, HELP_SCROLL_STEP
from core.managers.scene_manager import SceneManager
from core.managers.audio_manager import AudioManager
from core.managers.input_manager import InputManager
from core.managers.language_service import LanguageService
from core.ui.prompt_ui import draw_prompt_hint_row
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType


class HelpScene(BaseScene):
    SCROLL_STEP = HELP_SCROLL_STEP

    def __init__(self, screen: Surface):
        width, height = screen.get_size()
        super().__init__(screen, width, height)
        self.scene_manager = SceneManager.get()
        self.audio_manager = AudioManager.get()
        self.input_manager = InputManager.get()
        self.language_service = LanguageService.get()
        self.language = self.language_service.get_current_language()
        self.width = width
        self.height = height

        self.title_font = self.resources.load_font("PressStart2P-Regular.ttf", 24)
        self.subtitle_font = self.resources.load_font("PressStart2P-Regular.ttf", 11)
        self.section_font = self.resources.load_font("PressStart2P-Regular.ttf", 11)
        self.text_font = self.resources.load_font("PressStart2P-Regular.ttf", 10)
        self.hint_font = self.resources.load_font("PressStart2P-Regular.ttf", 9)
        self.hint_chip_font = self.resources.load_font("PressStart2P-Regular.ttf", 8)

        self.sections = get_help_sections(self.language)
        self.help_copy = get_help_page_copy(self.language)
        self.scroll_offset = 0.0
        self.max_scroll = 0.0

        self._create_buttons()

    def _button_surfaces(self) -> tuple[Surface, Surface]:
        surf_idle = pygame.transform.scale(self.resources.load_image("buttons/wide.png"), (330, 94))
        surf_pressed = pygame.transform.scale(self.resources.load_image("buttons/wide_pressed.png"), (330, 94))
        return surf_idle, surf_pressed

    def _create_buttons(self):
        idle, pressed = self._button_surfaces()
        self.back_button = Button(
            init_surface=idle,
            surface_pressed=pressed,
            pos_center=(self.width // 2, int(self.height * 0.91)),
            click_type=ClickType.AFTER_RELEASED,
            action=self.go_back,
            text=self.language_service.get_ui_label("help_back"),
            font_size=12,
            color_text=(245, 230, 170),
        )
        self.ui_manager.add(self.back_button)

    def start(self):
        pygame.mouse.set_visible(True)
        self.scroll_offset = 0.0

    def go_back(self):
        if self.scene_manager.can_resume_help_scene():
            self.scene_manager.resume_from_help(0.35)
            return
        self.scene_manager.start_fade("main_menu", 0.35)

    def _scroll_by(self, delta: float):
        if self.max_scroll <= 0:
            self.scroll_offset = 0.0
            return
        self.scroll_offset = max(0.0, min(self.max_scroll, self.scroll_offset + delta))

    def process_input(self, events: list[Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.audio_manager.play_ui("sfx/ui_back.wav", volume=0.9)
                    self.go_back()
                    return
                if event.key in (pygame.K_w, pygame.K_UP):
                    self._scroll_by(-self.SCROLL_STEP)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self._scroll_by(self.SCROLL_STEP)
                elif event.key == pygame.K_PAGEUP:
                    self._scroll_by(-self.height * 0.65)
                elif event.key == pygame.K_PAGEDOWN:
                    self._scroll_by(self.height * 0.65)
                elif event.key == pygame.K_HOME:
                    self.scroll_offset = 0.0
                elif event.key == pygame.K_END:
                    self.scroll_offset = self.max_scroll

            elif event.type == pygame.MOUSEWHEEL:
                self._scroll_by(-event.y * self.SCROLL_STEP)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self._scroll_by(-self.SCROLL_STEP)
                elif event.button == 5:
                    self._scroll_by(self.SCROLL_STEP)

            self.ui_manager.handle_event(event)

    def update(self, dt: float) -> None:
        self.ui_manager.update(dt)

    def _wrap_line(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = text.split(" ")
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
        return lines or [""]

    def _build_content_entries(self, max_width: int) -> tuple[list[tuple[str, pygame.font.Font | None, tuple[int, int, int] | None, int]], int]:
        entries: list[tuple[str, pygame.font.Font | None, tuple[int, int, int] | None, int]] = []
        total_height = 0

        intro = self.help_copy["intro"]
        entries.append((intro, self.subtitle_font, (212, 196, 156), 14))
        total_height += self.subtitle_font.get_linesize() + 14

        for section in self.sections:
            title = str(section.get("title", ""))
            lines = section.get("lines", [])

            entries.append((title, self.section_font, (247, 218, 151), 10))
            total_height += self.section_font.get_linesize() + 10

            if isinstance(lines, list):
                for raw_line in lines:
                    wrapped = self._wrap_line(f"- {raw_line}", self.text_font, max_width)
                    for piece in wrapped:
                        entries.append((piece, self.text_font, (232, 225, 205), 6))
                        total_height += self.text_font.get_linesize() + 6

            entries.append(("", None, None, 10))
            total_height += 10

        return entries, max(0, total_height)

    def _draw_scrollbar(self, content_rect: pygame.Rect, total_height: int):
        if self.max_scroll <= 0:
            return

        track = pygame.Rect(content_rect.right + 10, content_rect.top, 8, content_rect.height)
        pygame.draw.rect(self.screen, (52, 50, 44), track, border_radius=4)
        pygame.draw.rect(self.screen, (140, 132, 108), track, width=1, border_radius=4)

        thumb_h = max(26, int(content_rect.height * (content_rect.height / max(total_height, 1))))
        movable = max(1, track.height - thumb_h)
        ratio = self.scroll_offset / self.max_scroll
        thumb_y = track.y + int(movable * ratio)
        thumb = pygame.Rect(track.x + 1, thumb_y, track.width - 2, thumb_h)
        pygame.draw.rect(self.screen, (224, 196, 132), thumb, border_radius=4)

    def render(self) -> None:
        self.screen.fill(BLACK)

        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg.fill((10, 12, 18, 255))
        self.screen.blit(bg, (0, 0))

        panel_w = min(1180, int(self.width * 0.88))
        panel_h = min(820, int(self.height * 0.83))
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (self.width // 2, int(self.height * 0.45))

        board = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(board, (31, 28, 22, 236), board.get_rect(), border_radius=12)
        pygame.draw.rect(board, (162, 132, 84, 255), board.get_rect(), width=4, border_radius=12)
        inner = board.get_rect().inflate(-20, -20)
        pygame.draw.rect(board, (50, 44, 34, 220), inner, border_radius=8)
        pygame.draw.rect(board, (197, 166, 108, 180), inner, width=2, border_radius=8)
        self.screen.blit(board, panel.topleft)

        title = self.title_font.render(self.help_copy["title"], True, (246, 215, 144))
        subtitle = self.subtitle_font.render(self.help_copy["subtitle"], True, (216, 196, 148))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.top + 46)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.top + 82)))

        content_rect = pygame.Rect(
            panel.left + 36,
            panel.top + 116,
            panel.width - 92,
            panel.height - 190,
        )

        entries, total_height = self._build_content_entries(content_rect.width - 8)
        self.max_scroll = max(0.0, float(total_height - content_rect.height))
        self.scroll_offset = max(0.0, min(self.max_scroll, self.scroll_offset))

        y = content_rect.top - int(self.scroll_offset)
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(content_rect)
        for text, font, color, gap in entries:
            if font is None:
                y += gap
                continue
            surf = font.render(text, True, color)
            if y + surf.get_height() >= content_rect.top and y <= content_rect.bottom:
                self.screen.blit(surf, (content_rect.left, y))
            y += surf.get_height() + gap
        self.screen.set_clip(prev_clip)

        self._draw_scrollbar(content_rect, total_height)

        draw_prompt_hint_row(
            self.screen,
            self.hint_chip_font,
            self.hint_font,
            self.input_manager.get_prompt_items("help"),
            anchor=(panel.centerx, panel.bottom - 22),
            align="center",
        )

        self.ui_manager.draw(self.screen)
