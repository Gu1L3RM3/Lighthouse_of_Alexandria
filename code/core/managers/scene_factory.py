from scenes.base_scene import BaseScene


class SceneFactory:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = SceneFactory()
        return cls._instance

    def recreate(self, scene: BaseScene) -> BaseScene:
        scene_class = type(scene)
        screen = scene.screen
        if hasattr(scene, "level_path"):
            return scene_class(screen, level_path=scene.level_path)
        return scene_class(screen)
