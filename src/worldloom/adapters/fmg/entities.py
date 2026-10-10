"""Translation-boundary helpers for FMG entity collections.

FMG-derived entity identity is provisional: the identity-part format here is
an implementation of the current import experiment, not a settled
world/seed/address identity model. Importing two FMG maps into one WorldState
will collide because no world/seed scope is included.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from worldloom.core import derive_entity_id

from .sanitize import anomaly, anomaly_report, sanitize_strings

COLLECTION_SPECS = {
    "states": "state",
    "provinces": "province",
    "burgs": "burg",
    "cultures": "culture",
    "religions": "religion",
    "rivers": "river",
    "routes": "route",
    "markers": "marker",
}
EXCLUDED_KEYS = {
    "states": {"coa", "military", "campaigns"},
    "provinces": {"coa"},
    "burgs": {"coa", "production"},
    "cultures": set(),
    "religions": set(),
    "rivers": set(),
    "routes": set(),
    "markers": set(),
}
REFERENCE_SPECS = {
    "states": {"neighbors": ("states", False), "provinces": ("provinces", False)},
    "provinces": {"state": ("states", False), "center": ("pack.cells", True)},
    "burgs": {"cell": ("pack.cells", True), "state": ("states", False)},
    "rivers": {"cells": ("pack.cells", True)},
    "markers": {"cell": ("pack.cells", True)},
}


def _records(data: dict[str, Any], collection: str) -> list[Any]:
    value = data.get("pack", {}).get(collection, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"FMG pack.{collection} must be a list")
    return value


def _placeholder(collection: str, position: int, record: Any) -> bool:
    return (
        collection in {"provinces", "burgs"}
        and position == 0
        and isinstance(record, int)
        and not isinstance(record, bool)
    )


@dataclass
class _EntityBuildContext:
    data: dict[str, Any]
    id_maps: dict[str, dict[int, str]]
    anomalies: list[dict[str, Any]]


def _build_id_maps(
    data: dict[str, Any], anomalies: list[dict[str, Any]]
) -> dict[str, dict[int, str]]:
    id_maps: dict[str, dict[int, str]] = {collection: {} for collection in COLLECTION_SPECS}
    derived_ids: set[str] = set()
    for collection, kind in COLLECTION_SPECS.items():
        for position, record in enumerate(_records(data, collection)):
            if _placeholder(collection, position, record):
                continue
            path = f"pack.{collection}[{position}].i"
            if not isinstance(record, dict):
                anomalies.append(
                    anomaly("invalid-type", f"pack.{collection}[{position}]", position, record)
                )
                continue
            fmgi = record.get("i")
            if not isinstance(fmgi, int) or isinstance(fmgi, bool):
                anomalies.append(anomaly("invalid-type", path, position, fmgi))
                continue
            if fmgi in id_maps[collection]:
                raise ValueError(f"Duplicate explicit FMG i in pack.{collection}: {fmgi}")
            entity_id = derive_entity_id(
                kind, "source:fmg", f"collection:{collection}", f"fmg-id:{fmgi}"
            )
            if entity_id in derived_ids:
                raise ValueError(f"Derived entity ID collision: {entity_id}")
            derived_ids.add(entity_id)
            id_maps[collection][fmgi] = entity_id
    return id_maps


def _check_int_reference(
    ctx: _EntityBuildContext, value: Any, path: str, position: int
) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool):
        ctx.anomalies.append(anomaly("invalid-type", path, position, value))
        return None
    if value == -1:
        ctx.anomalies.append(anomaly("sentinel", path, position, value))
        return None
    return value


def _resolve_reference(
    ctx: _EntityBuildContext,
    position: int,
    value: Any,
    target: str,
    mesh: bool,
    path: str,
) -> Any | None:
    reference = _check_int_reference(ctx, value, path, position)
    if reference is None:
        return None
    if mesh:
        cell_count = len(_records(ctx.data, "cells"))
        if reference < 0 or reference >= cell_count:
            ctx.anomalies.append(anomaly("out-of-range", path, position, reference))
            return None
        return {"space": target, "index": reference}
    if reference in ctx.id_maps[target]:
        return ctx.id_maps[target][reference]
    target_records = _records(ctx.data, target)
    if 0 <= reference < len(target_records) and _placeholder(
        target, reference, target_records[reference]
    ):
        ctx.anomalies.append(
            anomaly("placeholder-reference", path, position, reference)
        )
    else:
        ctx.anomalies.append(anomaly("unresolved-reference", path, position, reference))
    return None


def _resolve_field(
    ctx: _EntityBuildContext,
    collection: str,
    position: int,
    field: str,
    value: Any,
    target: str,
    mesh: bool,
) -> Any | None:
    path = f"pack.{collection}[{position}].{field}"
    if isinstance(value, list):
        resolved = []
        for index, item in enumerate(value):
            item_resolved = _resolve_reference(
                ctx, position, item, target, mesh, f"{path}[{index}]"
            )
            if item_resolved is not None:
                resolved.append(item_resolved)
        # Partially resolved lists omit unresolved members; the raw list stays in attributes.
        return resolved if resolved else None
    return _resolve_reference(ctx, position, value, target, mesh, path)


def _resolve_route_points(
    ctx: _EntityBuildContext, position: int, value: Any
) -> list[dict[str, Any]] | None:
    path = f"pack.routes[{position}].points"
    if not isinstance(value, list):
        ctx.anomalies.append(anomaly("invalid-type", path, position, value))
        return None
    resolved: list[dict[str, Any]] = []
    for index, point in enumerate(value):
        point_path = f"{path}[{index}]"
        if not isinstance(point, list) or len(point) != 3:
            ctx.anomalies.append(anomaly("invalid-type", point_path, position, point))
            continue
        cell = _check_int_reference(ctx, point[2], f"{point_path}[2]", position)
        if cell is None:
            continue
        cell_count = len(_records(ctx.data, "cells"))
        if cell < 0 or cell >= cell_count:
            ctx.anomalies.append(anomaly("out-of-range", f"{point_path}[2]", position, cell))
            continue
        resolved.append({"space": "pack.cells", "index": cell})
    return resolved if resolved else None


def _entity_refs(
    ctx: _EntityBuildContext, collection: str, position: int, record: dict[str, Any]
) -> dict[str, Any]:
    refs: dict[str, Any] = {}
    for field, (target, mesh) in REFERENCE_SPECS.get(collection, {}).items():
        if field in record:
            resolved = _resolve_field(
                ctx, collection, position, field, record[field], target, mesh
            )
            if resolved is not None:
                refs[field] = resolved
    if collection == "routes" and "points" in record:
        resolved = _resolve_route_points(ctx, position, record["points"])
        if resolved is not None:
            refs["cells"] = resolved
    return refs


def _build_entity(
    ctx: _EntityBuildContext,
    collection: str,
    position: int,
    record: dict[str, Any],
    dropped: dict[str, dict[str, int]],
) -> tuple[str, dict[str, Any]]:
    attributes = sanitize_strings(
        deepcopy(record), f"pack.{collection}[{position}]", position, ctx.anomalies
    )
    for key in EXCLUDED_KEYS[collection]:
        if key in attributes:
            attributes.pop(key)
            dropped[collection][key] = dropped[collection].get(key, 0) + 1
    refs = _entity_refs(ctx, collection, position, record)
    entity_id = ctx.id_maps[collection][record["i"]]
    return entity_id, {
        "fmg": {"collection": collection, "id": record["i"], "position": position},
        "attributes": attributes,
        "refs": refs,
    }


def _entity_counts(data: dict[str, Any]) -> dict[str, int]:
    return {
        collection: sum(
            isinstance(record, dict)
            and isinstance(record.get("i"), int)
            and not isinstance(record.get("i"), bool)
            for record in _records(data, collection)
        )
        for collection in COLLECTION_SPECS
    }


def build_entities(data: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Build all entities, refs, and entity-report data before any writes."""
    anomalies: list[dict[str, Any]] = []
    id_maps = _build_id_maps(data, anomalies)
    ctx = _EntityBuildContext(data=data, id_maps=id_maps, anomalies=anomalies)
    entities: dict[str, dict[str, Any]] = {}
    dropped: dict[str, dict[str, int]] = {collection: {} for collection in COLLECTION_SPECS}

    for collection, _kind in COLLECTION_SPECS.items():
        for position, record in enumerate(_records(data, collection)):
            if _placeholder(collection, position, record):
                continue
            if (
                not isinstance(record, dict)
                or not isinstance(record.get("i"), int)
                or isinstance(record.get("i"), bool)
            ):
                continue
            entity_id, entity = _build_entity(ctx, collection, position, record, dropped)
            # Kept as a defensive guard; the first pass currently detects derived-ID collisions.
            if entity_id in entities:
                raise ValueError(f"Derived entity ID collision: {entity_id}")
            entities[entity_id] = entity

    report = {
        "entity_counts": _entity_counts(data),
        "dropped_keys": dropped,
        "anomalies": anomaly_report(anomalies),
    }
    return entities, report
