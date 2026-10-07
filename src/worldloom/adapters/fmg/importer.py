# Import the mesh and entity portions of an Azgaar Fantasy Map Generator full JSON snapshot.

from __future__ import annotations

from pathlib import Path
from typing import Any

from worldloom.core import Provenance, WorldState

from .diagnostics import build_mesh_diagnostics
from .entities import COLLECTION_SPECS, _sanitize_strings, build_entities
from .source import FMGSource, load_fmg_source

IMPORTER_VERSION = "0.3.0"


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


def import_fmg_snapshot(
    world: WorldState,
    path: str | Path,
    *,
    scope: str | None = None,
) -> None:
    if scope is not None:
        raise NotImplementedError("FMG entity identity scope is deferred")
    source = load_fmg_source(path)
    metadata = _source_metadata(source)
    source_anomalies: list[dict[str, Any]] = []
    metadata = _sanitize_strings(metadata, "fmg.source", -1, source_anomalies)
    diagnostics = build_mesh_diagnostics(source.data)
    entities, entity_report = build_entities(source.data)
    if source_anomalies:
        anomaly_counts = entity_report["anomalies"]["counts"].setdefault("lone-surrogate", {})
        for anomaly in source_anomalies:
            anomaly_counts[anomaly["path"]] = anomaly_counts.get(anomaly["path"], 0) + 1
        entity_report["anomalies"]["examples"].extend(source_anomalies)
        entity_report["anomalies"]["examples"].sort(
            key=lambda item: (item["path"], item["position"], item["kind"], repr(item["value"]))
        )
        entity_report["anomalies"]["examples"] = entity_report["anomalies"]["examples"][:20]
        entity_report["anomalies"]["total"] += len(source_anomalies)
    report = {
        "source": metadata,
        "mesh": {
            "pack_cells": len(source.pack["cells"]),
            "pack_vertices": len(source.pack.get("vertices", [])),
        },
        "diagnostics": diagnostics,
        "entities": entity_report,
    }

    existing = set(world.entities)
    collisions = sorted(existing.intersection(entities))
    if collisions:
        raise ValueError(f"Entity already exists: {collisions[0]}")

    # All validation, entity construction, reference resolution, and reporting
    # happen before any WorldState write, preserving PR 1 all-or-nothing import.
    for collection in COLLECTION_SPECS:
        provenance = _provenance(source, collection)
        for entity_id, entity in entities.items():
            if entity["fmg"]["collection"] == collection:
                world.add_entity(entity_id, entity, provenance)

    world.set_field("fmg.pack.cells", source.pack["cells"], _provenance(source, "pack.cells"))
    world.set_field("fmg.pack.vertices", source.pack.get("vertices", []), _provenance(source, "pack.vertices"))
    world.set_field("fmg.source", metadata, _provenance(source, "source"))
    world.set_observation("fmg.import.report", report, _provenance(source, "import.report"))
