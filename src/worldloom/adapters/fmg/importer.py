# Import the mesh portion of an Azgaar FMG full JSON snapshot.

from __future__ import annotations
from pathlib import Path
from typing import Any
from worldloom.core import Provenance, WorldState
from .diagnostics import build_mesh_diagnostics
from .source import FMGSource, load_fmg_source

IMPORTER_VERSION = "0.1.0"

def _provenance(source: FMGSource, collection: str) -> Provenance:
    info = source.info
    return Provenance(
        producer="worldloom.adapters.fmg",
        inputs=(source.path.name, source.sha256),
        configuration={
            "collection": collection,
            "fmg_version": info.get("version"),
            "mapId": info.get("mapId"),
            "seed": info.get("seed"),
            "importer_version": IMPORTER_VERSION,
        },
        time=0.0,
    )

def _source_metadata(source: FMGSource) -> dict[str, Any]:
    info = source.info
    return {
        "source": source.path.name,
        "sha256": source.sha256,
        "byte_size": len(source.raw_bytes),
        "fmg_version": info.get("version"),
        "mapId": info.get("mapId"),
        "seed": info.get("seed"),
        "width": info.get("width"),
        "height": info.get("height"),
        "mapCoordinates": source.data.get("mapCoordinates"),
    }

def import_fmg_snapshot(world: WorldState, path: str | Path, *, scope: str | None = None) -> None:
    # scope is accepted now so the eventual identity decision does not change the import boundary.
    del scope
    source = load_fmg_source(path)
    metadata = _source_metadata(source)
    world.set_field("fmg.pack.cells", source.pack["cells"], _provenance(source, "pack.cells"))
    world.set_field("fmg.pack.vertices", source.pack.get("vertices", []), _provenance(source, "pack.vertices"))
    world.set_field("fmg.source", metadata, _provenance(source, "source"))
    world.set_observation(
        "fmg.import.report",
        {
            "source": metadata,
            "mesh": {
                "pack_cells": len(source.pack["cells"]),
                "pack_vertices": len(source.pack.get("vertices", [])),
            },
            "diagnostics": build_mesh_diagnostics(source.data),
        },
        _provenance(source, "import.report"),
    )
