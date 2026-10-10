from __future__ import annotations

from pathlib import Path

from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.adapters.fmg.anomalies import (
    DEFAULT_SEVERITY,
    KIND_SEVERITY,
    SEVERITY_ORDER,
    format_counts,
    summarize_anomalies,
)
from worldloom.core import WorldState

ROOT = Path(__file__).parents[2]
CANONICAL_EXPORTS = (
    ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json",
    ROOT / "examples" / "Pithigy Full 2026-10-02-11-35.json",
    ROOT / "examples" / "Viveria Full 2026-10-02-11-31.json",
)
SKIPPED_BLOCKS = {"source", "mesh", "lookup_observations"}
RECOGNISED_BLOCKS = {"diagnostics", "entities", "features", "biomes", "climate"}


def _count_report(report):
    total = 0
    for name, block in report.items():
        if not isinstance(block, dict):
            continue
        anomaly = block.get("anomalies")
        counts = anomaly.get("counts") if isinstance(anomaly, dict) else None
        if isinstance(counts, dict):
            total += sum(
                count
                for paths in counts.values()
                if isinstance(paths, dict)
                for count in paths.values()
                if type(count) is int and count >= 0
            )
        if name == "diagnostics":
            for key in ("sentinels_minus_one", "out_of_range"):
                paths = block.get(key)
                if isinstance(paths, dict):
                    total += sum(
                        count for count in paths.values()
                        if type(count) is int and count >= 0
                    )
            count = block.get("invalid_structure_count")
            if type(count) is int and count >= 0:
                total += count
            sections = block.get("missing_sections")
            if isinstance(sections, list):
                total += len(sections)
    return total


def _import_report(path):
    world = WorldState()
    import_fmg_snapshot(world, path)
    return world.observations["fmg.import.report"]


def test_severity_table_and_unknown_kinds_default_to_warning():
    assert SEVERITY_ORDER == ("info", "warning", "error")
    assert KIND_SEVERITY == {
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
    assert DEFAULT_SEVERITY == "warning"
    summary = summarize_anomalies(
        {"entities": {"anomalies": {"counts": {"future-kind": {"x": 2}}}}}
    )
    assert summary is not None
    assert summary.by_kind["future-kind"]["severity"] == "warning"
    assert summary.by_severity == {"info": 0, "warning": 2, "error": 0}
    assert format_counts(summary) == "0 errors, 2 warnings, 0 info"


def test_mixed_report_shapes_count_exact_paths_and_skip_known_blocks():
    report = {
        "source": {"anomalies": {"counts": {"ignored": {"x": 99}}}},
        "mesh": {"unexpected": True},
        "lookup_observations": {"future": "ignored"},
        "entities": {
            "anomalies": {
                "counts": {
                    "sentinel": {"pack.cells[2].f": 2, "pack.cells[10].f": 1},
                    "lone-surrogate": {"pack.cells[3].name": 1},
                    "future-kind": {"pack.cells[1]": 4},
                }
            }
        },
        "diagnostics": {
            "sentinels_minus_one": {"pack.cells.c": 3},
            "out_of_range": {"pack.cells.c": 2},
            "invalid_structure_count": 2,
            "invalid_structure": [
                {"path": "pack.cells", "position": 4},
                {"path": "pack.cells", "position": 5},
            ],
            "missing_sections": ["grid", "pack.vertices"],
        },
        "climate": {
            "anomalies": {"counts": {"invalid-type": {"grid.cells[2].temp": 2}}}
        },
    }
    summary = summarize_anomalies(report)
    assert summary is not None
    assert summary.total == 19
    assert summary.by_severity == {"info": 6, "warning": 13, "error": 0}
    assert summary.by_block == {"climate": 2, "diagnostics": 9, "entities": 8}
    assert summary.by_kind["sentinel"]["count"] == 6
    assert summary.by_kind["sentinel"]["patterns"]["pack.cells[].f"] == {
        "count": 3,
        "paths": ["pack.cells[2].f", "pack.cells[10].f"],
    }
    assert summary.by_kind["invalid-structure"]["count"] == 2
    assert summary.unrecognised_blocks == []
    assert format_counts(summary) == "0 errors, 13 warnings, 6 info"


def test_patterns_normalise_indices_and_paths_are_naturally_sorted_and_capped():
    counts = {
        f"pack.cells[{index}].refs[0]": 2
        for index in (10, 2, 1, 11, 3, 4, 20)
    }
    summary = summarize_anomalies(
        {"entities": {"anomalies": {"counts": {"invalid-type": counts}}}}
    )
    assert summary is not None
    pattern = summary.by_kind["invalid-type"]["patterns"]["pack.cells[].refs[]"]
    assert pattern["count"] == 14
    assert pattern["paths"] == [
        "pack.cells[1].refs[0]",
        "pack.cells[2].refs[0]",
        "pack.cells[3].refs[0]",
        "pack.cells[4].refs[0]",
        "pack.cells[10].refs[0]",
    ]
    assert summary.total == sum(counts.values())


def test_malformed_counts_are_ignored_and_the_block_is_unrecognised():
    report = {
        "entities": {
            "anomalies": {
                "counts": {"invalid-type": {"pack.cells[0]": "bad", "pack.cells[1]": 2}}
            }
        },
        "future-block": {"some_other_shape": True},
        "source": {},
        "mesh": {},
        "non-mapping": [],
    }
    summary = summarize_anomalies(report)
    assert summary is not None
    assert summary.total == 2
    assert summary.by_kind["invalid-type"]["count"] == 2
    assert summary.unrecognised_blocks == ["entities", "future-block"]


def test_missing_none_and_non_mapping_reports_return_none():
    for report in (None, [], "report", 4):
        assert summarize_anomalies(report) is None
    assert summarize_anomalies({}) is not None
    assert summarize_anomalies({}).by_severity == {
        "info": 0,
        "warning": 0,
        "error": 0,
    }


def test_diagnostics_use_exact_invalid_structure_count_not_example_length():
    report = {
        "diagnostics": {
            "sentinels_minus_one": {"pack.cells.c": 2},
            "out_of_range": {"pack.cells.v": 1},
            "invalid_structure_count": 7,
            "invalid_structure": [{"path": "pack.cells", "position": 9}],
            "missing_sections": ["grid"],
        }
    }
    summary = summarize_anomalies(report)
    assert summary is not None
    assert summary.total == 11
    assert summary.by_kind["invalid-structure"]["count"] == 7
    assert summary.by_severity == {"info": 2, "warning": 9, "error": 0}
    assert summary.by_block == {"diagnostics": 11}
    assert summary.by_kind["invalid-structure"]["patterns"]["pack.cells[]"] == {
        "count": 1,
        "paths": ["pack.cells[9]"],
    }


def test_canonical_export_reports_are_fully_recognised_and_totals_match():
    for path in CANONICAL_EXPORTS:
        report = _import_report(path)
        summary = summarize_anomalies(report)
        assert summary is not None
        assert set(report) == SKIPPED_BLOCKS | RECOGNISED_BLOCKS
        assert summary.unrecognised_blocks == []
        assert summary.total == _count_report(report)

    thimaland = _import_report(CANONICAL_EXPORTS[0])
    summary = summarize_anomalies(thimaland)
    assert summary is not None
    diagnostics = thimaland["diagnostics"]["sentinels_minus_one"]
    assert summary.by_kind["sentinel"]["count"] == sum(diagnostics.values())
