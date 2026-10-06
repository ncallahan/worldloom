from pathlib import Path

import pytest

from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.core import WorldState


REPO_ROOT = Path(__file__).parents[2]
THIMALAND = REPO_ROOT / "examples" / "Thimaland Full 2026-10-02-14-17.json"
THIMALAND_CELLS = "c8462844f3ab6c0991ea21420d361204e372926793e523f1ea942a8b786db974"
THIMALAND_VERTICES = "2eff83ee043431f735834cfbf06eac819b3366a14c45aacbf3a28812ca65d5ca"


def test_thimaland_mesh_fingerprints_match_experiment():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    assert world.fingerprint(world.fields["fmg.pack.cells"]) == THIMALAND_CELLS
    assert world.fingerprint(world.fields["fmg.pack.vertices"]) == THIMALAND_VERTICES


def test_import_is_deterministic():
    world_a = WorldState()
    world_b = WorldState()
    import_fmg_snapshot(world_a, THIMALAND)
    import_fmg_snapshot(world_b, THIMALAND)
    assert world_a.fields == world_b.fields
    assert world_a.observations == world_b.observations
    assert world_a.provenance == world_b.provenance


def test_import_report_contains_mesh_reference_diagnostics():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    diagnostics = world.observations["fmg.import.report"]["diagnostics"]
    assert diagnostics["sentinels_minus_one"]["pack.vertices.v"] == 68
    assert diagnostics["out_of_range"] == {
        "pack.cells.c": 0,
        "pack.cells.v": 0,
        "pack.vertices.c": 0,
        "pack.vertices.v": 0,
    }


def test_scope_is_not_silently_ignored():
    with pytest.raises(NotImplementedError):
        import_fmg_snapshot(WorldState(), THIMALAND, scope="map:test")


def test_import_round_trip_preserves_mesh_fingerprints(tmp_path: Path):
    from worldloom.core.persistence import load_world, save_world

    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    path = tmp_path / "thimaland.json"
    save_world(world, path)
    loaded = load_world(path)

    for name in ("fmg.pack.cells", "fmg.pack.vertices"):
        assert world.fingerprint(world.fields[name]) == loaded.fingerprint(loaded.fields[name])
