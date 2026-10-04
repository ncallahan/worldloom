"""This module provides provisional minimal persistence, not the eventual world-file format; no format marker or version."""

from __future__ import annotations

import json
import math
from typing import Any, Callable

from .address import Address
from .events import Event
from .provenance import Provenance
from .spatial import SpatialGrid
from .state import WorldSnapshot, WorldState

_TAG_TUPLE = "$tuple"
_TAG_SET = "$set"
_TAG_DICT = "$dict"
_TAG_ADDRESS = "$address"
_TAGS = {_TAG_TUPLE, _TAG_SET, _TAG_DICT, _TAG_ADDRESS}
_TOP_LEVEL = {
    "fields",
    "entities",
    "events",
    "observations",
    "provenance",
    "metadata",
    "spatial_fields",
    "overlays",
    "overlay_priorities",
    "overlay_provenance",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _encode_mapping(
    value: dict[Any, Any], value_encoder: Callable[[Any], Any]
) -> dict[str, Any]:
    if all(type(key) is str and not key.startswith("$") for key in value):
        return {key: value_encoder(value[key]) for key in sorted(value)}
    pairs = [[_encode(key), value_encoder(item)] for key, item in value.items()]
    pairs.sort(key=lambda pair: _canonical_json(pair[0]))
    return {_TAG_DICT: pairs}


def _encode(value: Any) -> Any:
    value_type = type(value)
    if value is None or value_type in {str, int, bool}:
        return value
    if value_type is float:
        if not math.isfinite(value):
            raise TypeError("Non-finite floats are not supported")
        return value
    if value_type is Address:
        return {_TAG_ADDRESS: value.canonical}
    if value_type is list:
        return [_encode(item) for item in value]
    if value_type is tuple:
        return {_TAG_TUPLE: [_encode(item) for item in value]}
    if value_type is set:
        items = [_encode(item) for item in value]
        items.sort(key=_canonical_json)
        return {_TAG_SET: items}
    if value_type is dict:
        return _encode_mapping(value, _encode)
    raise TypeError(f"Unsupported value type: {value_type.__name__}")


def _decode(value: Any) -> Any:
    value_type = type(value)
    if value_type is float:
        if not math.isfinite(value):
            raise ValueError("Non-finite floats are not supported")
        return value
    if value_type is list:
        return [_decode(item) for item in value]
    if value_type is not dict:
        return value

    dollars = [
        key for key in value if type(key) is str and key.startswith("$")
    ]
    if dollars:
        if len(value) != 1:
            raise ValueError("Tagged object must contain exactly one key")
        tag = next(iter(value))
        if tag not in _TAGS:
            raise ValueError(f"Unknown tag: {tag}")
        payload = value[tag]
        if tag in {_TAG_TUPLE, _TAG_SET}:
            if type(payload) is not list:
                raise ValueError(f"{tag} payload must be a list")
            decoded = [_decode(item) for item in payload]
            if tag == _TAG_TUPLE:
                return tuple(decoded)
            result = set()
            for item in decoded:
                try:
                    result.add(item)
                except TypeError as exc:
                    raise ValueError("Unhashable set element") from exc
            if len(result) != len(decoded):
                raise ValueError("Duplicate set element")
            return result
        if tag == _TAG_ADDRESS:
            if type(payload) is not str:
                raise ValueError("$address payload must be a string")
            try:
                return Address.parse(payload)
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid address") from exc
        return _decode_dict_pairs(payload)

    return {key: _decode(item) for key, item in value.items()}


def _decode_dict_pairs(pairs: Any) -> dict[Any, Any]:
    if type(pairs) is not list:
        raise ValueError("$dict payload must be a list")
    result = {}
    for pair in pairs:
        if type(pair) is not list or len(pair) != 2:
            raise ValueError("$dict entries must be 2-element lists")
        key = _decode(pair[0])
        item = _decode(pair[1])
        try:
            hash(key)
        except TypeError as exc:
            raise ValueError("Unhashable dictionary key") from exc
        if key in result:
            raise ValueError("Duplicate decoded dictionary key")
        result[key] = item
    return result


def _decode_mapping(
    value: Any, value_decoder: Callable[[Any], Any]
) -> dict[Any, Any]:
    if type(value) is not dict:
        raise ValueError("Mapping must be an object or $dict")
    if any(type(key) is str and key.startswith("$") for key in value):
        if set(value) != {_TAG_DICT}:
            raise ValueError("Invalid tagged mapping")
        return _decode_mapping_pairs(value[_TAG_DICT], value_decoder)
    return {key: value_decoder(item) for key, item in value.items()}


def _decode_mapping_pairs(
    pairs: Any, value_decoder: Callable[[Any], Any]
) -> dict[Any, Any]:
    if type(pairs) is not list:
        raise ValueError("$dict payload must be a list")
    result = {}
    for pair in pairs:
        if type(pair) is not list or len(pair) != 2:
            raise ValueError("$dict entries must be 2-element lists")
        key = _decode(pair[0])
        item = value_decoder(pair[1])
        try:
            hash(key)
        except TypeError as exc:
            raise ValueError("Unhashable dictionary key") from exc
        if key in result:
            raise ValueError("Duplicate decoded dictionary key")
        result[key] = item
    return result


def _validate_event(value: Any, error_type: type[Exception]) -> None:
    if type(value) is not Event:
        raise error_type("Invalid Event")
    if type(value.kind) is not str or type(value.data) is not dict:
        raise error_type("Invalid Event fields")
    if type(value.time) not in {int, float} or type(value.time) is bool:
        raise error_type("Invalid Event time")


def _validate_provenance(value: Any, error_type: type[Exception]) -> None:
    if type(value) is not Provenance:
        raise error_type("Invalid Provenance")
    if type(value.producer) is not str or type(value.inputs) is not tuple:
        raise error_type("Invalid Provenance fields")
    if type(value.configuration) is not dict:
        raise error_type("Invalid Provenance configuration")
    if type(value.time) not in {int, float} or type(value.time) is bool:
        raise error_type("Invalid Provenance time")
    if value.fingerprint is not None and type(value.fingerprint) is not str:
        raise error_type("Invalid Provenance fingerprint")


def _validate_spatial(value: Any, error_type: type[Exception]) -> None:
    if type(value) is not SpatialGrid:
        raise error_type("Invalid SpatialGrid")
    if type(value.shape) is not tuple or type(value.transform) is not tuple:
        raise error_type("Invalid SpatialGrid tuple member")
    if type(value.crs) not in {str, type(None)}:
        raise error_type("Invalid SpatialGrid crs")


def _encode_event(event: Event) -> dict[str, Any]:
    _validate_event(event, TypeError)
    return {
        "kind": _encode(event.kind),
        "time": _encode(event.time),
        "data": _encode(event.data),
    }


def _decode_event(value: Any) -> Event:
    if type(value) is not dict or set(value) != {"kind", "time", "data"}:
        raise ValueError("Invalid Event object")
    kind = _decode(value["kind"])
    time = _decode(value["time"])
    data = _decode(value["data"])
    event = Event(kind, time, data)
    _validate_event(event, ValueError)
    return event


def _encode_provenance(value: Provenance) -> dict[str, Any]:
    _validate_provenance(value, TypeError)
    return {
        "producer": _encode(value.producer),
        "inputs": _encode(value.inputs),
        "configuration": _encode(value.configuration),
        "time": _encode(value.time),
        "fingerprint": _encode(value.fingerprint),
    }


def _decode_provenance(value: Any) -> Provenance:
    expected = {
        "producer",
        "inputs",
        "configuration",
        "time",
        "fingerprint",
    }
    if type(value) is not dict or set(value) != expected:
        raise ValueError("Invalid Provenance object")
    producer = _decode(value["producer"])
    inputs = _decode(value["inputs"])
    configuration = _decode(value["configuration"])
    time = _decode(value["time"])
    stored_fingerprint = _decode(value["fingerprint"])
    provenance = Provenance(
        producer,
        inputs,
        configuration,
        time,
        stored_fingerprint,
    )
    _validate_provenance(provenance, ValueError)
    return provenance


def _encode_spatial(value: SpatialGrid) -> dict[str, Any]:
    _validate_spatial(value, TypeError)
    return {
        "shape": _encode(value.shape),
        "crs": _encode(value.crs),
        "transform": _encode(value.transform),
    }


def _decode_spatial(value: Any) -> SpatialGrid:
    expected = {"shape", "crs", "transform"}
    if type(value) is not dict or set(value) != expected:
        raise ValueError("Invalid SpatialGrid object")
    shape = _decode(value["shape"])
    crs = _decode(value["crs"])
    transform = _decode(value["transform"])
    try:
        spatial = SpatialGrid(shape, crs, transform)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid SpatialGrid value") from exc
    _validate_spatial(spatial, ValueError)
    return spatial


def encode_snapshot(snapshot: WorldSnapshot) -> dict:
    if type(snapshot) is not WorldSnapshot:
        raise TypeError("Expected WorldSnapshot")
    return {
        "fields": _encode(snapshot.fields),
        "entities": _encode(snapshot.entities),
        "events": [_encode_event(event) for event in snapshot.events],
        "observations": _encode(snapshot.observations),
        "provenance": _encode_mapping(
            snapshot.provenance,
            _encode_provenance,
        ),
        "metadata": _encode(snapshot.metadata),
        "spatial_fields": _encode_mapping(
            snapshot.spatial_fields,
            _encode_spatial,
        ),
        "overlays": _encode(snapshot.overlays),
        "overlay_priorities": _encode(snapshot.overlay_priorities),
        "overlay_provenance": _encode_mapping(
            snapshot.overlay_provenance,
            lambda layers: _encode_mapping(
                layers,
                lambda values: _encode_mapping(
                    values,
                    _encode_provenance,
                ),
            ),
        ),
    }


def decode_snapshot(data) -> WorldSnapshot:
    if type(data) is not dict or set(data) != _TOP_LEVEL:
        raise ValueError("Snapshot has missing or unknown top-level keys")

    fields = _decode(data["fields"])
    entities = _decode(data["entities"])
    events_data = data["events"]
    observations = _decode(data["observations"])
    provenance = _decode_mapping(
        data["provenance"],
        _decode_provenance,
    )
    metadata = _decode(data["metadata"])
    spatial_fields = _decode_mapping(
        data["spatial_fields"],
        _decode_spatial,
    )
    overlays = _decode(data["overlays"])
    overlay_priorities = _decode(data["overlay_priorities"])
    overlay_provenance = _decode_mapping(
        data["overlay_provenance"],
        lambda layers: _decode_mapping(
            layers,
            lambda values: _decode_mapping(
                values,
                _decode_provenance,
            ),
        ),
    )

    if (
        type(fields) is not dict
        or type(entities) is not dict
        or type(events_data) is not list
        or type(observations) is not dict
        or type(provenance) is not dict
        or type(metadata) is not dict
        or type(spatial_fields) is not dict
        or type(overlays) is not dict
        or type(overlay_priorities) is not dict
        or type(overlay_provenance) is not dict
    ):
        raise ValueError("Invalid snapshot member type")

    if any(type(key) is not str for key in provenance):
        raise ValueError("Invalid provenance name")
    if any(type(key) is not str for key in spatial_fields):
        raise ValueError("Invalid spatial field name")
    if any(type(key) is not str for key in overlay_provenance):
        raise ValueError("Invalid overlay provenance name")

    events = [_decode_event(event) for event in events_data]
    return WorldSnapshot(
        fields,
        entities,
        events,
        observations,
        provenance,
        metadata,
        spatial_fields,
        overlays,
        overlay_priorities,
        overlay_provenance,
    )


def dumps_snapshot(snapshot: WorldSnapshot) -> str:
    return json.dumps(
        encode_snapshot(snapshot),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _reject_constant(value: str):
    raise ValueError(f"Invalid JSON constant: {value}")


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def loads_snapshot(text: str) -> WorldSnapshot:
    try:
        data = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError("Invalid JSON") from exc
    return decode_snapshot(data)


def save_world(
    world: WorldState,
    path,
    metadata: dict | None = None,
) -> None:
    text = dumps_snapshot(world.snapshot(metadata))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def load_snapshot(path) -> WorldSnapshot:
    with open(path, "r", encoding="utf-8") as handle:
        return loads_snapshot(handle.read())


def load_world(path) -> WorldState:
    world = WorldState()
    world.restore(load_snapshot(path))
    return world
