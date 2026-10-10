# Import the mesh and entity portions of an Azgaar Fantasy Map Generator full JSON snapshot.

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from worldloom.core import Provenance, WorldState

from .diagnostics import build_mesh_diagnostics
from .entities import COLLECTION_SPECS, build_entities
from .sanitize import anomaly, anomaly_report, sanitize_strings
from .source import FMGSource, load_fmg_source

IMPORTER_VERSION = "0.4.0"



def _provenance_values(source: FMGSource) -> dict[str, Any]:
    """Sanitize only the FMG metadata fields used by provenance."""
    # Position -1 marks fmg.source metadata anomalies in the report sort.
    return {
        key: sanitize_strings(source.info.get(key), f"fmg.source.{key}", -1, [])
        for key in ("version", "mapId", "seed")
    }


def _provenance(
    source: FMGSource,
    collection: str,
    *,
    values: dict[str, Any] | None = None,
) -> Provenance:
    if values is None:
        values = _provenance_values(source)
    return Provenance(
        producer="worldloom.adapters.fmg",
        inputs=(source.path.name, source.sha256),
        configuration={
            "collection": collection,
            "fmg_version": values["version"],
            "mapId": values["mapId"],
            "seed": values["seed"],
            "importer_version": IMPORTER_VERSION,
        },
        time=0.0,
    )


def _build_lookup(
    source: FMGSource,
    collection: str,
    *,
    drop_feature_placeholder: bool = False,
) -> tuple[dict[int, Any], dict[str, Any]]:
    records = source.pack.get(collection, [])
    if not isinstance(records, list):
        raise ValueError(f"FMG pack.{collection} must be a list")

    lookup: dict[int, Any] = {}
    anomalies: list[dict[str, Any]] = []
    dropped_placeholder_count = 0
    for position, record in enumerate(records):
        if (
            drop_feature_placeholder
            and position == 0
            and isinstance(record, int)
            and not isinstance(record, bool)
        ):
            dropped_placeholder_count += 1
            continue
        path = f"pack.{collection}[{position}]"
        if not isinstance(record, dict):
            anomalies.append(anomaly("invalid-type", path, position, record))
            continue
        fmgi = record.get("i")
        if not isinstance(fmgi, int) or isinstance(fmgi, bool):
            anomalies.append(anomaly("invalid-type", f"{path}.i", position, fmgi))
            continue
        if fmgi in lookup:
            raise ValueError(f"Duplicate explicit FMG i in pack.{collection}: {fmgi}")
        lookup[fmgi] = sanitize_strings(
            deepcopy(record), path, position, anomalies
        )

    return lookup, {
        "retained": len(lookup),
        "dropped_placeholder_count": dropped_placeholder_count,
        "anomalies": anomaly_report(anomalies),
    }


def _build_climate(source: FMGSource) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    grid = source.data.get("grid")
    grid_cells = grid.get("cells") if isinstance(grid, dict) else None
    if not isinstance(grid_cells, list):
        return {}, {
            "retained_grid_cells": 0,
            "pack_cells_with_usable_g": 0,
            "fields": {"temp": 0, "prec": 0},
            "anomalies": anomaly_report(
                [anomaly("missing-section", "grid.cells", -1, None)]
            ),
        }

    anomalies: list[dict[str, Any]] = []
    for index, record in enumerate(grid_cells):
        if isinstance(record, dict) and record.get("i") != index:
            anomalies.append(
                anomaly(
                    "id-position-mismatch",
                    f"grid.cells[{index}].i",
                    index,
                    record.get("i"),
                )
            )

    pack_cells = source.pack["cells"]
    climate: dict[int, dict[str, Any]] = {}
    reached: set[int] = set()
    usable_g_count = 0
    for position, cell in enumerate(pack_cells):
        g = cell.get("g") if isinstance(cell, dict) else None
        path = f"pack.cells[{position}].g"
        if not isinstance(g, int) or isinstance(g, bool):
            anomalies.append(anomaly("invalid-type", path, position, g))
            continue
        if g == -1:
            anomalies.append(anomaly("sentinel", path, position, g))
            continue
        if g < 0 or g >= len(grid_cells):
            anomalies.append(anomaly("out-of-range", path, position, g))
            continue
        usable_g_count += 1
        reached.add(g)

    for g in sorted(reached):
        record = grid_cells[g]
        if not isinstance(record, dict):
            anomalies.append(anomaly("invalid-type", f"grid.cells[{g}]", g, record))
            climate[g] = {}
            continue
        values: dict[str, Any] = {}
        for field in ("temp", "prec"):
            if field in record:
                values[field] = record[field]
            else:
                anomalies.append(
                    anomaly("missing-field", f"grid.cells[{g}].{field}", g, None)
                )
        climate[g] = values

    return climate, {
        "retained_grid_cells": len(climate),
        "pack_cells_with_usable_g": usable_g_count,
        "fields": {
            field: sum(field in values for values in climate.values())
            for field in ("temp", "prec")
        },
        "anomalies": anomaly_report(anomalies),
    }


