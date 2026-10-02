"""Provisional deterministic entity identities and alias lookup helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .hashing import fingerprint

_ID_SEPARATOR = ":"
_ID_HEX_LENGTH = 12


def derive_entity_id(kind: str, *identity_parts: str) -> str:
    """Derive a stable entity ID from the identity question being resolved.

    The selected answer (for example, a chosen location) must not be included
    in ``identity_parts``. Entity IDs identify the question/slot being resolved,
    while mutable or derived answers remain entity attributes.
    """
    if not isinstance(kind, str) or not kind:
        raise ValueError("Entity ID kind must be a non-empty string")
    if _ID_SEPARATOR in kind:
        raise ValueError("Entity ID kind must not contain ':'")
    if any(not isinstance(part, str) or not part for part in identity_parts):
        raise ValueError("Entity ID identity parts must be non-empty strings")

    digest = fingerprint({"kind": kind, "identity": identity_parts})[:_ID_HEX_LENGTH]
    return f"{kind}{_ID_SEPARATOR}{digest}"


def find_entity_by_alias(
    entities: Mapping[str, Mapping[str, Any]], alias: str
) -> str | None:
    """Return the entity ID carrying ``alias``, or ``None`` if absent."""
    if not isinstance(alias, str) or not alias:
        raise ValueError("Entity alias must be a non-empty string")

    match: str | None = None
    for entity_id, entity in entities.items():
        if entity.get("alias") != alias:
            continue
        if match is not None:
            raise ValueError(f"Duplicate entity alias: {alias}")
        match = entity_id
    return match
