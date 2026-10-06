import pytest
from worldloom.adapters.fmg.spaces import RefSpec, resolve_mesh_ref

def test_resolve_mesh_ref_returns_explicit_space_and_index():
    ref = resolve_mesh_ref(
        3,
        RefSpec("pack.cells.c", "pack.cells"),
        limits={"pack.cells": 10},
    )
    assert ref.space == "pack.cells"
    assert ref.index == 3

def test_resolve_mesh_ref_skips_minus_one_sentinel():
    assert resolve_mesh_ref(
        -1,
        RefSpec("rivers.cells", "pack.cells"),
        limits={"pack.cells": 10},
    ) is None

def test_resolve_mesh_ref_rejects_out_of_range():
    with pytest.raises(IndexError):
        resolve_mesh_ref(
            10,
            RefSpec("pack.cells.c", "pack.cells"),
            limits={"pack.cells": 10},
        )
