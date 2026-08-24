from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import math
import re


class CircuitError(Exception):
    """Base error for the circuit domain."""


class CircuitValidationError(CircuitError):
    """Raised when persisted or edited circuit data is invalid."""


class ElementKind(str, Enum):
    RESISTOR = "resistor"
    VOLTAGE_SOURCE = "voltage_source"
    CURRENT_SOURCE = "current_source"
    WIRE = "wire"
    NODE = "node"
    GROUND = "ground"

    @property
    def is_electrical(self) -> bool:
        return self in {
            ElementKind.RESISTOR,
            ElementKind.VOLTAGE_SOURCE,
            ElementKind.CURRENT_SOURCE,
        }


_ENGINEERING_VALUE = re.compile(
    r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)\s*(meg|[pnumkgt])?\s*$",
    re.IGNORECASE,
)
_MULTIPLIERS = {
    None: 1.0,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "meg": 1e6,
    "g": 1e9,
    "t": 1e12,
}


def parse_engineering_value(raw: str | int | float) -> float:
    if isinstance(raw, bool):
        raise CircuitValidationError("Boolean is not a valid electrical value")
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        match = _ENGINEERING_VALUE.match(str(raw))
        if match is None:
            raise CircuitValidationError(f"Invalid electrical value: {raw!r}")
        number, suffix = match.groups()
        value = float(number) * _MULTIPLIERS[suffix.lower() if suffix else None]
    if not math.isfinite(value):
        raise CircuitValidationError(f"Electrical value must be finite: {raw!r}")
    return value


@dataclass(frozen=True, slots=True)
class CircuitElement:
    kind: ElementKind
    x: int
    y: int
    rotation: int = 0
    editable: bool = True
    name: str | None = None
    value: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ElementKind):
            try:
                object.__setattr__(self, "kind", ElementKind(self.kind))
            except (TypeError, ValueError) as exc:
                raise CircuitValidationError(f"Unsupported element kind: {self.kind!r}") from exc
        normalized_rotation = int(self.rotation) % 360
        if normalized_rotation not in {0, 90, 180, 270}:
            raise CircuitValidationError(f"Invalid rotation: {self.rotation!r}")
        object.__setattr__(self, "rotation", normalized_rotation)
        object.__setattr__(self, "x", int(self.x))
        object.__setattr__(self, "y", int(self.y))

        if self.kind.is_electrical:
            if not self.name or not str(self.name).strip():
                raise CircuitValidationError(f"{self.kind.value} requires a component name")
            if self.value is None:
                raise CircuitValidationError(f"{self.name} requires a value")
            numeric_value = parse_engineering_value(self.value)
            if self.kind is ElementKind.RESISTOR and numeric_value <= 0:
                raise CircuitValidationError(f"Resistor {self.name} must be greater than zero")
            object.__setattr__(self, "name", str(self.name).strip())
            object.__setattr__(self, "value", str(self.value).strip())
        elif self.name is not None or self.value is not None:
            raise CircuitValidationError(f"{self.kind.value} cannot have name/value")

    @property
    def numeric_value(self) -> float:
        if self.value is None:
            raise CircuitValidationError(f"{self.kind.value} does not have an electrical value")
        return parse_engineering_value(self.value)


@dataclass(frozen=True, slots=True)
class CircuitDocument:
    elements: tuple[CircuitElement, ...] = ()
    schema_version: int = 2

    def __post_init__(self) -> None:
        if self.schema_version != 2:
            raise CircuitValidationError(f"Unsupported circuit schema: {self.schema_version}")
        object.__setattr__(self, "elements", tuple(self.elements))
        names: set[str] = set()
        for element in self.elements:
            if element.name is None:
                continue
            normalized = element.name.casefold()
            if normalized in names:
                raise CircuitValidationError(f"Duplicate component name: {element.name}")
            names.add(normalized)

    def with_component_value(self, component_name: str, value: str) -> CircuitDocument:
        normalized = component_name.casefold()
        changed = False
        elements: list[CircuitElement] = []
        for element in self.elements:
            if element.name and element.name.casefold() == normalized:
                elements.append(replace(element, value=str(value)))
                changed = True
            else:
                elements.append(element)
        if not changed:
            raise CircuitValidationError(f"Component not found: {component_name}")
        return CircuitDocument(tuple(elements))
