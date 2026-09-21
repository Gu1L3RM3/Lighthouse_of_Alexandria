"""Compatibility aliases for profiles and events created before circuit schema v2."""

RESISTOR_ENTITY = "Resistor"
CURRENT_SOURCE_ENTITY = "CurrentSource"
VOLTAGE_SOURCE_ENTITY = "VoltageSource"
LEGACY_VOLTAGE_SOURCE_ENTITY = "VoutageSource"
LEGACY_VOLTAGE_SOURCE_EVENT = "voutage_source_collected"

INVENTORY_COMPONENT_TYPES = frozenset(
    {RESISTOR_ENTITY, CURRENT_SOURCE_ENTITY, VOLTAGE_SOURCE_ENTITY}
)
INVENTORY_COMPONENT_TYPE_BY_KIND = {
    "resistor": RESISTOR_ENTITY,
    "current_source": CURRENT_SOURCE_ENTITY,
    "voltage_source": VOLTAGE_SOURCE_ENTITY,
}

_INVENTORY_TYPE_ALIASES = {
    "resistor": RESISTOR_ENTITY,
    "currentsource": CURRENT_SOURCE_ENTITY,
    "current_source": CURRENT_SOURCE_ENTITY,
    "voltagesource": VOLTAGE_SOURCE_ENTITY,
    "voltage_source": VOLTAGE_SOURCE_ENTITY,
    "voutagesource": VOLTAGE_SOURCE_ENTITY,
}


def normalize_entity_type(value: str) -> str:
    return _INVENTORY_TYPE_ALIASES.get(str(value).casefold(), value)


def normalize_inventory_component_type(value: str) -> str:
    """Return the canonical key used by inventory persistence and the editor."""
    normalized = normalize_entity_type(value)
    if normalized not in INVENTORY_COMPONENT_TYPES:
        raise ValueError(f"Unsupported inventory component type: {value!r}")
    return normalized


def looks_like_voltage_source(value: str) -> bool:
    normalized = value.casefold()
    return "voltage" in normalized or "voutage" in normalized
