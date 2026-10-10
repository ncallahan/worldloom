"""Shared, reader-side interpretation of FMG import anomalies."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

SEVERITY_ORDER = ("info", "warning", "error")
KIND_SEVERITY = {
    "sentinel": "info",
    "placeholder-reference": "info",
    "lone-surrogate": "warning",
    "nonstandard-id": "warning",
    "nonserialisable-value": "warning",
    "key-collision": "warning",
    "nonstandard-entity-shape": "warning",
    "fingerprint-fallback": "warning",
    "coerced-value": "info",
    "invalid-type": "warning",
    "out-of-range": "warning",
    "unresolved-reference": "warning",
    "invalid-structure": "warning",
    "missing-section": "warning",
    "missing-field": "warning",
    "id-position-mismatch": "warning",
}
DEFAULT_SEVERITY = "warning"
_KNOWN_SKIPPED_BLOCKS = {"source", "mesh", "lookup_observations"}
_DIAGNOSTIC_KEYS = {
    "sentinels_minus_one",
    "out_of_range",
    "invalid_structure_count",
    "invalid_structure",
    "missing_sections",
}
_INDEX_RE = re.compile(r"\[(\d+)\]")
_NATURAL_RE = re.compile(r"(\d+)")


@dataclass(frozen=True)
class AnomalySummary:
    """Immutable top-level anomaly totals and deterministic detail."""

    by_severity: dict[str, int]
    total: int
    by_kind: dict[str, dict[str, Any]]
    by_block: dict[str, int]
    unrecognised_blocks: list[str]


def _natural_key(value: str) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            (1, len(part.lstrip("0") or "0"), part.lstrip("0") or "0", part)
            if part.isdigit()
            else (0, part.casefold(), part)
        )
        for part in _NATURAL_RE.split(value)
    )


def _label(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return repr(value)
    except Exception:
        return "<unprintable>"


def _path(value: Any) -> str:
    return value if isinstance(value, str) else "<invalid path>"


def _add_pattern(
    patterns: dict[str, dict[str, dict[str, Any]]],
    kind: str,
    path: str,
    count: int,
) -> None:
    if count <= 0:
        return
    pattern = _INDEX_RE.sub("[]", path)
    item = patterns.setdefault(kind, {}).setdefault(
        pattern, {"count": 0, "paths": {}}
    )
    item["count"] += count
    item["paths"][path] = item["paths"].get(path, 0) + count


def _anomaly_entries(
    block: Mapping[str, Any],
) -> tuple[list[tuple[str, str, int]] | None, bool]:
    anomaly_data = block.get("anomalies")
    if not isinstance(anomaly_data, Mapping):
        return None, False
    counts = anomaly_data.get("counts")
    if not isinstance(counts, Mapping):
        return None, True
    entries: list[tuple[str, str, int]] = []
    malformed = False
    for raw_kind, raw_paths in counts.items():
        if not isinstance(raw_kind, str) or not isinstance(raw_paths, Mapping):
            malformed = True
            continue
        for raw_path, count in raw_paths.items():
            if not isinstance(raw_path, str) or type(count) is not int or count < 0:
                malformed = True
                continue
            if count:
                entries.append((raw_kind, raw_path, count))
    return entries, malformed


def _counted_path_entries(
    block: Mapping[str, Any], field: str, kind: str
) -> tuple[list[tuple[str, str, int]], bool, bool]:
    if field not in block:
        return [], False, False
    paths = block[field]
    if not isinstance(paths, Mapping):
        return [], True, False
    entries = []
    malformed = False
    for raw_path, count in paths.items():
        if not isinstance(raw_path, str) or type(count) is not int or count < 0:
            malformed = True
            continue
        if count:
            entries.append((kind, raw_path, count))
    return entries, malformed, True


def _structure_entries(
    block: Mapping[str, Any],
) -> tuple[list[tuple[str, str, int]], dict[str, int], bool, bool]:
    has_count = "invalid_structure_count" in block
    has_examples = "invalid_structure" in block
    if not has_count and not has_examples:
        return [], {}, False, False

    entries = []
    overrides = {}
    malformed = has_count != has_examples
    recognised = False
    if has_count:
        count = block["invalid_structure_count"]
        if type(count) is int and count >= 0:
            overrides["invalid-structure"] = count
            recognised = True
        else:
            malformed = True
    if has_examples:
        examples = block["invalid_structure"]
        if not isinstance(examples, list) or not has_count:
            malformed = True
        else:
            recognised = True
            for example in examples[:overrides.get("invalid-structure", 0)]:
                if not isinstance(example, Mapping):
                    malformed = True
                    continue
                raw_path = example.get("path")
                if not isinstance(raw_path, str):
                    malformed = True
                    raw_path = "<invalid path>"
                position = example.get("position")
                if type(position) is int and position >= 0:
                    raw_path = f"{raw_path}[{position}]"
                entries.append(("invalid-structure-example", raw_path, 1))
    return entries, overrides, malformed, recognised


def _missing_section_entries(
    block: Mapping[str, Any],
) -> tuple[list[tuple[str, str, int]], bool, bool]:
    if "missing_sections" not in block:
        return [], False, False
    sections = block["missing_sections"]
    if not isinstance(sections, list):
        return [], True, False
    entries = []
    malformed = False
    for section in sections:
        if not isinstance(section, str):
            malformed = True
        entries.append(("missing-section", _path(section), 1))
    return entries, malformed, True


def _diagnostic_entries(
    block: Mapping[str, Any],
) -> tuple[list[tuple[str, str, int]], dict[str, int], bool, bool]:
    if not _DIAGNOSTIC_KEYS.intersection(block):
        return [], {}, False, False

    entries = []
    overrides = {}
    malformed = False
    recognised = False
    for field, kind in (
        ("sentinels_minus_one", "sentinel"),
        ("out_of_range", "out-of-range"),
    ):
        found, bad, valid = _counted_path_entries(block, field, kind)
        entries.extend(found)
        malformed = malformed or bad
        recognised = recognised or valid

    found, counts, bad, valid = _structure_entries(block)
    entries.extend(found)
    overrides.update(counts)
    malformed = malformed or bad
    recognised = recognised or valid

    found, bad, valid = _missing_section_entries(block)
    entries.extend(found)
    malformed = malformed or bad
    recognised = recognised or valid
    return entries, overrides, malformed, recognised

def summarize_anomalies(report: Any) -> AnomalySummary | None:
    """Summarize supported report shapes without raising on malformed input."""
    if not isinstance(report, Mapping):
        return None

    kind_counts: dict[str, int] = {}
    patterns: dict[str, dict[str, dict[str, Any]]] = {}
    by_block: dict[str, int] = {}
    unrecognised: set[str] = set()

    for raw_block_name, block in report.items():
        if not isinstance(block, Mapping):
            continue
        block_name = _label(raw_block_name)
        if block_name in _KNOWN_SKIPPED_BLOCKS:
            continue

        entries, malformed = _anomaly_entries(block)
        anomaly_malformed = malformed
        overrides: dict[str, int] = {}
        if entries is None:
            diagnostic_entries, overrides, diagnostic_malformed, recognised = (
                _diagnostic_entries(block)
            )
            if not recognised:
                unrecognised.add(block_name)
                continue
            entries = diagnostic_entries
            malformed = anomaly_malformed or diagnostic_malformed
            if malformed:
                unrecognised.add(block_name)
        elif malformed:
            unrecognised.add(block_name)

        block_total = 0
        for kind, path, count in entries:
            if kind == "invalid-structure-example":
                _add_pattern(patterns, "invalid-structure", path, count)
                continue
            kind_counts[kind] = kind_counts.get(kind, 0) + count
            block_total += count
            _add_pattern(patterns, kind, path, count)

        for kind, count in overrides.items():
            if count:
                kind_counts[kind] = kind_counts.get(kind, 0) + count
                block_total += count
        if block_total:
            by_block[block_name] = block_total

    by_severity = {severity: 0 for severity in SEVERITY_ORDER}
    by_kind: dict[str, dict[str, Any]] = {}
    for kind in sorted(kind_counts, key=_natural_key):
        count = kind_counts[kind]
        severity = KIND_SEVERITY.get(kind, DEFAULT_SEVERITY)
        by_severity[severity] += count
        detail = {}
        for pattern in sorted(patterns.get(kind, {}), key=_natural_key):
            item = patterns[kind][pattern]
            paths = sorted(item["paths"], key=_natural_key)[:5]
            detail[pattern] = {"count": item["count"], "paths": paths}
        by_kind[kind] = {
            "severity": severity,
            "count": count,
            "patterns": detail,
        }

    return AnomalySummary(
        by_severity=by_severity,
        total=sum(kind_counts.values()),
        by_kind=by_kind,
        by_block={key: by_block[key] for key in sorted(by_block, key=_natural_key)},
        unrecognised_blocks=sorted(unrecognised, key=_natural_key),
    )


def format_counts(summary: AnomalySummary) -> str:
    """Format severity totals in the stable CLI order."""
    return (
        f"{summary.by_severity['error']} errors, "
        f"{summary.by_severity['warning']} warnings, "
        f"{summary.by_severity['info']} info"
    )
