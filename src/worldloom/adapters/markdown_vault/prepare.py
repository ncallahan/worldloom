"""Tolerant, deterministic preparation for the Markdown-vault projection."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import is_dataclass, replace
from types import SimpleNamespace
from typing import Any

from worldloom.core import Address, WorldState
from worldloom.adapters.markdown_vault.naming import is_standard_id

_SURROGATE_RE = re.compile("[\\ud800-\\udfff]")


class PreparedProjection:
    """Prepared read-only projection view and exact anomaly counts."""

    def __init__(self, view: WorldState, anomalies: dict[str, dict[str, int]]):
        self.view = view
        self.anomalies = anomalies


def _record(anomalies: dict[str, dict[str, int]], kind: str, path: str) -> None:
    counts = anomalies.setdefault(kind, {})
    counts[path] = counts.get(path, 0) + 1


def _clean_string(value: str, path: str, anomalies: dict[str, dict[str, int]]) -> str:
    if value.isascii() or _SURROGATE_RE.search(value) is None:
        return value
    _record(anomalies, "lone-surrogate", path)
    return _SURROGATE_RE.sub("\ufffd", value)


def _clean_key(value: str, path: str, anomalies: dict[str, dict[str, int]]) -> str:
    if value.isascii() or _SURROGATE_RE.search(value) is None:
        return value
    safe_key = _SURROGATE_RE.sub("\ufffd", value)
    _record(anomalies, "lone-surrogate", f"{path}.{safe_key}")
    return safe_key


def _safe_key_label(key: Any) -> str:
    if isinstance(key, str):
        return key
    if isinstance(key, Address):
        return key.canonical
    if key is None or isinstance(key, (bool, int, float, tuple)):
        try:
            value = list(key) if isinstance(key, tuple) else key
            return json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError):
            return "<nonstandard-key>"
    return f"<{type(key).__module__}.{type(key).__qualname__}>"


def _child_path(path: str, key: Any) -> str:
    return f"{path}.{_safe_key_label(key)}"


def _unique_key(key: Any, used: set[Any], reserved: set[Any], path: str,
                anomalies: dict[str, dict[str, int]]) -> Any:
    if key not in used:
        return key
    _record(anomalies, "key-collision", path)
    suffix = 2
    while f"{key} (duplicate {suffix})" in used or f"{key} (duplicate {suffix})" in reserved:
        suffix += 1
    return f"{key} (duplicate {suffix})"


def _sanitize_tree(value: Any, path: str,
                   anomalies: dict[str, dict[str, int]]) -> Any:
    if isinstance(value, str):
        return _clean_string(value, path, anomalies)
    if isinstance(value, Mapping):
        cleaned = [
            (_clean_key(key, path, anomalies) if isinstance(key, str) else key, item)
            for key, item in value.items()
        ]
        reserved = {key for key, _ in cleaned}
        result: dict[Any, Any] = {}
        used: set[Any] = set()
        for key, item in cleaned:
            clean_key = _unique_key(key, used, reserved, path, anomalies)
            used.add(clean_key)
            result[clean_key] = _sanitize_tree(item, _child_path(path, clean_key), anomalies)
        return result
    if isinstance(value, list):
        return [_sanitize_tree(item, f"{path}[{index}]", anomalies) for index, item in enumerate(value)]
    if isinstance(value, tuple):
        return tuple(_sanitize_tree(item, f"{path}[{index}]", anomalies) for index, item in enumerate(value))
    return value


def _json_safe(value: Any) -> bool:
    try:
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False, sort_keys=True)
        return True
    except (TypeError, ValueError, UnicodeError):
        return False


def _type_placeholder(value: Any) -> str:
    cls = type(value)
    return f"<{cls.__module__}.{cls.__qualname__}>"


def _sort_token(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False, sort_keys=True)
    except (TypeError, ValueError, UnicodeError):
        if isinstance(value, Address):
            return value.canonical
        return _type_placeholder(value)


def _key_text(key: Any, path: str, anomalies: dict[str, dict[str, int]]) -> str:
    if isinstance(key, Address):
        return key.canonical
    if isinstance(key, tuple):
        try:
            text = json.dumps(list(key), ensure_ascii=True, separators=(",", ":"), allow_nan=False, sort_keys=True)
            return text
        except (TypeError, ValueError, UnicodeError):
            _record(anomalies, "nonserialisable-value", path)
            return _type_placeholder(key)
    if key is None or isinstance(key, (bool, int)):
        return json.dumps(key, ensure_ascii=True, allow_nan=False)
    if isinstance(key, float):
        if math.isfinite(key):
            return json.dumps(key, ensure_ascii=True, allow_nan=False)
        _record(anomalies, "nonserialisable-value", path)
        return "NaN" if math.isnan(key) else ("Infinity" if key > 0 else "-Infinity")
    _record(anomalies, "nonserialisable-value", path)
    return _type_placeholder(key)


def _coerce_dict(value: dict[Any, Any], path: str,
                 anomalies: dict[str, dict[str, int]]) -> dict[str, Any]:
    entries = [
        (key if isinstance(key, str) else _key_text(key, path, anomalies), item)
        for key, item in value.items()
    ]
    reserved = {key for key, _ in entries}
    result: dict[str, Any] = {}
    used: set[str] = set()
    for text_key, item in entries:
        unique_key = _unique_key(text_key, used, reserved, path, anomalies)
        used.add(unique_key)
        result[unique_key] = _prepare_value(item, _child_path(path, unique_key), anomalies)
    return result


def _coerce_value(value: Any, path: str,
                  anomalies: dict[str, dict[str, int]]) -> Any:
    if isinstance(value, (set, frozenset)):
        _record(anomalies, "coerced-value", path)
        prepared = [_prepare_value(item, f"{path}[{index}]", anomalies)
                    for index, item in enumerate(sorted(value, key=_sort_token))]
        return sorted(prepared, key=_sort_token)
    if isinstance(value, (bytes, bytearray)):
        _record(anomalies, "coerced-value", path)
        return "bytes:" + bytes(value).hex()
    if isinstance(value, Address):
        _record(anomalies, "coerced-value", path)
        return value.canonical
    if isinstance(value, float) and not math.isfinite(value):
        _record(anomalies, "nonserialisable-value", path)
        return "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            _record(anomalies, "coerced-value", path)
            return _coerce_dict(value, path, anomalies)
        return {key: _prepare_value(item, _child_path(path, key), anomalies)
                for key, item in value.items()}
    if isinstance(value, list):
        return [_prepare_value(item, f"{path}[{index}]", anomalies) for index, item in enumerate(value)]
    if isinstance(value, tuple):
        return tuple(_prepare_value(item, f"{path}[{index}]", anomalies) for index, item in enumerate(value))
    _record(anomalies, "nonserialisable-value", path)
    return _type_placeholder(value)


def _prepare_value(value: Any, path: str,
                   anomalies: dict[str, dict[str, int]]) -> Any:
    clean = _sanitize_tree(value, path, anomalies)
    if _json_safe(clean):
        return clean
    return _coerce_value(clean, path, anomalies)


def _normalise_id(entity_id: str, anomalies: dict[str, dict[str, int]], path: str, original_id: str | None = None) -> str:
    clean = _clean_string(entity_id, path, anomalies)
    if is_standard_id(clean):
        return clean
    _record(anomalies, "nonstandard-id", path)
    raw_kind = clean.split(":", 1)[0] if ":" in clean else "entity"
    kind = "".join(char if char.isascii() and (char.isalnum() or char in "_-") else "_" for char in raw_kind)[:40]
    kind = kind or "entity"
    digest_source = entity_id if original_id is None else original_id
    digest = hashlib.sha256(digest_source.encode("utf-8", "surrogatepass")).hexdigest()[:12]
    return f"{kind}:{digest}"


def _rewrite_refs(value: Any, ids: dict[str, str]) -> Any:
    if isinstance(value, str):
        return ids.get(value, value)
    if isinstance(value, list):
        return [_rewrite_refs(item, ids) for item in value]
    if isinstance(value, tuple):
        return tuple(_rewrite_refs(item, ids) for item in value)
    if isinstance(value, dict):
        return {key: _rewrite_refs(item, ids) for key, item in value.items()}
    return value


def _prepare_entity(entity: Any, index: int, entity_id: str,
                    id_map: dict[str, str], anomalies: dict[str, dict[str, int]]) -> dict[str, Any]:
    path = f"entities[{index}]"
    if not isinstance(entity, Mapping):
        _record(anomalies, "nonstandard-entity-shape", path)
        return {"attributes": {"value": _prepare_value(entity, f"{path}.attributes.value", anomalies)}, "refs": {}}
    result = dict(entity)
    if "attributes" not in result:
        result["attributes"] = {}
    elif not isinstance(result["attributes"], Mapping):
        _record(anomalies, "nonstandard-entity-shape", f"{path}.attributes")
        result["attributes"] = {"value": _prepare_value(result["attributes"], f"{path}.attributes.value", anomalies)}
    else:
        result["attributes"] = _prepare_value(result["attributes"], f"{path}.attributes", anomalies)
    if "refs" not in result:
        result["refs"] = {}
    elif not isinstance(result["refs"], Mapping):
        _record(anomalies, "nonstandard-entity-shape", f"{path}.refs")
        result["refs"] = {}
    else:
        refs = _prepare_value(result["refs"], f"{path}.refs", anomalies)
        result["refs"] = _rewrite_refs(refs, id_map)
    if "fmg" in result:
        if not isinstance(result["fmg"], Mapping):
            _record(anomalies, "nonstandard-entity-shape", f"{path}.fmg")
        result["fmg"] = _prepare_value(result["fmg"], f"{path}.fmg", anomalies)
    extra_items = [(key, item) for key, item in result.items()
                   if key not in {"attributes", "refs", "fmg"}]
    cleaned_items = []
    for key, item in extra_items:
        if isinstance(key, str):
            clean_key = _clean_key(key, path, anomalies)
        else:
            clean_key = _key_text(key, _child_path(path, key), anomalies)
        cleaned_items.append((clean_key, item))
    reserved = {"attributes", "refs", "fmg"} | {key for key, _ in cleaned_items}
    used: set[str] = {"attributes", "refs"} | ({"fmg"} if "fmg" in result else set())
    extras: dict[str, Any] = {}
    for key, item in cleaned_items:
        key_path = f"{path}.{key}"
        unique_key = _unique_key(key, used, reserved, key_path, anomalies)
        used.add(unique_key)
        extras[unique_key] = _prepare_value(item, key_path, anomalies)
    result = {key: item for key, item in result.items()
              if key in {"attributes", "refs", "fmg"}}
    result.update(extras)
    return result


def _prepare_provenance(value: Any, index: int,
                        anomalies: dict[str, dict[str, int]]) -> Any:
    path = f"provenance[{index}]"
    fallback = _type_placeholder(value)
    try:
        raw_producer = value.producer
    except Exception:
        _record(anomalies, "nonserialisable-value", f"{path}.producer")
        producer = fallback
    else:
        producer = _prepare_value(raw_producer, f"{path}.producer", anomalies)

    try:
        raw_inputs = value.inputs
    except Exception:
        _record(anomalies, "nonserialisable-value", f"{path}.inputs")
        inputs = (fallback,)
    else:
        inputs = _prepare_value(raw_inputs, f"{path}.inputs", anomalies)
        if not isinstance(inputs, (list, tuple)):
            if _json_safe(raw_inputs):
                _record(anomalies, "nonserialisable-value", f"{path}.inputs")
            inputs = (_type_placeholder(raw_inputs),)

    try:
        raw_configuration = value.configuration
    except Exception:
        _record(anomalies, "nonserialisable-value", f"{path}.configuration")
        configuration = {}
    else:
        configuration = _prepare_value(raw_configuration, f"{path}.configuration", anomalies)
        if not isinstance(configuration, Mapping):
            if _json_safe(raw_configuration):
                _record(anomalies, "nonserialisable-value", f"{path}.configuration")
            configuration = {}

    if is_dataclass(value):
        try:
            return replace(value, producer=producer, inputs=inputs, configuration=configuration)
        except Exception:
            pass
    return SimpleNamespace(producer=producer, inputs=inputs, configuration=configuration)


def prepare_projection_input(world: WorldState) -> PreparedProjection:
    """Build a sanitized projection view without mutating canonical WorldState."""
    anomalies: dict[str, dict[str, int]] = {}
    source_items = list(world.entities.items())
    id_map: dict[str, str] = {}
    prepared_ids: list[str] = []
    seen_clean: set[str] = set()
    seen_prepared: set[str] = set()
    for index, (entity_id, _) in enumerate(source_items):
        if not isinstance(entity_id, str):
            raise ValueError(f"Entity ID must be a string: {entity_id!r}")
        clean_id = _clean_string(entity_id, f"entities[{index}].id", anomalies)
        if clean_id in seen_clean:
            raise ValueError(f"Sanitized entity ID collision: {clean_id}")
        seen_clean.add(clean_id)
        prepared_id = _normalise_id(clean_id, anomalies, f"entities[{index}].id", original_id=entity_id)
        if prepared_id in seen_prepared:
            raise ValueError(f"Sanitized entity ID collision: {prepared_id}")
        seen_prepared.add(prepared_id)
        prepared_ids.append(prepared_id)
        id_map[clean_id] = prepared_id
        id_map[entity_id] = prepared_id

    entities: dict[str, dict[str, Any]] = {}
    for index, ((_, entity), prepared_id) in enumerate(zip(source_items, prepared_ids)):
        entities[prepared_id] = _prepare_entity(entity, index, prepared_id, id_map, anomalies)

    fields: dict[str, Any] = {}
    if "fmg.source" in world.fields:
        fields["fmg.source"] = _prepare_value(world.fields["fmg.source"], "fields['fmg.source']", anomalies)
    observations: dict[str, Any] = {}
    if "fmg.import.report" in world.observations:
        observations["fmg.import.report"] = _prepare_value(
            world.observations["fmg.import.report"], "observations['fmg.import.report']", anomalies
        )

    provenance: dict[str, Any] = {}
    for index, (key, value) in enumerate(world.provenance.items()):
        prepared = _prepare_provenance(value, index, anomalies)
        if isinstance(key, str) and key.startswith("entity:"):
            original_id = key[len("entity:"):]
            new_id = id_map.get(original_id, _clean_string(original_id, f"provenance[{index}].key", anomalies))
            provenance[f"entity:{new_id}"] = prepared
        else:
            provenance[key] = prepared

    return PreparedProjection(
        WorldState(entities=entities, fields=fields, observations=observations, provenance=provenance),
        anomalies,
    )
