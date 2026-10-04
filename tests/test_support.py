"""Shared test fixtures and strict equality helpers."""

import math
from typing import Any

from worldloom.core import Address, Event, Provenance, SpatialGrid, WorldSnapshot


SETTLEMENT_IDENTITY = (
    "question:settlement.founding",
    "role:founding",
    "slot:001",
)


def _token(value: Any):
    if type(value) is tuple:
        return ("tuple", tuple(_token(item) for item in value))
    if type(value) is Address:
        return ("address", value.segments)
    if type(value) is dict:
        return (
            "dict",
            tuple(
                sorted(
                    (_token(key), _token(item))
                    for key, item in value.items()
                )
            ),
        )
    if type(value) is set:
        return ("set", tuple(sorted(_token(item) for item in value)))
    return (type(value).__name__, value)


def strict_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if left is None or type(left) in {str, int, bool}:
        return left == right
    if type(left) is float:
        return (
            left == right
            and math.copysign(1.0, left) == math.copysign(1.0, right)
        )
    if type(left) in {list, tuple}:
        return len(left) == len(right) and all(
            strict_equal(a, b) for a, b in zip(left, right)
        )
    if type(left) is dict:
        if len(left) != len(right):
            return False
        left_by_token = {
            _token(key): value for key, value in left.items()
        }
        right_by_token = {
            _token(key): value for key, value in right.items()
        }
        return left_by_token.keys() == right_by_token.keys() and all(
            strict_equal(left_by_token[key], right_by_token[key])
            for key in left_by_token
        )
    if type(left) is set:
        return {_token(item) for item in left} == {
            _token(item) for item in right
        }
    if type(left) is Address:
        return left.segments == right.segments
    if type(left) is Event:
        return (
            strict_equal(left.kind, right.kind)
            and strict_equal(left.time, right.time)
            and strict_equal(left.data, right.data)
        )
    if type(left) is Provenance:
        return (
            strict_equal(left.producer, right.producer)
            and strict_equal(left.inputs, right.inputs)
            and strict_equal(left.configuration, right.configuration)
            and strict_equal(left.time, right.time)
            and strict_equal(left.fingerprint, right.fingerprint)
        )
    if type(left) is SpatialGrid:
        return (
            strict_equal(left.shape, right.shape)
            and strict_equal(left.crs, right.crs)
            and strict_equal(left.transform, right.transform)
        )
    if type(left) is WorldSnapshot:
        return all(
            strict_equal(getattr(left, name), getattr(right, name))
            for name in (
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
            )
        )
    raise TypeError(f"Unsupported strict comparison type: {type(left).__name__}")
