from core.managers.life_manager import LifeManager
from core.managers.scene_manager import SceneManager
from core.managers.scene_factory import SceneFactory
from core.managers.save_game_manager import SaveGameManager


class DeathFlowManager:
    _instance = None

    def __init__(self):
        self.life_manager = LifeManager.get()
        self.scene_manager = SceneManager.get()
        self.scene_factory = SceneFactory.get()
        self.save_manager = SaveGameManager.get()
        self.death_scene_name = "death_transition"
        self.game_over_return_scene = "level_2"
        self.death_context: dict | None = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = DeathFlowManager()
        return cls._instance

    def handle_player_death(self, duration: float = 0.5):
        if not self.scene_manager.active_scene_name:
            return

        lives_before = self.life_manager.current_lives
        lives_after = self.life_manager.lose_life()
        is_game_over = self.life_manager.is_game_over()
        active_scene = self.scene_manager.active_scene
        if is_game_over and active_scene and hasattr(active_scene, "reset_bomb_circuit_to_default"):
            try:
                active_scene.reset_bomb_circuit_to_default()
            except Exception:
                pass

        self.death_context = {
            "lives_before": lives_before,
            "lives_after": lives_after,
            "is_game_over": is_game_over,
            "return_scene_name": self.scene_manager.active_scene_name,
        }
        # Mantem o save coerente mesmo se o jogador fechar o jogo na transicao.
        if is_game_over:
            self.save_manager.autosave_scene(
                self.game_over_return_scene,
                current_lives=self.life_manager.max_lives,
                max_lives=self.life_manager.max_lives,
            )
        else:
            self.save_manager.autosave_scene(
                self.scene_manager.active_scene_name,
                current_lives=lives_after,
                max_lives=self.life_manager.max_lives,
            )
        self.scene_manager.start_fade(self.death_scene_name, duration)

    def get_death_context(self) -> dict | None:
        return self.death_context

    def resolve_death_transition(self, duration: float = 0.55):
        if not self.death_context:
            self.scene_manager.start_fade(self.game_over_return_scene, duration)
            return

        context = self.death_context
        self.death_context = None

        if context["is_game_over"]:
            self.life_manager.reset_lives()
            self.scene_manager.start_new_journey(
                start_scene_name=self.game_over_return_scene,
                duration=duration,
            )
            return

        return_scene_name = context["return_scene_name"]
        if return_scene_name not in self.scene_manager.scenes:
            self.scene_manager.start_fade(self.game_over_return_scene, duration)
            return

        new_scene = self.scene_factory.recreate(self.scene_manager.scenes[return_scene_name])
        self.scene_manager.replace_scene_and_fade(return_scene_name, new_scene, duration)
