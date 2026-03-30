from pathlib import Path

from core.ecs import System
from core.settings import (
    GENERIC_LEVEL_TEMPORARY_LIGHT_DURATION_SECONDS,
    GENERIC_LEVEL_TEMPORARY_LIGHT_FADE_OUT_SECONDS,
)
from entities.itens.crystal_invisibility_item import CrystalInvisibilityItem


class GenericLevelEnvironmentSystem(System):
    def __init__(self, scene):
        self.scene = scene

    def update(self, entity_manager, dt: float):
        _ = entity_manager
        self.update_crystal_respawn_queue(dt)
        self.update_temporary_light(dt)

    def activate_temporary_light(self, duration: float):
        if not hasattr(self.scene, "light_system"):
            return
        if self.scene._temporary_light_timer <= 0:
            self.scene._temporary_light_restore_enabled = self.scene.light_system.enabled
        self.scene.light_system.turn_on()
        self.scene._temporary_light_timer = max(0.0, float(duration))

    def activate_permanent_light(self):
        if not hasattr(self.scene, "light_system"):
            return
        self.scene.light_system.turn_on()
        if self.scene._temporary_light_timer > 0:
            self.scene._temporary_light_restore_enabled = self.scene.light_system.enabled

    def toggle_permanent_light(self):
        if not hasattr(self.scene, "light_system"):
            return

        if self.scene.light_system.enabled:
            self.scene.light_system.turn_on()
        else:
            self.scene.light_system.turn_off()

        if self.scene._temporary_light_timer > 0:
            self.scene._temporary_light_restore_enabled = self.scene.light_system.enabled

    def update_temporary_light(self, dt: float):
        if self.scene._temporary_light_timer <= 0:
            return
        self.scene._temporary_light_timer = max(0.0, self.scene._temporary_light_timer - dt)
        if self.scene._temporary_light_timer > 0:
            return
        if hasattr(self.scene, "light_system") and self.scene._temporary_light_restore_enabled is not None:
            self.scene.light_system.set_enabled(
                self.scene._temporary_light_restore_enabled,
                transition_seconds=GENERIC_LEVEL_TEMPORARY_LIGHT_FADE_OUT_SECONDS,
            )
        self.scene._temporary_light_restore_enabled = None

    def get_temporary_light_ratio(self) -> float:
        duration = float(GENERIC_LEVEL_TEMPORARY_LIGHT_DURATION_SECONDS)
        if duration <= 0:
            return 0.0
        return max(0.0, min(1.0, self.scene._temporary_light_timer / duration))

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

