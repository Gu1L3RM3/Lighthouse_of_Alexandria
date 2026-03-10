import pygame
from pygame import Event, Surface

from scenes.base_scene import BaseScene
from core.settings import BLACK
from core.managers.scene_manager import SceneManager
from core.managers.life_manager import LifeManager
from core.managers.audio_manager import AudioManager
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType


class MainMenuScene(BaseScene):
    def __init__(self, screen: Surface):
        width, height = screen.get_size()
        super().__init__(screen, width, height)
        self.scene_manager = SceneManager.get()
        self.life_manager = LifeManager.get()
        self.audio_manager = AudioManager.get()
        self.width = width
        self.height = height
        self.low_res_size = (320, 180)

        self.component_icons = {
            "v": pygame.transform.scale(self.resources.load_image("eletric_components/voltage_source.png"), (22, 11)),
            "r": pygame.transform.scale(self.resources.load_image("eletric_components/resistor.png"), (22, 11)),
            "i": pygame.transform.scale(self.resources.load_image("eletric_components/current_source.png"), (22, 11)),
            "g": pygame.transform.scale(self.resources.load_image("eletric_components/gnd.png"), (12, 12)),
        }

        self.backgrounds = self._build_backgrounds()
        self.bg_index = 0
        self.bg_time = 0.0
        self.bg_duration = 7.5
        self.bg_fade = 1.0
        self.next_bg_index = 1 if len(self.backgrounds) > 1 else 0

        self.torch_frames = [
            pygame.transform.scale(self.resources.load_image(f"torch/torch_{i}.png"), (80, 80))
            for i in range(1, 5)
        ]
        self.torch_index = 0
        self.torch_timer = 0.0
        self.torch_interval = 0.14

        self.title_font = self.resources.load_font("PressStart2P-Regular.ttf", 34)
        self.subtitle_font = self.resources.load_font("PressStart2P-Regular.ttf", 14)

        self._create_buttons()

    def _upscale_pixel(self, low_surface: Surface) -> Surface:
        return pygame.transform.scale(low_surface, (self.width, self.height))

    def _build_backgrounds(self) -> list[Surface]:
        base = self._build_harbor_background()
        night = self._tint_surface(base, (12, 18, 34), 46)
        dawn = self._tint_surface(base, (120, 78, 34), 54)
        storm = self._tint_surface(base, (20, 42, 62), 62)
        return [night, dawn, storm]

    def _tint_surface(self, surface: Surface, color: tuple[int, int, int], alpha: int) -> Surface:
        tinted = surface.copy()
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((*color, alpha))
        tinted.blit(overlay, (0, 0))
        return tinted

    def _build_harbor_background(self) -> Surface:
        w, h = self.low_res_size
        bg = pygame.Surface((w, h))

        # Ceu noturno em camadas (pixel art)
        sky_bands = [
            (15, 20, 42),
            (23, 31, 58),
            (33, 43, 74),
            (42, 56, 90),
        ]
        band_h = h // 4
        for idx, color in enumerate(sky_bands):
            pygame.draw.rect(bg, color, (0, idx * band_h, w, band_h))

        # Mar do porto e horizonte
        pygame.draw.rect(bg, (24, 49, 81), (0, int(h * 0.62), w, int(h * 0.38)))
        for y in range(int(h * 0.62), h, 6):
            tone = 85 + (y % 18)
            pygame.draw.line(bg, (tone // 2, tone, tone + 35), (0, y), (w, y), 1)

        # Silhuetas de cidade/colinas
        pygame.draw.polygon(bg, (20, 24, 40), [(0, 118), (26, 95), (56, 108), (82, 90), (108, 112), (138, 98), (162, 120), (0, 120)])
        pygame.draw.polygon(bg, (20, 24, 40), [(200, 120), (225, 97), (246, 104), (268, 87), (300, 103), (320, 90), (320, 120)])

        # Farol estilizado de Alexandria
        pygame.draw.rect(bg, (176, 166, 136), (140, 50, 42, 74))
        pygame.draw.rect(bg, (145, 133, 104), (134, 124, 54, 10))
        pygame.draw.rect(bg, (205, 194, 156), (146, 38, 30, 14))
        pygame.draw.rect(bg, (235, 180, 92), (154, 26, 14, 12))
        pygame.draw.rect(bg, (255, 224, 138), (151, 20, 20, 7))

        # Brilho da chama
        glow = pygame.Surface((44, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 220, 120, 88), glow.get_rect())
        bg.blit(glow, (140, 12))

        # Estrelas
        for x, y in [(34, 20), (52, 34), (90, 26), (214, 24), (244, 42), (276, 18)]:
            bg.set_at((x, y), (245, 236, 198))
            bg.set_at((x + 1, y), (190, 182, 154))

        return self._upscale_pixel(bg)

    def _button_surfaces(self) -> tuple[Surface, Surface]:
        surf_idle = pygame.transform.scale(self.resources.load_image("buttons/wide.png"), (310, 94))
        surf_pressed = pygame.transform.scale(self.resources.load_image("buttons/wide_pressed.png"), (310, 94))
        return surf_idle, surf_pressed

    def _create_buttons(self):
        idle, pressed = self._button_surfaces()
        center_x = self.width // 2
        first_y = int(self.height * 0.47)
        gap = 96

        self.resume_button = Button(
            init_surface=idle.copy(),
            surface_pressed=pressed.copy(),
            pos_center=(center_x, first_y),
            click_type=ClickType.AFTER_RELEASED,
            action=self.resume_current_scene,
            text="RETOMAR FASE",
            font_size=12,
            color_text=(245, 230, 170),
        )

        self.start_button = Button(
            init_surface=idle.copy(),
            surface_pressed=pressed.copy(),
            pos_center=(center_x, first_y + gap),
            click_type=ClickType.AFTER_RELEASED,
            action=self.start_new_game,
            text="INICIAR JORNADA",
            font_size=12,
            color_text=(245, 230, 170),
        )
        self.credits_button = Button(
            init_surface=idle.copy(),
            surface_pressed=pressed.copy(),
            pos_center=(center_x, first_y + gap * 2),
            click_type=ClickType.AFTER_RELEASED,
            action=self.open_credits,
            text="CREDITOS",
            font_size=12,
            color_text=(245, 230, 170),
        )
        self.exit_button = Button(
            init_surface=idle.copy(),
            surface_pressed=pressed.copy(),
            pos_center=(center_x, first_y + gap * 3),
            click_type=ClickType.AFTER_RELEASED,
            action=self.exit_game,
            text="SAIR",
            font_size=12,
            color_text=(245, 230, 170),
        )
        self.ui_manager.add(self.resume_button, self.start_button, self.credits_button, self.exit_button)

    def _refresh_resume_button(self):
        can_resume = self.scene_manager.can_resume_scene()
        if can_resume:
            self.resume_button.change_text("RETOMAR FASE")
            self.resume_button.text_widget.font_color = (245, 230, 170)
        else:
            self.resume_button.change_text("SEM FASE ATIVA")
            self.resume_button.text_widget.font_color = (166, 154, 126)

    def resume_current_scene(self):
        if not self.scene_manager.can_resume_scene():
            return
        self.scene_manager.resume_from_menu(0.45)

    def start_new_game(self):
        self.life_manager.reset_lives()
        self.scene_manager.start_fade("home_scene", 0.6)

    def open_credits(self):
        self.scene_manager.start_fade("credits", 0.45)

    def exit_game(self):
        self.audio_manager.play_ui("sfx/ui_back.wav", volume=0.9)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def start(self):
        pygame.mouse.set_visible(True)
        self._refresh_resume_button()

    def process_input(self, events: list[Event]):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.audio_manager.play_ui("sfx/ui_click.wav", volume=0.9)
                    self.start_new_game()
                elif event.key == pygame.K_ESCAPE:
                    self.audio_manager.play_ui("sfx/ui_back.wav", volume=0.9)
                    self.resume_current_scene()
            self.ui_manager.handle_event(event)

    def update(self, dt: float):
        self.bg_time += dt
        cycle = self.bg_duration + self.bg_fade
        if self.bg_time >= cycle:
            self.bg_time = 0.0
            self.bg_index = self.next_bg_index
            self.next_bg_index = (self.bg_index + 1) % len(self.backgrounds)

        self.torch_timer += dt
        if self.torch_timer >= self.torch_interval:
            self.torch_timer = 0.0
            self.torch_index = (self.torch_index + 1) % len(self.torch_frames)

        self.ui_manager.update(dt)

    def _draw_background(self):
        if not self.backgrounds:
            self.screen.fill(BLACK)
            return

        self.screen.blit(self.backgrounds[self.bg_index], (0, 0))
        if self.bg_time >= self.bg_duration:
            fade_t = min(1.0, (self.bg_time - self.bg_duration) / self.bg_fade)
            overlay = self.backgrounds[self.next_bg_index].copy()
            overlay.set_alpha(int(255 * fade_t))
            self.screen.blit(overlay, (0, 0))

        dark = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dark.fill((7, 8, 13, 130))
        self.screen.blit(dark, (0, 0))

    def _draw_torches(self):
        frame = self.torch_frames[self.torch_index]
        margin = 28
        y = 26
        self.screen.blit(frame, (margin, y))
        self.screen.blit(frame, (self.width - frame.get_width() - margin, y))

    def _draw_title_and_panel(self):
        panel_w = min(780, int(self.width * 0.66))
        panel_h = min(640, int(self.height * 0.84))
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (self.width // 2, self.height // 2 + 28)

        # Painel de pedra/bronze
        panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel.fill((0, 0, 0, 0))
        pygame.draw.rect(panel, (38, 35, 30, 230), panel.get_rect(), border_radius=10)
        pygame.draw.rect(panel, (130, 106, 64, 255), panel.get_rect(), width=4, border_radius=10)
        inner = panel.get_rect().inflate(-18, -18)
        pygame.draw.rect(panel, (58, 52, 44, 210), inner, border_radius=8)
        pygame.draw.rect(panel, (162, 138, 90, 200), inner, width=2, border_radius=8)
        self.screen.blit(panel, panel_rect)

        title_top = panel_rect.top + 52
        title1 = self.title_font.render("FAROL DE", True, (240, 208, 132))
        title2 = self.title_font.render("ALEXANDRIA", True, (247, 218, 151))
        subtitle = self.subtitle_font.render("Historia, enigmas e eletricidade", True, (204, 180, 126))
        line = self.subtitle_font.render("pixel adventure", True, (167, 145, 102))

        self.screen.blit(title1, title1.get_rect(center=(self.width // 2, title_top)))
        self.screen.blit(title2, title2.get_rect(center=(self.width // 2, title_top + 52)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, title_top + 98)))
        self.screen.blit(line, line.get_rect(center=(self.width // 2, title_top + 126)))

        # Ornamentos eletricos discretos
        icon_y = panel_rect.bottom - 58
        self.screen.blit(self.component_icons["v"], (panel_rect.left + 56, icon_y))
        self.screen.blit(self.component_icons["r"], (panel_rect.left + 110, icon_y))
        self.screen.blit(self.component_icons["g"], (panel_rect.right - 68, icon_y - 2))

    def render(self):
        self._draw_background()
        self._draw_torches()
        self._draw_title_and_panel()
        self.ui_manager.draw(self.screen)
