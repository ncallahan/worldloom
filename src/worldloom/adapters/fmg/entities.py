"""Translation-boundary helpers for FMG entity collections.

FMG-derived entity identity is provisional: the identity-part format here is
an implementation of the current import experiment, not a settled
world/seed/address identity model. Importing two FMG maps into one WorldState
will collide because no world/seed scope is included.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from worldloom.core import derive_entity_id

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


def _anomaly(kind: str, path: str, position: int, value: Any) -> dict[str, Any]:
    return {"kind": kind, "path": path, "position": position, "value": _sanitize_without_anomalies(value)}


def _sanitize_string(value: str) -> tuple[str, list[str]]:
    """Tolerate lone surrogates at the FMG importer boundary only."""
    result: list[str] = []
    labels: list[str] = []
    index = 0
    while index < len(value):
        code = ord(value[index])
        if 0xD800 <= code <= 0xDFFF:
            if (
                0xD800 <= code <= 0xDBFF
                and index + 1 < len(value)
                and 0xDC00 <= ord(value[index + 1]) <= 0xDFFF
            ):
                result.extend((value[index], value[index + 1]))
                index += 2
                continue
            result.append("\ufffd")
            labels.append(f"U+{code:04X}")
        else:
            result.append(value[index])
        index += 1
    return "".join(result), labels


def _sanitize_without_anomalies(value: Any) -> Any:
    """Sanitize a copied value without recording anomalies for the copy."""
    return _sanitize_strings(value, "", -1, [])


def _sanitize_strings(
    path: str,
    position: int,
    anomalies: list[dict[str, Any]],
) -> Any:
    """Recursively sanitize strings; this does not define core string validity."""
    if isinstance(value, str):
        sanitized, labels = _sanitize_string(value)
        if labels:
            anomalies.append(_anomaly("lone-surrogate", path, position, labels))
        return sanitized
    if isinstance(value, list):
        return [
            _sanitize_strings(item, f"{path}[{index}]", position, anomalies)
            for index, item in enumerate(value)
        ]
    if isinstance(value, dict):
        sanitized_dict: dict[Any, Any] = {}
        for key, item in value.items():
            key_path = f"{path}.{{key}}"
            if isinstance(key, str):
                sanitized_key, labels = _sanitize_string(key)
                if labels:
                    anomalies.append(_anomaly("lone-surrogate", key_path, position, labels))
                key = sanitized_key
            if key in sanitized_dict:
                raise ValueError(f"Sanitized dict key collision at {path}: {key!r}")
            sanitized_dict[key] = _sanitize_strings(
                item, f"{path}.{key}", position, anomalies
            )
        return sanitized_dict
    return value


def build_entities(data: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Build all entities, refs, and entity-report data before any writes."""
    id_maps: dict[str, dict[int, str]] = {c: {} for c in COLLECTION_SPECS}
    derived_ids: set[str] = set()
    anomalies: list[dict[str, Any]] = []

    # First pass: derive every ID map before constructing any entity.
    for collection, kind in COLLECTION_SPECS.items():
        for position, record in enumerate(_records(data, collection)):
            if _placeholder(collection, position, record):
                continue
            path = f"pack.{collection}[{position}].i"
            if not isinstance(record, dict):
                anomalies.append(_anomaly("invalid-type", f"pack.{collection}[{position}]", position, record))
                continue
            fmgi = record.get("i")
            if not isinstance(fmgi, int) or isinstance(fmgi, bool):
                anomalies.append(_anomaly("invalid-type", path, position, fmgi))
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

    entities: dict[str, dict[str, Any]] = {}
    dropped: dict[str, dict[str, int]] = {c: {} for c in COLLECTION_SPECS}

    def resolve_one(
        collection: str,
        position: int,
        value: Any,
        target: str,
        mesh: bool,
        path: str,
    ) -> Any | None:
        if not isinstance(value, int) or isinstance(value, bool):
            anomalies.append(_anomaly("invalid-type", path, position, value))
            return None
        if value == -1:
            anomalies.append(_anomaly("sentinel", path, position, value))
            return None
        if mesh:
            cell_count = len(_records(data, "cells"))
            if value < 0 or value >= cell_count:
                anomalies.append(_anomaly("out-of-range", path, position, value))
                return None
            return {"space": target, "index": value}
        if value in id_maps[target]:
            return id_maps[target][value]
        target_records = _records(data, target)
        if 0 <= value < len(target_records) and _placeholder(target, value, target_records[value]):
            anomalies.append(_anomaly("placeholder-reference", path, position, value))
        else:
            anomalies.append(_anomaly("unresolved-reference", path, position, value))
        return None

    def resolve(
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
                item_resolved = resolve_one(
                    collection, position, item, target, mesh, f"{path}[{index}]"
                )
                if item_resolved is not None:
                    resolved.append(item_resolved)
            # Partially resolved lists omit unresolved members; the raw list stays in attributes.
            return resolved if resolved else None
        return resolve_one(collection, position, value, target, mesh, path)

    def resolve_route_points(position: int, value: Any) -> list[dict[str, Any]] | None:
        path = f"pack.routes[{position}].points"
        if not isinstance(value, list):
            anomalies.append(_anomaly("invalid-type", path, position, value))
            return None
        resolved: list[dict[str, Any]] = []
        for index, point in enumerate(value):
            point_path = f"{path}[{index}]"
            if not isinstance(point, list) or len(point) != 3:
                anomalies.append(_anomaly("invalid-type", point_path, position, point))
                continue
            cell = point[2]
            if not isinstance(cell, int) or isinstance(cell, bool):
                anomalies.append(_anomaly("invalid-type", f"{point_path}[2]", position, cell))
                continue
            if cell == -1:
                anomalies.append(_anomaly("sentinel", f"{point_path}[2]", position, cell))
                continue
            cell_count = len(_records(data, "cells"))
            if cell < 0 or cell >= cell_count:
                anomalies.append(_anomaly("out-of-range", f"{point_path}[2]", position, cell))
                continue
            resolved.append({"space": "pack.cells", "index": cell})
        return resolved if resolved else None

    for collection, kind in COLLECTION_SPECS.items():
        excluded = EXCLUDED_KEYS[collection]
        for position, record in enumerate(_records(data, collection)):
            if _placeholder(collection, position, record):
                continue
            if not isinstance(record, dict) or not isinstance(record.get("i"), int) or isinstance(record.get("i"), bool):
                continue
            attributes = _sanitize_strings(
                deepcopy(record), f"pack.{collection}[{position}]", position, anomalies
            )
            for key in excluded:
                if key in attributes:
                    attributes.pop(key)
                    dropped[collection][key] = dropped[collection].get(key, 0) + 1
            refs: dict[str, Any] = {}
            for field, (target, mesh) in REFERENCE_SPECS.get(collection, {}).items():
                if field in record:
                    resolved = resolve(collection, position, field, record[field], target, mesh)
                    if resolved is not None:
                        refs[field] = resolved
            if collection == "routes" and "points" in record:
                resolved = resolve_route_points(position, record["points"])
                if resolved is not None:
                    refs["cells"] = resolved
            entity_id = id_maps[collection][record["i"]]
            if entity_id in entities:
                raise ValueError(f"Derived entity ID collision: {entity_id}")
            entities[entity_id] = {
                "fmg": {"collection": collection, "id": record["i"], "position": position},
                "attributes": attributes,
                "refs": refs,
            }

    counts: dict[str, dict[str, int]] = {}
    for item in anomalies:
        counts.setdefault(item["kind"], {})
        path_counts = counts[item["kind"]]
        path_counts[item["path"]] = path_counts.get(item["path"], 0) + 1
    ordered = sorted(
        anomalies,
        key=lambda item: (
            item["path"],
            item["position"],
            item["kind"],
            repr(item["value"]),
        ),
    )
    report = {
        "entity_counts": {
            c: sum(
                isinstance(r, dict)
                and isinstance(r.get("i"), int)
                and not isinstance(r.get("i"), bool)
                for r in _records(data, c)
            )
            for c in COLLECTION_SPECS
        },
        "dropped_keys": dropped,
        "anomalies": {"counts": counts, "examples": ordered[:20], "total": len(ordered)},
    }
    return entities, report
