"""Read-only provenance traces for saved Worldloom entities."""

from __future__ import annotations

from typing import Any

from worldloom.core.hashing import fingerprint
from worldloom.detail.burg_wards import (
    GENERATOR_ID, LAYERING_KEY, PRIOR_KEY, QUESTION_ID,
)

RENDERERS: dict[str, Any] = {}


def _safe(value: Any) -> Any:
    if isinstance(value, str):
        return value.encode("utf-8", "replace").decode("utf-8")
    if isinstance(value, dict):
        return {_safe(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if value is None or type(value) in (bool, int, float):
        return value
    return f"<unreadable: {type(value).__name__}>"


def _entity_id(value: str) -> str | None:
    prefix, sep, key = value.partition(":")
    return key if sep and prefix == "entity" else None


def _status(world: Any, provenance: Any, input_key: str) -> str:
    entity_id = _entity_id(input_key)
    if entity_id is None or entity_id not in world.entities:
        return "input missing"
    config = getattr(provenance, "configuration", None)
    fingerprints = config.get("input_fingerprints") if isinstance(config, dict) else None
    if not isinstance(fingerprints, dict) or input_key not in fingerprints:
        return "no recorded fingerprint"
    try:
        current = fingerprint(world.entities[entity_id])
    except (TypeError, ValueError, UnicodeError):
        return "fingerprint unavailable"
    recorded = fingerprints[input_key]
    if not isinstance(recorded, str):
        return "no recorded fingerprint"
    return "current" if current == recorded else "stale (input changed since resolution)"


def _event(world: Any, burg_id: str) -> dict[str, Any] | None:
    events = getattr(world, "events", None)
    if not isinstance(events, list):
        return None
    for event in events:
        data = getattr(event, "data", None)
        if (getattr(event, "kind", None) == "local_detail.resolved"
                and isinstance(data, dict) and data.get("entity_id") == burg_id
                and data.get("question_id") == QUESTION_ID):
            return data
    return None


def _recorded(mapping: Any, key: str, nested: str | None = None) -> Any:
    if not isinstance(mapping, dict):
        return None
    value = mapping.get(key)
    return value.get(nested) if nested and isinstance(value, dict) else value


def _ward_view(world: Any, entity_id: str, entity: dict[str, Any],
               provenance: Any) -> dict[str, Any]:
    config = getattr(provenance, "configuration", None)
    config = config if isinstance(config, dict) else {}
    refs = entity.get("refs")
    burg_id = refs.get("burg") if isinstance(refs, dict) else None
    burg = world.entities.get(burg_id) if isinstance(burg_id, str) else None
    attrs = burg.get("attributes") if isinstance(burg, dict) else None
    attrs = attrs if isinstance(attrs, dict) else {}
    prior = _recorded(getattr(world, "observations", None), PRIOR_KEY)
    prior_entry = prior.get(burg_id) if isinstance(prior, dict) and isinstance(burg_id, str) else None
    event = _event(world, burg_id) if isinstance(burg_id, str) else None
    record = event if event is not None else config
    layering = _recorded(getattr(world, "observations", None), LAYERING_KEY)
    state_index = attrs.get("state")
    state_id = next((key for key, value in world.entities.items()
                     if isinstance(value, dict)
                     and isinstance(value.get("fmg"), dict)
                     and value["fmg"].get("collection") == "states"
                     and isinstance(value.get("attributes"), dict)
                     and value["attributes"].get("i") == state_index), None)
    layering_row = layering.get(state_id) if isinstance(layering, dict) and state_id else None
    if layering is None:
        layering_row = "not recorded"
    elif not isinstance(layering, dict):
        layering_row = "unreadable"
    elif layering_row is None:
        layering_row = "not recorded"
    if isinstance(layering_row, dict):
        layering_row = dict(layering_row)
        if layering_row.get("relative_difference") is None:
            layering_row["relative_difference"] = "not computable"
    elif layering is not None:
        layering_row = "unreadable"
    ward_ids = [key for key, value in world.entities.items()
                if isinstance(value, dict) and isinstance(value.get("refs"), dict)
                and value["refs"].get("burg") == burg_id
                and isinstance(value.get("local_detail"), dict)
                and "slot" in value["local_detail"]]
    inputs = getattr(provenance, "inputs", ())
    burg_input = f"entity:{burg_id}" if isinstance(burg_id, str) else ""
    status = _status(world, provenance, burg_input) if burg_input else "input missing"
    return _safe({
        "entity_id": entity_id,
        "producer": getattr(provenance, "producer", None),
        "inputs": list(inputs) if isinstance(inputs, (list, tuple)) else "unreadable",
        "configuration": config,
        "claim": {"burg_id": burg_id, "name": attrs.get("name") if isinstance(attrs.get("name"), str) else None,
                  "current_imported_population": attrs.get("population")},
        "prior": prior_entry if isinstance(prior_entry, dict) else ("not recorded" if prior_entry is None else "unreadable"),
        "prior_claim_comparison": (
            "matches" if isinstance(prior_entry, dict) and prior_entry.get("claim") == attrs.get("population")
            else "differs" if isinstance(prior_entry, dict) else "not recorded"
        ),
        "resolved_draw": {"resolved_total": config.get("resolved_total"),
                          "slot": entity.get("local_detail", {}).get("slot")
                          if isinstance(entity.get("local_detail"), dict) else None,
                          "population": (entity.get("attributes") or {}).get("population")
                          if isinstance(entity.get("attributes"), dict) else None,
                          "wards_currently_present": len(ward_ids)},
        "resolution_record": {"source": "event" if event is not None else "entity provenance",
                              "recorded": event is not None,
                              **{key: record.get(key) for key in (
                                  "producer", "version", "seed", "burg_sigma",
                                  "ward_sigma", "target_ward_size", "max_wards")},
                              "identity_parts": config.get("identity_parts")},
        "burg_input_staleness": status,
        "layering": (layering_row if isinstance(layering_row, dict) else None),
    })


RENDERERS[GENERATOR_ID] = _ward_view


def _provenance(world: Any, key: str) -> Any:
    records = getattr(world, "provenance", None)
    return records.get(key) if isinstance(records, dict) else None


def _generic(world: Any, entity_id: str, visited: set[str]) -> dict[str, Any]:
    key = f"entity:{entity_id}"
    entity = world.entities.get(entity_id)
    provenance = _provenance(world, key)
    if not isinstance(entity, dict):
        return {"entity_id": entity_id, "status": "input missing"}
    if provenance is None:
        return {"entity_id": entity_id, "status": "no provenance recorded"}
    inputs = getattr(provenance, "inputs", ())
    config = getattr(provenance, "configuration", None)
    node = {"entity_id": entity_id, "producer": getattr(provenance, "producer", None),
            "inputs": [] if isinstance(inputs, (tuple, list)) else "unreadable",
            "configuration": _safe(config) if isinstance(config, dict) else "unreadable"}
    for item in inputs if isinstance(inputs, (tuple, list)) else ():
        if not isinstance(item, str):
            node["inputs"].append({"value": _safe(item), "status": "unreadable"})
        elif item.startswith("entity:"):
            child_id = item[len("entity:"):]
            node["inputs"].append({"input": _safe(item), "staleness": _status(world, provenance, item),
                                   "trace": {"status": "cycle detected"} if child_id in visited
                                   else _generic(world, child_id, visited | {child_id})})
        else:
            node["inputs"].append({"input": _safe(item), "recorded_only": True})
    if getattr(provenance, "producer", None) == "worldloom.adapters.fmg":
        fields = getattr(world, "fields", {})
        source = fields.get("fmg.source") if isinstance(fields, dict) else None
        node["imported_source"] = _safe({
            "fmg.source": source if isinstance(source, dict) else None,
            "producer": getattr(provenance, "producer", None),
            "importer_version": config.get("importer_version") if isinstance(config, dict) else None,
        })
    return node


def _import_source(world: Any, entity_id: str) -> dict[str, Any]:
    provenance = _provenance(world, f"entity:{entity_id}")
    config = getattr(provenance, "configuration", None)
    fields = getattr(world, "fields", {})
    source = fields.get("fmg.source") if isinstance(fields, dict) else None
    if getattr(provenance, "producer", None) != "worldloom.adapters.fmg":
        return {"status": "not imported by FMG importer"}
    return _safe({
        "fmg.source": source if isinstance(source, dict) else "not recorded",
        "producer": getattr(provenance, "producer", None),
        "importer_version": config.get("importer_version") if isinstance(config, dict) else "unreadable",
    })


def _burg_layering(world: Any, burg: dict[str, Any]) -> Any:
    attrs = burg.get("attributes")
    if not isinstance(attrs, dict):
        return "unreadable"
    state_index = attrs.get("state")
    state_id = next((key for key, value in world.entities.items()
                     if isinstance(value, dict)
                     and isinstance(value.get("fmg"), dict)
                     and value["fmg"].get("collection") == "states"
                     and isinstance(value.get("attributes"), dict)
                     and value["attributes"].get("i") == state_index), None)
    observations = getattr(world, "observations", {})
    rows = _recorded(observations, LAYERING_KEY)
    if not isinstance(rows, dict):
        return "not recorded" if rows is None else "unreadable"
    row = rows.get(state_id) if state_id else None
    if not isinstance(row, dict):
        return "not recorded"
    result = dict(row)
    if result.get("relative_difference") is None:
        result["relative_difference"] = "not computable"
    return _safe(result)


def build_trace(world: Any, entity_id: str) -> dict[str, Any]:
    """Build a JSON-serialisable trace without modifying or resolving the world."""
    entity = world.entities.get(entity_id)
    if not isinstance(entity, dict):
        raise ValueError(f"unknown entity ID: {entity_id}")
    provenance = _provenance(world, f"entity:{entity_id}")
    renderer = RENDERERS.get(getattr(provenance, "producer", None))
    if provenance is not None and renderer is not None:
        return _safe({"kind": "ward", "ward": renderer(world, entity_id, entity, provenance),
                      "trace": _generic(world, entity_id, {entity_id})})
    result = {"kind": "burg" if isinstance(entity.get("fmg"), dict)
              and entity["fmg"].get("collection") == "burgs" else "entity",
              "trace": _generic(world, entity_id, {entity_id})}
    if result["kind"] == "burg":
        event = _event(world, entity_id)
        observations = getattr(world, "observations", {})
        result["burg"] = _safe({
            "claim": (entity.get("attributes") or {}).get("population")
                     if isinstance(entity.get("attributes"), dict) else None,
            "name": (entity.get("attributes") or {}).get("name")
                    if isinstance(entity.get("attributes"), dict)
                    and isinstance(entity["attributes"].get("name"), str) else None,
            "prior": (
                _recorded(observations, PRIOR_KEY, entity_id)
                if isinstance(_recorded(observations, PRIOR_KEY), dict)
                else ("not recorded" if _recorded(observations, PRIOR_KEY) is None else "unreadable")
            ),
            "resolution_record": event,
            "resolution_status": "recorded" if event is not None else
                "no recorded resolution; reason not recorded",
            "wards_currently_present": [
                key for key, value in world.entities.items()
                if isinstance(value, dict) and isinstance(value.get("refs"), dict)
                and value["refs"].get("burg") == entity_id
                and isinstance(value.get("local_detail"), dict) and "slot" in value["local_detail"]
            ],
            "layering": _burg_layering(world, entity),
            "imported_source": _import_source(world, entity_id),
        })
    return _safe(result)


def format_trace(trace: dict[str, Any]) -> str:
    """Format a trace as deterministic sectioned plain text."""
    lines: list[str] = []
    def walk(value: Any, prefix: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                label = f"{prefix}{key.replace('_', ' ')}"
                if isinstance(child, (dict, list)):
                    lines.append(f"{label.title()}:")
                    walk(child, prefix + "  ")
                else:
                    lines.append(f"{label}: {child}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{prefix}None recorded")
            for item in value:
                if isinstance(item, (dict, list)):
                    walk(item, prefix)
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{value}")
    walk(trace)
    return "\n".join(lines)
