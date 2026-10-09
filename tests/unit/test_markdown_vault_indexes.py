from __future__ import annotations

import re

from worldloom.adapters.markdown_vault.indexes import render_indexes
from worldloom.adapters.markdown_vault.plan import build_projection_plan
from worldloom.core import WorldState


def _world():
    world = WorldState()
    world.add_entity("zeta:000000000001", {
        "attributes": {"name": "Zulu", "type": "a", "group": "with ```ticks"},
        "refs": {},
    })
    world.add_entity("alpha:000000000002", {
        "attributes": {"name": "Alpha", "type": "a", "group": "group ]] # one"},
        "refs": {},
    })
    world.add_entity("alpha:000000000003", {
        "attributes": {"name": "Missing", "type": None},
        "refs": {},
    })
    world.add_entity("alpha:000000000004", {
        "attributes": {"name": "Beta", "type": "z]] # two", "group": "group ]] # one"},
        "refs": {},
    })
    world.add_entity("plain:000000000005", {"attributes": {"name": "Plain"}, "refs": {}})
    return world


def test_group_indexes_include_none_and_fence_hostile_values():
    plan = build_projection_plan(_world().entities)
    rendered = render_indexes(plan)
    type_text = rendered["indexes/alpha-by-type.md"].decode("utf-8")
    group_text = rendered["indexes/alpha-by-group.md"].decode("utf-8")
    assert "### (none) (1)" in type_text
    assert "z]] # two" in type_text
    assert "group ]] # one" in group_text
    assert "````with ```ticks````" in rendered["indexes/zeta-by-group.md"].decode("utf-8")


def test_group_section_counts_sum_to_kind_size():
    plan = build_projection_plan(_world().entities)
    rendered = render_indexes(plan)
    for kind, size in (("alpha", 3), ("zeta", 1)):
        for attribute in ("type", "group"):
            key = f"indexes/{kind}-by-{attribute}.md"
            if key not in rendered:
                continue
            text = rendered[key].decode("utf-8")
            counts = [int(value) for value in re.findall(r"^### .* \((\d+)\)$", text, re.MULTILINE)]
            assert sum(counts) == size


def test_kind_without_categorical_attributes_has_no_group_indexes():
    rendered = render_indexes(build_projection_plan(_world().entities))
    assert "indexes/plain-by-type.md" not in rendered
    assert "indexes/plain-by-group.md" not in rendered
    assert "indexes/plain.md" in rendered


def test_member_sort_order_and_root_index_lines():
    rendered = render_indexes(build_projection_plan(_world().entities))
    alpha = rendered["indexes/alpha.md"].decode("utf-8")
    assert alpha.index("|Alpha]]") < alpha.index("|Beta]]") < alpha.index("|Missing]]")
    root = rendered["index.md"].decode("utf-8")
    assert root.startswith("# Worldloom\n\nGenerated note indexes:\n\n")
    assert "- [[indexes/alpha|alpha]] (3)" in root
    assert "- [[indexes/zeta|zeta]] (1)" in root
    assert "- [[indexes/alpha-by-type|alpha by type]] (3)" in root
    assert "- [[indexes/alpha-by-group|alpha by group]] (3)" in root


def test_render_indexes_order_matches_export_generated_dict(monkeypatch, tmp_path):
    import worldloom.adapters.markdown_vault.exporter as exporter

    world = _world()
    captured = {}

    def capture(root, files, **kwargs):
        captured["keys"] = list(files)

    monkeypatch.setattr(exporter, "write_managed_tree", capture)
    exporter.export_markdown_vault(world, tmp_path / "unused")
    plan = build_projection_plan(world.entities)
    expected = list(render_indexes(plan))
    entity_count = len(plan.entities)
    assert captured["keys"][entity_count:-1] == expected
    assert captured["keys"][-2:] == ["index.md", "_worldloom/import.md"]
