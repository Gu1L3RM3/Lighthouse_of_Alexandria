"""Small, JSON-safe descriptions of a circuit the player submitted."""

from collections import Counter

EDIT_KINDS = ("placed", "deleted", "rotated", "cleared")
SOURCE_KINDS = ("voltage_source", "current_source")
RESISTOR_KIND = "resistor"


def _kind_name(element) -> str:
    kind = element.kind
    return getattr(kind, "value", str(kind))


def summarize_circuit(document) -> dict:
    elements = list(getattr(document, "elements", ()))
    counts = Counter(_kind_name(element) for element in elements)
    sources: dict[str, list[str]] = {}
    for element in elements:
        kind = _kind_name(element)
        if kind in SOURCE_KINDS:
            sources.setdefault(kind, []).append(element.value)
    return {
        "component_counts": dict(counts),
        "resistor_values": [element.value for element in elements if _kind_name(element) == RESISTOR_KIND],
        "source_values": sources,
    }


class EditTally:
    """Counts the edits of one editor session, reported once per submit instead of one event each."""

    def __init__(self):
        self._counts = dict.fromkeys(EDIT_KINDS, 0)

    def count(self, kind: str) -> None:
        self._counts[kind] = self._counts.get(kind, 0) + 1

    def as_dict(self) -> dict:
        return dict(self._counts)
