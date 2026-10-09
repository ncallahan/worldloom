from __future__ import annotations

import pytest

from worldloom.adapters.markdown_vault.naming import build_display_map
from worldloom.adapters.markdown_vault.plan import build_projection_plan


def _entity(name: str, digest: str, kind: str = "test", refs=None):
    return {"attributes": {"name": name}, "refs": {} if refs is None else refs}, f"{kind}:{digest}"


def _entities(*items):
    return {entity_id: value for value, entity_id in items}


def test_plan_assigns_titles_and_paths():
    world_entities = _entities(
        _entity("North / Gate", "000000000001", "place"),
        _entity("", "000000000002", "place"),
    )
    plan = build_projection_plan(world_entities)
    assert plan.entities["place:000000000001"]["_title"] == "North  Gate"
    assert plan.entities["place:000000000001"]["_path"] == "place/North  Gate (000000000001).md"
    assert plan.paths["place:000000000002"] == "place/Unnamed place (000000000002).md"
    assert world_entities["place:000000000001"]["attributes"]["name"] == "North / Gate"


def test_plan_raises_projected_path_collision():
    world_entities = _entities(
        _entity("A", "000000000001"),
        _entity("B", "000000000002"),
    )
    from worldloom.adapters.markdown_vault import plan as plan_module

    original = plan_module.entity_filename
    plan_module.entity_filename = lambda entity_id, entity: ("test", "same (000000000000).md")
    try:
        with pytest.raises(ValueError, match=r"^Projected path collision: test/same \(000000000000\)\.md$"):
            build_projection_plan(world_entities)
    finally:
        plan_module.entity_filename = original


def test_plan_invalid_id_message_is_unchanged():
    with pytest.raises(
        ValueError,
        match=r"^Entity ID is not a projection-compatible kind:12hex ID: 'invalid'$",
    ):
        build_projection_plan({"invalid": {"attributes": {"name": "Bad"}, "refs": {}}})


def test_plan_displays_and_disambiguation_counts_match_naming_helper():
    world_entities = _entities(
        _entity("Same", "000000000001", refs={"parent": "place:000000000001"}),
        _entity("Same", "000000000002", refs={"parent": "place:000000000002"}),
        _entity("North", "000000000001", "place"),
    )
    plan = build_projection_plan(world_entities)
    displays, counts = build_display_map(plan.entities)
    assert plan.displays == displays
    assert plan.disambiguation_counts == counts


def test_plan_inverse_handles_single_list_and_dangling_references():
    target = "place:000000000001"
    source = "burg:000000000002"
    other = "burg:000000000003"
    world_entities = _entities(
        _entity("Target", "000000000001", "place"),
        _entity("Source", "000000000002", "burg", refs={
            "single": target,
            "list": [target, other, "place:999999999999"],
            "dangling": "place:999999999999",
        }),
        _entity("Other", "000000000003", "burg"),
    )
    inverse = build_projection_plan(world_entities).inverse
    assert inverse[target] == [
        ("burg", "single", source),
        ("burg", "list", source),
    ]
    assert inverse[other] == [("burg", "list", source)]
    assert "place:999999999999" not in inverse


def test_duplicate_title_counts_are_per_kind():
    world_entities = _entities(
        _entity("Same", "000000000001", "place"),
        _entity("Same", "000000000002", "place"),
        _entity("Other", "000000000003", "place"),
        _entity("Same", "000000000004", "river"),
        _entity("Same", "000000000005", "river"),
        _entity("Else", "000000000006", "river"),
        _entity("Only", "000000000007", "mountain"),
    )
    assert build_projection_plan(world_entities).duplicate_counts == {
        "place": 1,
        "river": 1,
        "mountain": 0,
    }


def test_later_invalid_id_is_raised_before_earlier_path_collision():
    from worldloom.adapters.markdown_vault import plan as plan_module

    world_entities = _entities(
        _entity("A", "000000000001"),
        _entity("B", "000000000002"),
        ({"attributes": {"name": "Bad"}, "refs": {}}, "not-an-id"),
    )
    original = plan_module.entity_filename
    plan_module.entity_filename = lambda entity_id, entity: ("test", "same.md")
    try:
        with pytest.raises(ValueError, match="Entity ID is not a projection-compatible"):
            build_projection_plan(world_entities)
    finally:
        plan_module.entity_filename = original