def _lookup_observation(
    source: FMGSource,
    field: str,
    lookup: dict[int, Any],
) -> dict[str, Any]:
    missing: set[Any] = set()
    values: set[Any] = set()
    for cell in source.pack["cells"]:
        if isinstance(cell, dict):
            value = cell.get(field)
            values.add(
                value
                if isinstance(value, (int, str, float, bool, type(None)))
                else repr(value)
            )
            if not isinstance(value, int) or isinstance(value, bool):
                missing.add(
                    value
                    if isinstance(value, (str, int, float, bool, type(None)))
                    else repr(value)
                )
            elif value not in lookup:
                missing.add(value)
    return {
        "all_pack_cells_reference_lookup_keys": not missing,
        "missing_values": sorted(missing, key=repr),
        "unique_pack_cell_values": len(values),
    }


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
    metadata = sanitize_strings(metadata, "fmg.source", -1, source_anomalies)
    diagnostics = build_mesh_diagnostics(source.data)
    entities, entity_report = build_entities(source.data)
    features, feature_report = _build_lookup(
        source, "features", drop_feature_placeholder=True
    )
    biomes, biome_report = _build_lookup(source, "biomes")
    climate, climate_report = _build_climate(source)

    lookup_observations = {
        "features": _lookup_observation(source, "f", features),
        "biomes": _lookup_observation(source, "biome", biomes),
    }
    if source_anomalies:
        anomaly_counts = entity_report["anomalies"]["counts"].setdefault(
            "lone-surrogate", {}
        )
        for source_anomaly in source_anomalies:
            anomaly_counts[source_anomaly["path"]] = (
                anomaly_counts.get(source_anomaly["path"], 0) + 1
            )
        entity_report["anomalies"]["examples"].extend(source_anomalies)
        entity_report["anomalies"]["examples"].sort(
            key=lambda item: (
                item["path"],
                item["position"],
                item["kind"],
                repr(item["value"]),
            )
        )
        entity_report["anomalies"]["examples"] = entity_report["anomalies"][
            "examples"
        ][:20]
        entity_report["anomalies"]["total"] += len(source_anomalies)
    report = {
        "source": metadata,
        "mesh": {
            "pack_cells": len(source.pack["cells"]),
            "pack_vertices": len(source.pack.get("vertices", [])),
        },
        "diagnostics": diagnostics,
        "entities": entity_report,
        "features": feature_report,
        "biomes": biome_report,
        "climate": climate_report,
        "lookup_observations": lookup_observations,
    }

    existing = set(world.entities)
    collisions = sorted(existing.intersection(entities))
    if collisions:
        raise ValueError(f"Entity already exists: {collisions[0]}")

    provenance_values = _provenance_values(source)
    provenance = {
        collection: _provenance(source, collection, values=provenance_values)
        for collection in (
            *COLLECTION_SPECS,
            "features",
            "biomes",
            "grid.climate",
            "pack.cells",
            "pack.vertices",
            "source",
            "import.report",
        )
    }

    # All validation, entity construction, reference resolution, lookup
    # construction, reporting, and provenance construction happen before any
    # WorldState write.
    for collection in COLLECTION_SPECS:
        for entity_id, entity in entities.items():
            if entity["fmg"]["collection"] == collection:
                world.add_entity(entity_id, entity, provenance[collection])

    world.set_field("fmg.features", features, provenance["features"])
    world.set_field("fmg.biomes", biomes, provenance["biomes"])
    world.set_field("fmg.grid.climate", climate, provenance["grid.climate"])
    world.set_field("fmg.pack.cells", source.pack["cells"], provenance["pack.cells"])
    world.set_field(
        "fmg.pack.vertices",
        source.pack.get("vertices", []),
        provenance["pack.vertices"],
    )
    world.set_field("fmg.source", metadata, provenance["source"])
    world.set_observation(
        "fmg.import.report", report, provenance["import.report"]
    )

