"""Adapters for integrating established specialist systems with Worldloom."""

from __future__ import annotations

from typing import Any, Mapping

from .fmg import import_fmg_snapshot
from .geotiff import export_world_rasters
from .markdown_vault import export_markdown_vault
from .raster import RasterTerrainAdapter


def _export_geotiff(world, path: str, config: Mapping[str, Any]) -> None:
    export_world_rasters(
        world,
        path,
        config["fields"],
        reference_field=config["reference_field"],
    )


_OUTPUT_ADAPTERS = {
    "geotiff": _export_geotiff,
}


def get_output_adapter(name: str):
    """Return a built-in output adapter by its configuration name."""
    return _OUTPUT_ADAPTERS[name]


__all__ = [
    "RasterTerrainAdapter",
    "export_world_rasters",
    "export_markdown_vault",
    "import_fmg_snapshot",
    "get_output_adapter",
]
