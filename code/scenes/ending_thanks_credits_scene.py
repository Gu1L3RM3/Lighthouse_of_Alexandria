import pygame
from pygame import Event, Surface

from scenes.base_scene import BaseScene
from core.settings import BLACK
from core.managers.scene_manager import SceneManager
from core.managers.input_manager import InputManager


class EndingThanksCreditsScene(BaseScene):
    def __init__(self, screen: Surface):
        width, height = screen.get_size()
        super().__init__(screen, width, height)
        self.scene_manager = SceneManager.get()
        self.input_manager = InputManager.get()
        self.width = width
        self.height = height

        self.title_font = self.resources.load_font("PressStart2P-Regular.ttf", 26)
        self.subtitle_font = self.resources.load_font("PressStart2P-Regular.ttf", 13)
        self.text_font = self.resources.load_font("PressStart2P-Regular.ttf", 11)

        self.total_duration = 9.0
        self.min_skip_time = 1.0
        self.timer = 0.0
        self._resolved = False

        self.lines = [
            "AGRADECIMENTOS",
            "Obrigado por jogar Farol de Alexandria.",
            "",
            "CREDITOS",
            "Autor: Guilherme Abreu Cavazzani",
            "Orientador: Samir Martins",
            "Projeto desenvolvido no GCoM",
            "https://www.ufsj.edu.br/gcom/",
            "",
            "Assets e bibliotecas:",
            "Top Down Adventure Pack v1.0 - o_lobster",
            "2D Pixel Dungeon Asset Pack v2.0",
            "SMNA (Symbolic Modified Nodal Analysis)",
            "Fonte: PressStart2P-Regular.ttf",
            "",
            "Nao e permitido vender este jogo sem autorizacao do autor.",
        ]

    def start(self):
        self.timer = 0.0
        self._resolved = False
        pygame.mouse.set_visible(True)

    def process_input(self, events: list[Event]) -> None:
        if self.timer >= self.min_skip_time and (
            self.input_manager.is_action_just_pressed("confirm")
            or self.input_manager.is_action_just_pressed("back")
        ):
            self._go_menu()
            return

        for event in events:
            if (
                event.type == pygame.KEYDOWN
                and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE)
                and self.timer >= self.min_skip_time
            ):
                self._go_menu()

    def update(self, dt: float) -> None:
        self.timer += dt
        if self.timer >= self.total_duration:
            self._go_menu()

    def _go_menu(self):
        if self._resolved:
            return
        self._resolved = True
        self.scene_manager.start_fade("main_menu", 0.8)

    def render(self) -> None:
        self.screen.fill(BLACK)

        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg.fill((8, 12, 20, 255))
        self.screen.blit(bg, (0, 0))

        panel_w = min(1120, int(self.width * 0.84))
        panel_h = min(760, int(self.height * 0.82))
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (self.width // 2, self.height // 2)

        board = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(board, (28, 24, 18, 235), board.get_rect(), border_radius=12)
        pygame.draw.rect(board, (161, 129, 79, 255), board.get_rect(), width=4, border_radius=12)
        inner = board.get_rect().inflate(-20, -20)
        pygame.draw.rect(board, (47, 41, 31, 220), inner, border_radius=8)
        pygame.draw.rect(board, (195, 162, 100, 180), inner, width=2, border_radius=8)
        self.screen.blit(board, panel.topleft)

        title = self.title_font.render("FAROL DE ALEXANDRIA", True, (246, 215, 144))
        subtitle = self.subtitle_font.render("Agradecimentos e creditos finais", True, (214, 192, 142))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.top + 54)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.top + 90)))

        y = panel.top + 130
        line_spacing = 24
        for raw_line in self.lines:
            if not raw_line:
                y += line_spacing // 2
                continue
            color = (236, 222, 188) if "http" not in raw_line else (147, 194, 255)
            line = self.text_font.render(raw_line, True, color)
            self.screen.blit(line, (panel.left + 36, y))
            y += line_spacing

        confirm_label = self.input_manager.get_prompt_button("confirm")
        back_label = self.input_manager.get_prompt_button("back")
        hint = self.subtitle_font.render(f"{confirm_label}/{back_label} para pular", True, (168, 154, 126))
        self.screen.blit(hint, hint.get_rect(center=(self.width // 2, int(self.height * 0.93))))
