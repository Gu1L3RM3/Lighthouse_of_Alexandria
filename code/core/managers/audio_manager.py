from __future__ import annotations

from pathlib import Path
import pygame

from core.settings import ASSETS_DIR
from core.managers.resource_manager import ResourceManager


class AudioManager:
    _instance = None

    def __init__(self):
        self.enabled = False
        self.rm = ResourceManager.get()
        self._current_music: str | None = None
        self._warned_music_files: set[str] = set()
        self._scene_music_map = {
            "main_menu": "music/main_menu.wav",
            # Casa e narrativa introspectiva.
            "home_scene": "music/home.ogg",
            "home_after": "music/home_after.ogg",
            # Fases iniciais e desafios.
            "level_1": "music/level_1_2.flac",
            "level_2": "music/level_1_2.flac",
            "fase_3": "music/other_fases.wav",
            "fase_4": "music/other_fases.wav",
            "fase_5": "music/other_fases.wav",
            "fase_6": "music/other_fases.wav",
            "fase_7": "music/fase_7.ogg",
            # Fases de explicacao (calmas, foco didatico).
            "exp_fase_3": "music/fase_explicativa.mp3",
            "exp_fase_4": "music/fase_explicativa.mp3",
            "exp_fase_5": "music/fase_explicativa.mp3",
            "exp_fase_6": "music/fase_explicativa.mp3",
            "exp_fase_7": "music/fase_explicativa.mp3",
            # Climax/final.
            "fase_8": "music/final_theme_loop.wav",
            "final_level": "music/final_theme_loop.wav",
            "ending_lighthouse": "music/ending_lighthouse.ogg",
            "ending_thanks_credits": "music/ending_thanks_credits.ogg",
            "credits": "music/ending_thanks_credits.ogg",
            "death_transition": None,
        }
        self._default_music = "music/other_fases.wav"
        self._validate_music_files()

        self.vol_music = 0.45
        self.vol_ui = 0.70
        self.vol_sfx = 0.75
        self.vol_ambient = 0.35

        self._init_mixer()

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = AudioManager()
        return cls._instance

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.enabled = True
            pygame.mixer.set_num_channels(16)
        except pygame.error:
            self.enabled = False

    def _music_path(self, relative_path: str) -> str:
        return str(Path(ASSETS_DIR) / "sounds" / relative_path)

    def _warn_missing_music(self, relative_path: str):
        if relative_path in self._warned_music_files:
            return
        self._warned_music_files.add(relative_path)
        print(f"[AudioManager] Musica nao encontrada: {relative_path}")

    def _validate_music_files(self):
        music_files = {v for v in self._scene_music_map.values() if v is not None}
        music_files.add(self._default_music)
        for relative_path in sorted(music_files):
            if not Path(self._music_path(relative_path)).exists():
                self._warn_missing_music(relative_path)

    def set_bus_volume(self, bus: str, value: float):
        value = max(0.0, min(1.0, float(value)))
        if bus == "music":
            self.vol_music = value
            if self.enabled:
                pygame.mixer.music.set_volume(self.vol_music)
        elif bus == "ui":
            self.vol_ui = value
        elif bus == "sfx":
            self.vol_sfx = value
        elif bus == "ambient":
            self.vol_ambient = value

    def play_sfx(self, filename: str, volume: float = 1.0):
        if not self.enabled:
            return
        try:
            snd = self.rm.load_sound(filename)
            snd.set_volume(max(0.0, min(1.0, self.vol_sfx * volume)))
            snd.play()
        except Exception:
            return

    def play_ui(self, filename: str, volume: float = 1.0):
        if not self.enabled:
            return
        try:
            snd = self.rm.load_sound(filename)
            snd.set_volume(max(0.0, min(1.0, self.vol_ui * volume)))
            pygame.mixer.Channel(0).play(snd)
        except Exception:
            return

    def play_music(self, filename: str | None, fade_ms: int = 800, loop: bool = True):
        if not self.enabled:
            return
        if filename is None:
            self.stop_music(fade_ms)
            return
        if self._current_music == filename:
            return

        try:
            path = self._music_path(filename)
            if not Path(path).exists():
                self._warn_missing_music(filename)
                self._current_music = None
                return
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.vol_music)
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
            self._current_music = filename
        except Exception:
            self._current_music = None

    def stop_music(self, fade_ms: int = 600):
        if not self.enabled:
            return
        pygame.mixer.music.fadeout(fade_ms)
        self._current_music = None

    def on_scene_changed(self, scene_name: str):
        # Stinger de morte sem trocar trilha permanentemente.
        if scene_name == "death_transition":
            self.play_sfx("sfx/death_stinger.wav", volume=0.9)
            return

        if scene_name in self._scene_music_map:
            self.play_music(self._scene_music_map[scene_name])
            return

        if scene_name.startswith("generic_levels_") or scene_name.startswith("generic_level_"):
            # Fallback para nomes antigos/auxiliares.
            self.play_music("music/other_fases.wav")
            return
        self.play_music(self._default_music)
