import pygame
from pygame import Event, Surface

from scenes.base_scene import BaseScene
from core.localization.scene_copy_catalog import SceneCopyCatalog
from core.managers.scene_manager import SceneManager
from core.managers.audio_manager import AudioManager
from core.managers.language_service import LanguageService


class LighthouseRekindleScene(BaseScene):
    def __init__(self, screen: Surface):
        width, height = screen.get_size()
        super().__init__(screen, width, height)
        self.scene_manager = SceneManager.get()
        self.copy = SceneCopyCatalog(LanguageService.get().get_current_language())
        self.width = width
        self.height = height
        self.low_res_size = (320, 180)

        self.title_font = self.resources.load_font("PressStart2P-Regular.ttf", 20)
        self.small_font = self.resources.load_font("PressStart2P-Regular.ttf", 12)

        self.timer = 0.0
        self.hold_before_light = 1.2
        self.light_rise_duration = 2.8
        self.total_duration = 6.4
        self._resolved = False
        self.min_skip_time = 1.0
        self._ignite_sfx_played = False

        self.background = self._build_background()

    def start(self):
        self.timer = 0.0
        self._resolved = False
        self._ignite_sfx_played = False
        pygame.mouse.set_visible(False)

    def process_input(self, events: list[Event]) -> None:
        for event in events:
            if (
                event.type == pygame.KEYDOWN
                and event.key in (pygame.K_RETURN, pygame.K_SPACE)
                and self.timer >= self.min_skip_time
            ):
                self._go_next()

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.total_duration:
            self._go_next()

    def render(self) -> None:
        self.screen.blit(self.background, (0, 0))
        self._draw_lighthouse_light()
        self._draw_texts()

    def _go_next(self):
        if self._resolved:
            return
        self._resolved = True
        self.scene_manager.start_fade("home_after", 0.85)

    def _upscale_pixel(self, low_surface: Surface) -> Surface:
        return pygame.transform.scale(low_surface, (self.width, self.height))

    def _build_background(self) -> Surface:
        w, h = self.low_res_size
        bg = pygame.Surface((w, h))

        sky_bands = [
            (14, 18, 34),
            (20, 28, 50),
            (28, 38, 66),
            (36, 48, 78),
        ]
        band_h = h // 4
        for idx, color in enumerate(sky_bands):
            pygame.draw.rect(bg, color, (0, idx * band_h, w, band_h))

        pygame.draw.rect(bg, (22, 44, 72), (0, int(h * 0.62), w, int(h * 0.38)))
        for y in range(int(h * 0.62), h, 6):
            tone = 80 + (y % 16)
            pygame.draw.line(bg, (tone // 2, tone, tone + 28), (0, y), (w, y), 1)

        pygame.draw.polygon(bg, (18, 22, 36), [(0, 120), (30, 96), (62, 110), (88, 92), (124, 116), (0, 120)])
        pygame.draw.polygon(bg, (18, 22, 36), [(194, 120), (226, 99), (252, 106), (286, 90), (320, 110), (320, 120)])

        # Farol.
        pygame.draw.rect(bg, (170, 162, 134), (140, 50, 42, 74))
        pygame.draw.rect(bg, (142, 128, 100), (134, 124, 54, 10))
        pygame.draw.rect(bg, (198, 190, 152), (146, 38, 30, 14))
        # Lanterna inicia "apagada" para destacar o acendimento na animacao.
        pygame.draw.rect(bg, (96, 86, 70), (154, 26, 14, 12))
        pygame.draw.rect(bg, (112, 100, 80), (151, 20, 20, 7))

        for x, y in [(36, 21), (52, 34), (90, 26), (214, 24), (244, 42), (276, 18)]:
            bg.set_at((x, y), (240, 232, 198))

        return self._upscale_pixel(bg)

    def _draw_lighthouse_light(self):
        t = self.timer - self.hold_before_light
        if t <= 0:
            return
        if not self._ignite_sfx_played:
            AudioManager.get().play_sfx("sfx/lighthouse_ignite.wav", volume=0.95)
            self._ignite_sfx_played = True
        progress = min(1.0, t / self.light_rise_duration)
        eased = progress * progress * (3.0 - 2.0 * progress)

        # Ancora da lanterna em coordenada do fundo low-res.
        # Mantem alinhamento correto com o farol em qualquer resolucao.
        low_w, low_h = self.low_res_size
        light_x = int(self.width * (161 / low_w))
        light_y = int(self.height * (27 / low_h))

        # Feixe em cone: inicia para cima e termina para baixo.
        cone_half_w = int(4 + (self.width * 0.18) * eased)
        cone_alpha = int(20 + 170 * eased)
        sweep_start_y = light_y - int(self.height * 0.28)
        sweep_end_y = light_y + int(self.height * 0.34)
        beam_y = int(sweep_start_y + (sweep_end_y - sweep_start_y) * eased)

        cone = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.polygon(
            cone,
            (255, 228, 138, cone_alpha),
            [
                (light_x, light_y),
                (light_x - cone_half_w, beam_y),
                (light_x + cone_half_w, beam_y),
            ],
        )
        self.screen.blit(cone, (0, 0))

        # Nucleo da lampada acende do zero sem glow circular gigante.
        core_r = int(2 + 8 * eased)
        ring_r = int(4 + 12 * eased)
        core = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(core, (255, 242, 186, int(40 + 210 * eased)), (32, 32), core_r)
        pygame.draw.circle(core, (255, 214, 112, int(25 + 165 * eased)), (32, 32), ring_r, 2)
        self.screen.blit(core, core.get_rect(center=(light_x, light_y + 2)))

    def _draw_texts(self):
        title = self.title_font.render(self.copy.get("lighthouse_title"), True, (247, 219, 146))
        subtitle = self.small_font.render(self.copy.get("lighthouse_subtitle"), True, (216, 195, 152))
        hint_text = self.copy.get("lighthouse_skip_hint").format(confirm="ENTER")
        hint = self.small_font.render(hint_text, True, (160, 150, 122))

        self.screen.blit(title, title.get_rect(center=(self.width // 2, int(self.height * 0.84))))
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, int(self.height * 0.89))))
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, int(self.height * 0.94))))
