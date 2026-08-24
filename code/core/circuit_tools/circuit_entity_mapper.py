from __future__ import annotations

import re
from collections.abc import Iterable

from core.circuit_tools.circuit_domain import CircuitDocument, CircuitElement, ElementKind
from core.components.connectable import Connectable
from core.components.dropped import Dropped
from core.components.label_component import LabelComponent
from core.components.position import Position
from core.components.sprite import Sprite
from core.ecs import Entity
from entities.circuit_editor.eletric_components import (
    CurrentSource,
    Ground,
    Node,
    Resistor,
    VoltageSource,
    Wire,
)


_ENTITY_TO_KIND = {
    Resistor: ElementKind.RESISTOR,
    VoltageSource: ElementKind.VOLTAGE_SOURCE,
    CurrentSource: ElementKind.CURRENT_SOURCE,
    Wire: ElementKind.WIRE,
    Node: ElementKind.NODE,
    Ground: ElementKind.GROUND,
}


class CircuitEntityMapper:
    def from_entities(self, entities: Iterable[Entity]) -> CircuitDocument:
        elements: list[CircuitElement] = []
        for entity in entities:
            kind = next((mapped for cls, mapped in _ENTITY_TO_KIND.items() if isinstance(entity, cls)), None)
            if kind is None:
                continue
            position = entity.get(Position)
            sprite = entity.get(Sprite)
            dropped = entity.get(Dropped)
            label = entity.get(LabelComponent) if kind.is_electrical else None
            elements.append(
                CircuitElement(
                    kind=kind,
                    x=int(position.x),
                    y=int(position.y),
                    rotation=int(sprite.angle),
                    editable=bool(dropped.can_dropped),
                    name=label.name if label else None,
                    value=label.value if label else None,
                )
            )
        return CircuitDocument(tuple(elements))

    def to_entities(self, document: CircuitDocument) -> list[Entity]:
        return [self._to_entity(element) for element in document.elements]

    def _to_entity(self, element: CircuitElement) -> Entity:
        if element.kind is ElementKind.RESISTOR:
            entity = Resistor(element.x, element.y, self._numeric_id(element.name), element.value or "")
        elif element.kind is ElementKind.VOLTAGE_SOURCE:
            entity = VoltageSource(element.x, element.y, self._numeric_id(element.name), element.value or "")
        elif element.kind is ElementKind.CURRENT_SOURCE:
            entity = CurrentSource(element.x, element.y, self._numeric_id(element.name), element.value or "")
        elif element.kind is ElementKind.WIRE:
            entity = Wire(element.x, element.y)
        elif element.kind is ElementKind.NODE:
            entity = Node(element.x, element.y)
        elif element.kind is ElementKind.GROUND:
            entity = Ground(element.x, element.y)
        else:  # pragma: no cover
            raise ValueError(element.kind)

        if element.kind.is_electrical:
            label = entity.get(LabelComponent)
            label.name = element.name or ""
            label.value = element.value or ""
        sprite = entity.get(Sprite)
        if element.rotation:
            sprite.rotate(element.rotation)
            entity.get(Connectable).set_connections(element.rotation)
        entity.get(Dropped).can_dropped = element.editable
        return entity

    @staticmethod
    def _numeric_id(name: str | None) -> int:
        match = re.search(r"(\d+)$", name or "")
        return int(match.group(1)) if match else 1
