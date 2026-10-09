from __future__ import annotations

from worldloom.adapters.markdown_vault.report import render_import_note
from worldloom.core import WorldState


def _world(*, fields=None, observations=None, entities=None):
    world = WorldState(fields={} if fields is None else fields, observations={} if observations is None else observations)
    for entity_id, entity in ({} if entities is None else entities).items():
        world.add_entity(entity_id, entity)
    return world


def test_source_metadata_and_entity_counts_use_fmg_collection_or_id_kind():
    world = _world(
        fields={"fmg.source": {"z": 2, "name": "map"}},
        entities={
            "place:000000000001": {"attributes": {"name": "North"}, "fmg": {"collection": "places"}},
            "river:000000000002": {"attributes": {"name": "River"}},
        },
    )
    text = render_import_note(world, {"place": 1}, {})
    assert "## Source metadata" in text and "- name: " in text and "- z: " in text
    assert "- places: 1" in text and "- river: 1" in text
    assert "- place: 1 (qualifier: 0, hex: 0)" in text


def test_anomaly_mappings_and_diagnostics_shapes_and_missing_report():
    report = {
        "diagnostics": {"sentinels_minus_one": {"a": 2, "b": 1}, "out_of_range": [1, 2], "invalid_structure_count": 0, "missing_sections": []},
        "entities": {"anomalies": {"total": 4, "counts": {"bad": {"a": 2, "b": 1}, "other": {"x": 1}}}},
        "features": {"sentinels_minus_one": 0, "out_of_range": "bad", "invalid_structure_count": 0, "missing_sections": []},
        "biomes": [],
        "climate": {"sentinels_minus_one": 1},
    }
    text = render_import_note(_world(observations={"fmg.import.report": report}), {}, {})
    assert "### diagnostics" in text and "- total: 5" in text
    assert "- out_of_range: 2" in text and "- sentinels_minus_one: 3" in text
    assert "### entities\n- total: 4\n- bad: 3\n- other: 1" in text
    assert "### features" not in text and "### biomes" not in text
    assert "### climate\n- total: 1\n- sentinels_minus_one: 1" in text
    for observations in ({}, {"fmg.import.report": None}, {"fmg.import.report": []}):
        assert "## Anomalies" in render_import_note(_world(observations=observations), {}, {})


def test_duplicate_title_lines_with_and_without_disambiguation_counts():
    world = _world()
    text = render_import_note(world, {"place": 2, "river": 1}, {"place": {"qualifier": 1, "hex": 1}})
    assert "- place: 2 (qualifier: 1, hex: 1)" in text
    assert "- river: 1 (qualifier: 0, hex: 0)" in text
