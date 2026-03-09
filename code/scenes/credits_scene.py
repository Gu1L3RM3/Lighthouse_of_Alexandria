import pygame
from pygame import Event, Surface

from scenes.base_scene import BaseScene
from core.settings import BLACK
from core.managers.scene_manager import SceneManager
from core.ui.widgets.button import Button
from core.ui.widgets.gesture_detector import ClickType


class CreditsScene(BaseScene):
    def __init__(self, screen: Surface):
        width, height = screen.get_size()
        super().__init__(screen, width, height)
        self.scene_manager = SceneManager.get()
        self.width = width
        self.height = height

        self.title_font = self.resources.load_font("PressStart2P-Regular.ttf", 28)
        self.subtitle_font = self.resources.load_font("PressStart2P-Regular.ttf", 14)
        self.text_font = self.resources.load_font("PressStart2P-Regular.ttf", 12)

        self._create_buttons()

        self.credit_lines = [
            "Projeto",
            "Farol de Alexandria",
            "",
            "Autor",
            "Guilherme Abreu Cavazzani",
            "",
            "Orientador",
            "Samir Martins",
            "",
            "Instituicao e grupo",
            "Projeto desenvolvido no GCoM",
            "https://www.ufsj.edu.br/gcom/",
            "",
            "Creditos de assets e bibliotecas",
            "Top Down Adventure Pack v1.0 - o_lobster",
            "https://o-lobster.itch.io/adventure-pack",
            "2D Pixel Dungeon Asset Pack v2.0",
            "Usado em tiles e elementos visuais do jogo",
            "SMNA (Symbolic Modified Nodal Analysis)",
            "https://github.com/Tiburonboy/Symbolic-modified-nodal-analysis",
            "Fonte: PressStart2P-Regular.ttf",
            "Licenca conforme distribuicao original da fonte",
        ]

    def _button_surfaces(self) -> tuple[Surface, Surface]:
        surf_idle = pygame.transform.scale(self.resources.load_image("buttons/wide.png"), (330, 94))
        surf_pressed = pygame.transform.scale(self.resources.load_image("buttons/wide_pressed.png"), (330, 94))
        return surf_idle, surf_pressed

    def _create_buttons(self):
        idle, pressed = self._button_surfaces()
        self.back_button = Button(
            init_surface=idle,
            surface_pressed=pressed,
            pos_center=(self.width // 2, int(self.height * 0.88)),
            click_type=ClickType.AFTER_RELEASED,
            action=self.go_back,
            text="VOLTAR AO MENU",
            font_size=12,
            color_text=(245, 230, 170),
        )
        self.ui_manager.add(self.back_button)

    def go_back(self):
        self.scene_manager.start_fade("main_menu", 0.45)

    def start(self):
        pygame.mouse.set_visible(True)

    def process_input(self, events: list[Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.go_back()
                return
            self.ui_manager.handle_event(event)

    def update(self, dt: float) -> None:
        self.ui_manager.update(dt)

    def render(self) -> None:
        self.screen.fill(BLACK)

        # Fundo simples para manter contraste de leitura.
        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg.fill((8, 12, 20, 255))
        self.screen.blit(bg, (0, 0))

        panel_w = min(1080, int(self.width * 0.82))
        panel_h = min(760, int(self.height * 0.78))
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (self.width // 2, int(self.height * 0.44))

        board = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(board, (28, 24, 18, 235), board.get_rect(), border_radius=12)
        pygame.draw.rect(board, (161, 129, 79, 255), board.get_rect(), width=4, border_radius=12)
        inner = board.get_rect().inflate(-20, -20)
        pygame.draw.rect(board, (47, 41, 31, 220), inner, border_radius=8)
        pygame.draw.rect(board, (195, 162, 100, 180), inner, width=2, border_radius=8)
        self.screen.blit(board, panel.topleft)

        title = self.title_font.render("CREDITOS", True, (246, 215, 144))
        subtitle = self.subtitle_font.render("Referencias e atribuicoes do projeto", True, (214, 192, 142))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.top + 52)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.top + 92)))

        y = panel.top + 132
        line_spacing = 26
        for raw_line in self.credit_lines:
            if not raw_line:
                y += line_spacing // 2
                continue
            color = (236, 222, 188) if "http" not in raw_line else (147, 194, 255)
            line = self.text_font.render(raw_line, True, color)
            self.screen.blit(line, (panel.left + 36, y))
            y += line_spacing

        self.ui_manager.draw(self.screen)
