import math
import random
import pygame
from pygame import Event, Surface

from scenes.base_scene import BaseScene
from core.settings import BLACK
from core.managers.death_flow_manager import DeathFlowManager
from core.managers.audio_manager import AudioManager
from core.managers.input_manager import InputManager


class DeathTransitionScene(BaseScene):
    def __init__(self, screen: Surface):
        width, height = screen.get_size()
        super().__init__(screen, width, height)
        self.death_flow_manager = DeathFlowManager.get()
        self.audio_manager = AudioManager.get()
        self.input_manager = InputManager.get()
        self.title_font = self.resources.load_font("PressStart2P-Regular.ttf", 34)
        self.main_font = self.resources.load_font("PressStart2P-Regular.ttf", 20)
        self.small_font = self.resources.load_font("PressStart2P-Regular.ttf", 14)

        self.timer = 0.0
        self.total_duration = 2.8
        self.resolved = False
        self.particles = []
        self.lives_before = 0
        self.lives_after = 0
        self.is_game_over = False

    def start(self):
        self.timer = 0.0
        self.resolved = False
        context = self.death_flow_manager.get_death_context() or {}
        self.lives_before = int(context.get("lives_before", 0))
        self.lives_after = int(context.get("lives_after", 0))
        self.is_game_over = bool(context.get("is_game_over", False))
        if self.is_game_over:
            self.audio_manager.play_sfx("sfx/game_over.wav", volume=1.0)
        self._spawn_particles(42)

    def process_input(self, events: list[Event]) -> None:
        if self.timer >= 1.0 and (
            self.input_manager.is_action_just_pressed("confirm")
            or self.input_manager.is_action_just_pressed("back")
        ):
            self._resolve()
            return

        for event in events:
            if event.type == pygame.KEYDOWN and self.timer >= 1.0:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._resolve()

    def update(self, dt: float) -> None:
        self.timer += dt
        for particle in self.particles:
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt
            particle["life"] -= dt
            particle["alpha"] = max(0, int(255 * (particle["life"] / particle["max_life"])))

        self.particles = [p for p in self.particles if p["life"] > 0]
        while len(self.particles) < 24:
            self._spawn_particles(4)

        if self.timer >= self.total_duration:
            self._resolve()

    def render(self) -> None:
        w, h = self.screen.get_size()
        self.screen.fill(BLACK)

        # Fundo em camadas para manter leitura sem quebrar a identidade do jogo
        for i in range(h):
            tone = int(10 + 28 * (i / max(1, h - 1)))
            pygame.draw.line(self.screen, (tone, tone // 2, tone + 10), (0, i), (w, i))

        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 115), (0, 0, w, h), border_radius=0)
        self.screen.blit(vignette, (0, 0))

        self._draw_particles()
        self._draw_panel()

    def _spawn_particles(self, amount: int):
        w, h = self.screen.get_size()
        for _ in range(amount):
            x = random.randint(int(w * 0.2), int(w * 0.8))
            y = random.randint(int(h * 0.22), int(h * 0.78))
            speed = random.uniform(12, 44)
            angle = random.uniform(-2.8, -0.35)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "radius": random.randint(1, 3),
                    "life": random.uniform(0.6, 1.6),
                    "max_life": 1.6,
                    "alpha": 255,
                }
            )

    def _draw_particles(self):
        for p in self.particles:
            dot = pygame.Surface((p["radius"] * 4, p["radius"] * 4), pygame.SRCALPHA)
            c = (252, 205, 120, p["alpha"])
            pygame.draw.circle(dot, c, (p["radius"] * 2, p["radius"] * 2), p["radius"])
            self.screen.blit(dot, (int(p["x"]), int(p["y"])))

    def _draw_panel(self):
        w, h = self.screen.get_size()
        panel_w = min(760, int(w * 0.68))
        panel_h = min(440, int(h * 0.55))
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (w // 2, h // 2)

        board = pygame.Surface(panel.size, pygame.SRCALPHA)
        pygame.draw.rect(board, (26, 23, 18, 235), board.get_rect(), border_radius=12)
        pygame.draw.rect(board, (170, 136, 79, 255), board.get_rect(), width=4, border_radius=12)
        inner = board.get_rect().inflate(-18, -18)
        pygame.draw.rect(board, (57, 48, 35, 220), inner, border_radius=10)
        pygame.draw.rect(board, (201, 164, 94, 180), inner, width=2, border_radius=10)
        self.screen.blit(board, panel.topleft)

        title = "GAME OVER" if self.is_game_over else "TENTATIVA PERDIDA"
        subtitle = "As sombras vencem por ora; voltamos ao inicio da jornada para tentar de novo." if self.is_game_over else "Respire e tente novamente."
        title_color = (244, 132, 98) if self.is_game_over else (245, 214, 132)
        title_surf = self.title_font.render(title, True, title_color)
        sub_surf = self.small_font.render(subtitle, True, (215, 196, 151))
        self.screen.blit(title_surf, title_surf.get_rect(center=(panel.centerx, panel.top + 74)))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(panel.centerx, panel.top + 118)))

        phase = max(0.0, min(1.0, (self.timer - 0.55) / 0.85))
        pulse = 1.0 + 0.35 * math.sin(self.timer * 12.0) * (1.0 - phase)
        lives_text_before = self.main_font.render(str(self.lives_before), True, (238, 206, 126))
        lives_text_after = self.main_font.render(str(self.lives_after), True, (244, 136, 110) if self.is_game_over else (175, 236, 148))

        label = self.small_font.render("TENTATIVAS", True, (220, 188, 130))
        self.screen.blit(label, label.get_rect(center=(panel.centerx, panel.centery - 22)))

        before_scaled = pygame.transform.scale(
            lives_text_before,
            (
                max(1, int(lives_text_before.get_width() * pulse)),
                max(1, int(lives_text_before.get_height() * pulse)),
            ),
        )
        self.screen.blit(before_scaled, before_scaled.get_rect(center=(panel.centerx - 54, panel.centery + 26)))

        arrow = self.main_font.render("->", True, (220, 188, 130))
        self.screen.blit(arrow, arrow.get_rect(center=(panel.centerx, panel.centery + 26)))

        after_alpha = int(255 * phase)
        lives_text_after.set_alpha(after_alpha)
        self.screen.blit(lives_text_after, lives_text_after.get_rect(center=(panel.centerx + 54, panel.centery + 26)))

        if self.timer >= 1.0:
            hint_button = self.input_manager.get_prompt_button("confirm")
            hint = f"{hint_button} para avancar"
        else:
            hint = "..."
        hint_surf = self.small_font.render(hint, True, (177, 156, 120))
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(panel.centerx, panel.bottom - 34)))

    def _resolve(self):
        if self.resolved:
            return
        self.resolved = True
        self.death_flow_manager.resolve_death_transition(0.55)
