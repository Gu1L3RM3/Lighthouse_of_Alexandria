from pathlib import Path

from core.ecs import System
from entities.itens.crystal_invisibility_item import CrystalInvisibilityItem


class GenericLevelEnvironmentSystem(System):
    def __init__(self, scene):
        self.scene = scene

    def update(self, entity_manager, dt: float):
        _ = entity_manager
        self.update_crystal_respawn_queue(dt)

    def uses_custom_crystal_respawn(self) -> bool:
        level_name = Path(self.scene.level_path).stem.lower()
        return level_name in {"fase_8", "final_level"}

    def on_crystal_invisibility_collected(self, event: dict):
        self.scene.crystal_respawn_queue.append(
            {
                "remaining": float(event.get("respawn_delay", 20.0)),
                "x": float(event.get("spawn_x", 0.0)),
                "y": float(event.get("spawn_y", 0.0)),
                "duration": float(event.get("duration", 6.0)),
                "respawn_delay": float(event.get("respawn_delay", 20.0)),
            }
        )

    def update_crystal_respawn_queue(self, dt: float):
        if self.uses_custom_crystal_respawn() or not self.scene.crystal_respawn_queue:
            return

        still_waiting: list[dict] = []
        for entry in self.scene.crystal_respawn_queue:
            entry["remaining"] -= dt
            if entry["remaining"] > 0:
                still_waiting.append(entry)
                continue

            props = {
                "duration": entry["duration"],
                "respawn_delay": entry["respawn_delay"],
                "tmx_file": self.scene.tile_map.tmx_file,
            }
            crystal = CrystalInvisibilityItem(entry["x"], entry["y"], True, props)
            self.scene.entity_mn.add_entity(crystal)

        self.scene.crystal_respawn_queue = still_waiting

