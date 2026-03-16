import pygame

from core.managers.resource_manager import ResourceManager
from core.settings import FONT
from core.ui.widgets.widget import Widget
from utils.setter_values import SetterValues


class BombStatusWidget(Widget):
    def __init__(self, bomb_manager, pos: tuple[int, int] = (10, 86)):
        super().__init__()
        self.bomb_manager = bomb_manager
        self.pos = pos
        self.rm = ResourceManager.get()
        self.font_title = self.rm.load_font(FONT, 10)
        self.font_info = self.rm.load_font(FONT, 8)
        self.icon = self._try_load_icon()

    def _try_load_icon(self):
        try:
            icon = self.rm.load_image("circuit_components/eletron.png")
            return pygame.transform.scale(icon, (18, 18))
        except Exception:
            return None

    def update(self, dt):
        _ = dt

    def draw(self, surface: pygame.Surface):
        x, y = self.pos
        panel_w = 272
        panel_h = 68
        panel = pygame.Rect(x, y, panel_w, panel_h)
        pygame.draw.rect(surface, (20, 22, 29), panel, border_radius=8)
        pygame.draw.rect(surface, (235, 221, 160), panel, width=2, border_radius=8)

        params = self.bomb_manager.current_params
        bombs = self.bomb_manager.remaining_bombs
        fallback = "PADRAO" if params.used_fallback else "R1"
        title = self.font_title.render(f"NUCLEOS x{bombs} ({fallback})", True, (245, 230, 170))
        title_x = x + 8
        if self.icon is not None:
            surface.blit(self.icon, (x + 8, y + 6))
            title_x += 24
        surface.blit(title, (title_x, y + 7))

        v_label = SetterValues.format_eng(float(params.voltage_r1), "V")
        i_label = SetterValues.format_eng(float(params.current_r1), "A")
        info_1 = self.font_info.render(f"V_R1: {v_label}  I_R1: {i_label}", True, (225, 225, 225))
        info_2 = self.font_info.render(
            f"Tempo: {params.explosion_delay:0.2f}s  Area: {int(params.explosion_radius)}  Pulso: {int(params.damage)}",
            True,
            (225, 225, 225),
        )
        surface.blit(info_1, (x + 8, y + 29))
        surface.blit(info_2, (x + 8, y + 47))
