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
}
EXCLUDED_KEYS = {
    "states": {"coa", "military", "campaigns"},
    "provinces": {"coa"},
    "burgs": {"coa", "production"},
    "cultures": set(),
    "religions": set(),
}
REFERENCE_SPECS = {
    "states": {"neighbors": ("states", False), "provinces": ("provinces", False)},
    "provinces": {"state": ("states", False), "center": ("pack.cells", True)},
    "burgs": {"cell": ("pack.cells", True), "state": ("states", False)},
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


def _anomaly(kind: str, path: str, record: int, value: Any) -> dict[str, Any]:
    return {"kind": kind, "path": path, "record": record, "value": value}


def build_entities(data: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Build all entities, refs, and entity-report data before any writes."""
    id_maps: dict[str, dict[int, str]] = {c: {} for c in COLLECTION_SPECS}
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
            if entity_id in id_maps[collection].values():
                raise ValueError(f"Derived entity ID collision: {entity_id}")
            id_maps[collection][fmgi] = entity_id

    entities: dict[str, dict[str, Any]] = {}
    dropped: dict[str, dict[str, int]] = {c: {} for c in COLLECTION_SPECS}

    def resolve_one(collection: str, position: int, field: str, value: Any, target: str, mesh: bool, path: str) -> Any | None:
        if not isinstance(value, int) or isinstance(value, bool):
            anomalies.append(_anomaly("invalid-type", path, position, value))
            return None
        if value == -1:
            anomalies.append(_anomaly("sentinel", path, position, value))
            return None
        if mesh:
            return {"space": target, "index": value}
        if value in id_maps[target]:
            return id_maps[target][value]
        target_records = _records(data, target)
        if 0 <= value < len(target_records) and _placeholder(target, value, target_records[value]):
            anomalies.append(_anomaly("placeholder-reference", path, position, value))
        else:
            anomalies.append(_anomaly("unresolved-reference", path, position, value))
        return None

    def resolve(collection: str, position: int, field: str, value: Any, target: str, mesh: bool) -> Any | None:
        path = f"pack.{collection}[{position}].{field}"
        if isinstance(value, list):
            resolved = []
            for index, item in enumerate(value):
                item_resolved = resolve_one(collection, position, field, item, target, mesh, f"{path}[{index}]")
                if item_resolved is not None:
                    resolved.append(item_resolved)
            return resolved
        return resolve_one(collection, position, field, value, target, mesh, path)

    for collection, kind in COLLECTION_SPECS.items():
        excluded = EXCLUDED_KEYS[collection]
        for position, record in enumerate(_records(data, collection)):
            if _placeholder(collection, position, record):
                continue
            if not isinstance(record, dict) or not isinstance(record.get("i"), int) or isinstance(record.get("i"), bool):
                continue
            attributes = deepcopy(record)
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
            item["record"] if isinstance(item["record"], int) else -1,
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
