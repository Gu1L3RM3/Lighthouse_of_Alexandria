from __future__ import annotations

from typing import Callable

from core.settings import (
    COMPONENT_OVERLOAD_ENABLED,
    COMPONENT_OVERLOAD_REFERENCE_COMPONENT_COUNT,
    COMPONENT_OVERLOAD_SPEED_MULTIPLIERS,
)


class ComponentOverloadService:
    def __init__(
        self,
        speed_multiplier_applier: Callable[[float], None],
        total_components_provider: Callable[[], int] | None = None,
        total_areas_provider: Callable[[], int] | None = None,
        inventory_service=None,
    ):
        self._speed_multiplier_applier = speed_multiplier_applier
        self._total_components_provider = total_components_provider
        self._total_areas_provider = total_areas_provider
        self._inventory_service = inventory_service
        self.total_weight = 0.0
        self.multiplier = 1.0
        self.ratio = 0.0
        if self._inventory_service is not None:
            self._inventory_service.add_listener(self.sync_from_inventory)
            self.sync_from_inventory()

    def reset(self):
        self.sync_from_inventory()

    def sync_from_inventory(self):
        if self._inventory_service is not None:
            self.total_weight = max(0.0, float(self._inventory_service.current_weight))
        self._recompute()

    def register_component(self, event: dict, kind: str = "resistor"):
        _ = event
        _ = kind
        self.sync_from_inventory()

    def on_panel_solved(self, event: dict):
        _ = event
        # Solving is not a transfer. Weight changes only when inventory changes.
        self.sync_from_inventory()

    def update_timers(self, dt: float):
        _ = dt
        return

    def get_snapshot(self) -> dict:
        show = bool(COMPONENT_OVERLOAD_ENABLED)
        return {
            "show": show,
            "weight": self.total_weight,
            "multiplier": self.multiplier,
            "ratio": self.ratio,
            "map_components": self._get_total_components_count(),
            "map_areas": self._get_total_area_count(),
            "avg_components_per_area": self._get_phase_average_components_per_area(),
        }

    def clear_speed_penalty(self):
        self._speed_multiplier_applier(1.0)

    def _get_total_components_count(self) -> int:
        if self._total_components_provider is None:
            return int(COMPONENT_OVERLOAD_REFERENCE_COMPONENT_COUNT)
        try:
            value = int(self._total_components_provider())
        except Exception:
            value = int(COMPONENT_OVERLOAD_REFERENCE_COMPONENT_COUNT)
        return max(1, value)

    def _get_total_area_count(self) -> int:
        if self._total_areas_provider is None:
            return 1
        try:
            value = int(self._total_areas_provider())
        except Exception:
            value = 1
        return max(1, value)

    def _get_phase_average_components_per_area(self) -> float:
        total_components = float(self._get_total_components_count())
        total_areas = float(self._get_total_area_count())
        return max(1.0, total_components / total_areas)

    def _resolve_speed_multiplier(self, weight: float) -> float:
        multipliers = tuple(float(x) for x in COMPONENT_OVERLOAD_SPEED_MULTIPLIERS)
        if not multipliers:
            return 1.0

        max_weight = self._get_max_weight()
        ratio = max(0.0, min(1.0, weight / max_weight))
        idx = int(ratio * (len(multipliers) - 1))
        return multipliers[idx]

    def _recompute(self):
        if not COMPONENT_OVERLOAD_ENABLED:
            self.multiplier = 1.0
            self.ratio = 0.0
            self._speed_multiplier_applier(self.multiplier)
            return

        self.multiplier = self._resolve_speed_multiplier(self.total_weight)
        max_threshold = self._get_max_weight()
        self.ratio = max(0.0, min(1.0, self.total_weight / max_threshold))
        self._speed_multiplier_applier(self.multiplier)

    def _get_max_weight(self) -> float:
        if self._inventory_service is not None:
            return max(1.0, float(self._inventory_service.max_weight))
        return self._get_phase_average_components_per_area()
