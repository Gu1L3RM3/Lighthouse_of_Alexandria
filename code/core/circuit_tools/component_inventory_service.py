from __future__ import annotations

from collections.abc import Callable, Iterable

from core.settings import COMPONENT_OVERLOAD_BASE_WEIGHT


class ComponentInventoryService:
    """Owns component transfers between the player inventory and circuits."""

    _CANONICAL_TYPE = {
        "resistor": "resistor",
        "currentsource": "current_source",
        "current_source": "current_source",
        "voutagesource": "voltage_source",
        "voltagesource": "voltage_source",
        "voltage_source": "voltage_source",
    }

    def __init__(
        self,
        storage_manager,
        max_weight_provider: Callable[[], float],
        weights: dict[str, float] | None = None,
    ):
        self.storage_manager = storage_manager
        self._max_weight_provider = max_weight_provider
        self._weights = dict(weights or COMPONENT_OVERLOAD_BASE_WEIGHT)
        self._listeners: list[Callable[[], None]] = []
        self._storage_notifies = hasattr(self.storage_manager, "add_listener")
        if self._storage_notifies:
            self.storage_manager.add_listener(self.notify_changed)

    @classmethod
    def normalize_type(cls, component_type: str) -> str | None:
        compact = str(component_type or "").replace(" ", "").replace("-", "").lower()
        return cls._CANONICAL_TYPE.get(compact)

    @property
    def max_weight(self) -> float:
        try:
            return max(1.0, float(self._max_weight_provider()))
        except (TypeError, ValueError):
            return 1.0

    @property
    def current_weight(self) -> float:
        total = 0.0
        for storage_type, values in self.storage_manager.storage_circuit.items():
            canonical = self.normalize_type(storage_type)
            if canonical is None:
                continue
            unit_weight = float(self._weights.get(canonical, 0.0))
            total += unit_weight * sum(max(0, int(quantity)) for quantity in values.values())
        return total

    def unit_weight(self, component_type: str) -> float:
        canonical = self.normalize_type(component_type)
        if canonical is None:
            return 0.0
        return max(0.0, float(self._weights.get(canonical, 0.0)))

    @property
    def ratio(self) -> float:
        return max(0.0, min(1.0, self.current_weight / self.max_weight))

    @property
    def is_full(self) -> bool:
        return self.current_weight >= self.max_weight

    def add_listener(self, listener: Callable[[], None]):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def notify_changed(self):
        for listener in tuple(self._listeners):
            listener()

    def can_add(self, component_type: str, quantity: int = 1) -> bool:
        canonical = self.normalize_type(component_type)
        quantity = int(quantity)
        if canonical is None or quantity <= 0:
            return False
        added_weight = self.unit_weight(canonical) * quantity
        return self.current_weight + added_weight <= self.max_weight + 1e-9

    def try_add(self, component_type: str, value: str, quantity: int = 1) -> bool:
        quantity = int(quantity)
        if not self.can_add(component_type, quantity):
            return False
        self.storage_manager.add_component(component_type, str(value), quantity=quantity)
        if not self._storage_notifies:
            self.notify_changed()
        return True

    def try_add_many(self, components: Iterable[tuple[str, str, int]]) -> bool:
        entries = [(kind, str(value), int(quantity)) for kind, value, quantity in components]
        if not entries or any(quantity <= 0 for _, _, quantity in entries):
            return False
        added_weight = 0.0
        for component_type, _, quantity in entries:
            canonical = self.normalize_type(component_type)
            if canonical is None:
                return False
            added_weight += self.unit_weight(canonical) * quantity
        if self.current_weight + added_weight > self.max_weight + 1e-9:
            return False
        for component_type, value, quantity in entries:
            self.storage_manager.add_component(component_type, value, quantity=quantity)
        if not self._storage_notifies:
            self.notify_changed()
        return True

    def try_remove(self, component_type: str, value: str, quantity: int = 1) -> bool:
        removed = self.storage_manager.remove_component(component_type, str(value), quantity=int(quantity))
        if removed and not self._storage_notifies:
            self.notify_changed()
        return removed
