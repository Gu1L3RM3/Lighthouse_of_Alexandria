"""Compatibility aliases for profiles and events created before circuit schema v2."""

LEGACY_VOLTAGE_SOURCE_ENTITY = "VoutageSource"
LEGACY_VOLTAGE_SOURCE_EVENT = "voutage_source_collected"
VOLTAGE_SOURCE_ENTITY = "VoltageSource"


def normalize_entity_type(value: str) -> str:
    if value == LEGACY_VOLTAGE_SOURCE_ENTITY:
        return VOLTAGE_SOURCE_ENTITY
    return value


def looks_like_voltage_source(value: str) -> bool:
    normalized = value.casefold()
    return "voltage" in normalized or "voutage" in normalized
