from pathlib import Path
from worldloom.adapters.fmg import import_fmg_snapshot
from worldloom.core import WorldState

THIMALAND = Path("examples/Thimaland Full 2026-10-02-14-17.json")
THIMALAND_CELLS = "0fee46f9a89d7dfaac01433361b9a29b43f4c9e0bb27348c463741c253217710"
THIMALAND_VERTICES = "0fdcd7106564d0b4735fc206be494413dc9cbf4279caadb3f08e7f15a59cec51"

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

def test_import_report_contains_source_metadata_and_mesh_counts():
    world = WorldState()
    import_fmg_snapshot(world, THIMALAND)
    report = world.observations["fmg.import.report"]
    assert report["source"]["sha256"] == "d37a94173eb66d4aae73312838e9e100e43a95f1b7be7c0b6af2b3186db99423"
    assert report["source"]["fmg_version"] == "1.153.1"
    assert report["source"]["mapId"] == 1790914616100
    assert report["mesh"]["pack_cells"] == len(world.fields["fmg.pack.cells"])
    assert report["mesh"]["pack_vertices"] == len(world.fields["fmg.pack.vertices"])
