"""Adapters for integrating established specialist systems with Worldloom."""

from __future__ import annotations
from typing import Any, Mapping

from .fmg import import_fmg_snapshot
from .geotiff import export_world_rasters
from .raster import RasterTerrainAdapter

def _export_geotiff(world, path: str, config: Mapping[str, Any]) -> None:
    export_world_rasters(world, path, config["fields"], reference_field=config["reference_field"])

_OUTPUT_ADAPTERS = {"geotiff": _export_geotiff}

def get_output_adapter(name: str):
    return _OUTPUT_ADAPTERS[name]

__all__ = ["RasterTerrainAdapter", "export_world_rasters", "import_fmg_snapshot", "get_output_adapter"]
