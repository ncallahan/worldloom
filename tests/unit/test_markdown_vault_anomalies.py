from __future__ import annotations

from pathlib import Path

from worldloom.adapters import export_markdown_vault
from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.adapters.fmg.anomalies import summarize_anomalies
from worldloom.adapters.markdown_vault.markup import code_span
from worldloom.adapters.markdown_vault.report import render_anomalies_note, render_import_note
from worldloom.core import WorldState
from worldloom.core.persistence import load_world, save_world

ROOT = Path(__file__).parents[2]
CANONICAL_EXPORTS = (
    ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json",
    ROOT / "examples" / "Pithigy Full 2026-10-02-11-35.json",
    ROOT / "examples" / "Viveria Full 2026-10-02-11-31.json",
)


def _world(report):
    return WorldState(observations={"fmg.import.report": report})


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _mixed_report():
    return {
        "entities": {
            "anomalies": {
                "counts": {
                    "sentinel": {"pack.cells[0].f": 1},
                    "placeholder-reference": {"pack.features[0]": 1},
                    "lone-surrogate": {"pack.cells[2].name": 2},
                    "invalid-type": {"pack.cells[3]": 1},
                }
            }
        }
    }


def test_anomalies_note_and_import_note_render_severity_summary(tmp_path):
    report = _mixed_report()
    world = _world(report)
    import_note = render_import_note(world, {}, {})
    anomalies_note = render_anomalies_note(report)
    output = tmp_path / "vault"
    export_markdown_vault(world, output)

    assert "## Anomalies" in import_note
    assert "### Warning (3)" in import_note
    assert "- lone-surrogate: 2" in import_note
    assert import_note.index("### Warning") < import_note.index("### Info")
    assert "### Error" not in import_note
    assert "## Warning (3)" in anomalies_note
    assert "## Info (2)" in anomalies_note
    assert anomalies_note.index("## Warning") < anomalies_note.index("## Info")
    assert "## Error" not in anomalies_note
    assert "### `lone-surrogate` (2)" in anomalies_note
    assert "- `pack.cells[].name`: 2" in anomalies_note
    assert "  - `pack.cells[2].name`" in anomalies_note
    index = (output / "index.md").read_text(encoding="utf-8")
    assert index.startswith(
        "Import anomalies: 0 errors, 3 warnings "
        "(see [[_worldloom/anomalies|anomalies]])\n\n# Worldloom\n"
    )
    assert (output / "_worldloom/anomalies.md").read_text(encoding="utf-8") == anomalies_note


def test_zero_anomaly_report_gets_file_and_no_banner(tmp_path):
    world = _world({"entities": {"anomalies": {"counts": {}}}})
    output = tmp_path / "vault"
    export_markdown_vault(world, output)
    import_note = (output / "_worldloom/import.md").read_text(encoding="utf-8")
    anomalies_note = (output / "_worldloom/anomalies.md").read_text(encoding="utf-8")
    index = (output / "index.md").read_text(encoding="utf-8")

    assert "- No anomalies recorded" in import_note
    assert "No anomalies recorded" in anomalies_note
    assert index.startswith("# Worldloom\n")
    assert "Import anomalies:" not in index


def test_info_only_report_does_not_add_banner(tmp_path):
    world = _world(
        {"entities": {"anomalies": {"counts": {"sentinel": {"pack.cells[0].f": 1}}}}}
    )
    output = tmp_path / "vault"
    export_markdown_vault(world, output)
    index = (output / "index.md").read_text(encoding="utf-8")
    anomalies_note = (output / "_worldloom/anomalies.md").read_text(encoding="utf-8")
    assert index.startswith("# Worldloom\n")
    assert "## Info (1)" in anomalies_note
    assert "## Warning" not in anomalies_note
    assert "## Error" not in anomalies_note


def test_reserved_error_severity_is_zero_in_all_vault_surfaces(tmp_path):
    report = {
        "entities": {
            "anomalies": {
                "counts": {
                    "sentinel": {"pack.cells[0].f": 1},
                    "invalid-type": {"pack.cells[1]": 2},
                }
            }
        }
    }
    summary = summarize_anomalies(report)
    assert summary is not None
    assert summary.by_severity["error"] == 0
    assert summary.total == 3

    output = tmp_path / "vault"
    export_markdown_vault(_world(report), output)
    import_note = (output / "_worldloom/import.md").read_text(encoding="utf-8")
    anomalies_note = (output / "_worldloom/anomalies.md").read_text(encoding="utf-8")
    index = (output / "index.md").read_text(encoding="utf-8")
    assert "0 errors" in index
    assert "### Error" not in import_note
    assert "## Error" not in anomalies_note


def test_hostile_paths_are_rendered_as_inert_code_spans():
    hostile = "pack.cells[0]\n# Injected heading"
    report = {"entities": {"anomalies": {"counts": {"invalid-type": {hostile: 1}}}}}
    text = render_anomalies_note(report)
    assert code_span(hostile) in text
    assert "\n# Injected heading" not in text
    assert "\n  - " + code_span(hostile) in text


def test_anomaly_export_is_deterministic_and_survives_save_load(tmp_path):
    world = _world(_mixed_report())
    first, second = tmp_path / "first", tmp_path / "second"
    export_markdown_vault(world, first)
    export_markdown_vault(world, second)
    assert _tree(first) == _tree(second)

    saved = tmp_path / "world.json"
    save_world(world, saved)
    restored = load_world(saved)
    roundtrip = tmp_path / "roundtrip"
    export_markdown_vault(restored, roundtrip)
    assert _tree(first) == _tree(roundtrip)


def test_canonical_exports_surface_report_derived_counts_and_banner(tmp_path):
    for source in CANONICAL_EXPORTS:
        world = WorldState()
        import_fmg_snapshot(world, source)
        report = world.observations["fmg.import.report"]
        summary = summarize_anomalies(report)
        assert summary is not None
        assert summary.by_kind["lone-surrogate"]["count"] > 0
        output = tmp_path / source.stem
        export_markdown_vault(world, output)
        expected = (
            f"Import anomalies: {summary.by_severity['error']} errors, "
            f"{summary.by_severity['warning']} warnings "
            "(see [[_worldloom/anomalies|anomalies]])"
        )
        index = (output / "index.md").read_text(encoding="utf-8")
        assert index.startswith(expected + "\n\n# Worldloom\n")
        import_note = (output / "_worldloom/import.md").read_text(encoding="utf-8")
        assert f"### Warning ({summary.by_severity['warning']})" in import_note
        anomalies_note = (output / "_worldloom/anomalies.md").read_text(encoding="utf-8")
        assert "## Warning" in anomalies_note
