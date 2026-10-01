"""Prototype simulation modules."""

from __future__ import annotations

from .prototype import (
    HydrologyModule,
    SettlementResolutionModule,
    SettlementSuitabilityModule,
    TerrainModule,
)

_MODULES = {
    TerrainModule.spec.name: TerrainModule,
    HydrologyModule.spec.name: HydrologyModule,
    SettlementSuitabilityModule.spec.name: SettlementSuitabilityModule,
    SettlementResolutionModule.spec.name: SettlementResolutionModule,
}


def get_module_class(name: str) -> type:
    """Return a built-in module class by its Worldloom contract name."""
    return _MODULES[name]


__all__ = [
    "HydrologyModule",
    "SettlementResolutionModule",
    "SettlementSuitabilityModule",
    "TerrainModule",
    "get_module_class",
]
