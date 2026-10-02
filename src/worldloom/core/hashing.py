"""Canonical normalisation and hashing for deterministic world data.

This module intentionally supports the limited JSON-like data domain used by
WorldState fingerprints. Unsupported objects raise TypeError rather than falling
back to an object's potentially process-dependent repr().
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def normalise_for_hash(value: Any) -> Any:
    """Normalise supported world-data values for deterministic hashing."""
    if isinstance(value, dict):
        entries = [
            [normalise_for_hash(key), normalise_for_hash(item)]
            for key, item in value.items()
        ]
        return sorted(
            entries,
            key=lambda entry: json.dumps(entry[0], sort_keys=True, separators=(",", ":")),
        )
    if isinstance(value, (list, tuple)):
        return [normalise_for_hash(item) for item in value]
    if isinstance(value, set):
        normalised = [normalise_for_hash(item) for item in value]
        return sorted(
            normalised,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"Unsupported value type for fingerprinting: {type(value).__name__}")


def fingerprint(value: Any) -> str:
    """Return a stable SHA-256 digest for supported nested world data."""
    payload = json.dumps(
        normalise_for_hash(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
