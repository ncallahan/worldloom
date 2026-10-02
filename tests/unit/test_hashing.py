from __future__ import annotations

import pytest

from worldloom.core import WorldState
from worldloom.core.hashing import fingerprint, normalise_for_hash


# Verified independently against the pre-extraction WorldState.fingerprint implementation
# at commit a51d582b2c6a5746cdaa0942a2ea9f133c06d0a6.
def test_golden_fingerprints_are_stable_after_hashing_extraction():
    cases = {
        "nested": {
            "a": 1,
            "b": [2, 3],
            "c": {"x": "hello", "y": None},
        },
        "unordered_mapping": {"b": 2, "a": 1},
        "mixed": {
            "nested": {"z": [3, 2, 1], "a": True},
            "tuple": (1, 2),
        },
    }

    expected = {
        "nested": "b507dcccc1cdab6221f71965e211136872bdabd36da6fc43fce6d38ae84781bb",
        "unordered_mapping": "cda25b5537fd16060f51eb839e5891c35559f199e9b4bd755b916dd61da60d71",
        "mixed": "8f3d958139f946af833ccb39e7fcf40fba664993e72558d1c2fecdb5d12c5525",
    }

    assert {name: fingerprint(value) for name, value in cases.items()} == expected
    assert {name: WorldState.fingerprint(value) for name, value in cases.items()} == expected


def test_hashing_refactor_preserves_unsupported_value_type_error():
    with pytest.raises(TypeError, match="Unsupported value type for fingerprinting: object"):
        fingerprint(object())
    with pytest.raises(TypeError, match="Unsupported value type for fingerprinting: object"):
        WorldState.fingerprint(object())


def test_normalisation_remains_order_independent():
    assert normalise_for_hash({"b": 2, "a": 1}) == normalise_for_hash({"a": 1, "b": 2})
