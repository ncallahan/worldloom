"""Naming and display-label helpers for the Markdown-vault projection."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

_FORBIDDEN = re.compile(r'[\\/:*?"<>|#^\[\]\x00-\x1f\x7f]')
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_ID_RE = re.compile(r"^([A-Za-z0-9_-]+):([0-9a-fA-F]{12})$")


def is_standard_id(entity_id: Any) -> bool:
    """Return whether an entity ID uses the standard kind:12-hex form."""
    return isinstance(entity_id, str) and _ID_RE.fullmatch(entity_id) is not None


def id_parts(entity_id: str) -> tuple[str, str]:
    match = _ID_RE.fullmatch(entity_id)
    if not match:
        raise ValueError(f"Entity ID is not a projection-compatible kind:12hex ID: {entity_id!r}")
    return match.group(1), match.group(2).lower()


def entity_title(entity: dict[str, Any], kind: str) -> str:
    value = entity.get("attributes", {}).get("name")
    raw = value if isinstance(value, str) and value else f"Unnamed {kind}"
    raw = unicodedata.normalize("NFC", raw)
    raw = _FORBIDDEN.sub("", raw)
    raw = " ".join(raw.split()).strip(" .")
    raw = raw[:80].rstrip(" .")
    reserved_base = raw.split(".", 1)[0]
    if reserved_base.upper() in _RESERVED:
        raw = f"{reserved_base}_{raw[len(reserved_base):]}"
    return raw or f"Unnamed {kind}"


def entity_filename(entity_id: str, entity: dict[str, Any]) -> tuple[str, str]:
    kind, digest = id_parts(entity_id)
    title = entity_title(entity, kind)
    return kind, f"{title} ({digest}).md"


def build_display_map(
    entities: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], dict[str, dict[str, int]]]:
    groups: dict[tuple[str, str], list[str]] = {}
    for entity_id, entity in entities.items():
        kind = id_parts(entity_id)[0]
        groups.setdefault((kind, entity["_title"]), []).append(entity_id)

    displays: dict[str, str] = {}
    counts: dict[str, dict[str, int]] = {}
    for (kind, title), entity_ids in sorted(groups.items()):
        qualifier_by_id: dict[str, str | None] = {}
        for entity_id in entity_ids:
            qualifier = None
            refs = entities[entity_id].get("refs", {})
            if isinstance(refs, dict):
                for field in sorted(refs):
                    value = refs[field]
                    if isinstance(value, str) and value in entities:
                        qualifier = entities[value]["_title"]
                        break
            qualifier_by_id[entity_id] = qualifier

        candidates = {
            entity_id: title if qualifier is None else f"{title} ({qualifier})"
            for entity_id, qualifier in qualifier_by_id.items()
        }
        candidate_counts: dict[str, int] = {}
        for candidate in candidates.values():
            candidate_counts[candidate] = candidate_counts.get(candidate, 0) + 1

        kind_counts = counts.setdefault(kind, {"qualifier": 0, "hex": 0})
        for entity_id in sorted(entity_ids):
            qualifier = qualifier_by_id[entity_id]
            candidate = candidates[entity_id]
            if len(entity_ids) == 1:
                displays[entity_id] = title
            elif qualifier is not None and candidate_counts[candidate] == 1:
                displays[entity_id] = candidate
                kind_counts["qualifier"] += 1
            else:
                displays[entity_id] = (
                    f"{candidate[:-1]}, {id_parts(entity_id)[1]})"
                    if qualifier is not None
                    else f"{title} ({id_parts(entity_id)[1]})"
                )
                kind_counts["hex"] += 1
    return displays, counts
