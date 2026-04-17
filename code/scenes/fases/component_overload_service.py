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
    ):
        self._speed_multiplier_applier = speed_multiplier_applier
        self._total_components_provider = total_components_provider
        self._total_areas_provider = total_areas_provider
        self.total_weight = 0.0
        self._area_load: dict[int, float] = {}
        self._relieved_areas: set[int] = set()
        self.multiplier = 1.0
        self.ratio = 0.0

    def reset(self):
        self.total_weight = 0.0
        self._area_load = {}
        self._relieved_areas = set()
        self._recompute()

    def register_component(self, event: dict, kind: str = "resistor"):
        area_raw = event.get("area_id", -1)
        try:
            area_id = int(area_raw)
        except (TypeError, ValueError):
            area_id = -1
        _ = kind
        # Nova regra: cada componente coletado soma 1 unidade de peso.
        self.total_weight += 1.0
        self._area_load[area_id] = float(self._area_load.get(area_id, 0.0)) + 1.0
        self._recompute()

    def on_panel_solved(self, event: dict):
        area_raw = event.get("area_id", -1)
        try:
            area_id = int(area_raw)
        except (TypeError, ValueError):
            area_id = -1
        if area_id in self._relieved_areas:
            return

        area_load = float(self._area_load.get(area_id, 0.0))
        if area_load <= 0.0:
            return

        # Alivio inteligente: ao resolver o painel da area, remove o peso
        # associado a essa area ate o teto da media por area da fase.
        avg_per_area = self._get_phase_average_components_per_area()
        relief = min(area_load, avg_per_area)
        self._area_load[area_id] = max(0.0, area_load - relief)
        self.total_weight = max(0.0, self.total_weight - relief)
        self._relieved_areas.add(area_id)
        self._recompute()

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

        max_weight = self._get_phase_average_components_per_area()
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
        max_threshold = self._get_phase_average_components_per_area()
        self.ratio = max(0.0, min(1.0, self.total_weight / max_threshold))
        self._speed_multiplier_applier(self.multiplier)
