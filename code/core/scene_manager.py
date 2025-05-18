from typing import Dict
from scenes.base_scene import BaseScene

class SceneManager:
    _instance = None

    def __init__(self):
        # cena name -> instância de BaseScene
        self.scenes: Dict[str, BaseScene] = {}
        self.active_scene: BaseScene 

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SceneManager()
        return cls._instance

    def register(self, name: str, scene: BaseScene):
        """Registra uma cena sob o identificador `name`."""
        self.scenes[name] = scene

    def change(self, name: str):
        """Torna a cena `name` a cena ativa."""
        if name not in self.scenes:
            raise KeyError(f"Scene '{name}' not registered.")
        self.active_scene = self.scenes[name]
