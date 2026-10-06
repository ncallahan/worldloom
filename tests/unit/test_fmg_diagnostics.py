from worldloom.adapters.fmg.diagnostics import build_mesh_diagnostics


def test_missing_vertices_and_grid_are_diagnostics_not_out_of_range():
    data = {"pack": {"cells": [{"c": [0], "v": [0]}]}}
    diagnostics = build_mesh_diagnostics(data)
    assert diagnostics["missing_sections"] == ["grid", "pack.vertices"]
    assert diagnostics["out_of_range"] == {
        "pack.cells.c": 0,
        "pack.cells.v": 0,
        "pack.vertices.c": 0,
        "pack.vertices.v": 0,
    }


def test_non_dict_mesh_record_is_an_invalid_structure_diagnostic():
    data = {
        "pack": {
            "cells": [{"c": [0]}, "not-a-cell"],
            "vertices": [],
        },
        "grid": {"cells": [], "vertices": []},
    }
    diagnostics = build_mesh_diagnostics(data)
    assert {
        "path": "pack.cells.v",
        "position": 1,
        "kind": "invalid-structure",
    } in diagnostics["invalid_structure"]


def test_non_list_mesh_reference_is_an_invalid_structure_diagnostic():
    data = {
        "pack": {
            "cells": [{"c": 0}],
            "vertices": [{"v": [0], "c": [0]}],
        },
        "grid": {"cells": [0], "vertices": [0]},
    }
    diagnostics = build_mesh_diagnostics(data)
    assert {
        "path": "pack.cells.c",
        "position": 0,
        "kind": "invalid-structure",
    } in diagnostics["invalid_structure"]
