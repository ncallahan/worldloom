"""Structural and synthetic known-answer tests for FMG layering measurements."""
import importlib.util
import json
import math
from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "experiments" / "fmg_layering" / "measure.py"
SPEC = importlib.util.spec_from_file_location("fmg_layering_measure", MODULE_PATH)
MEASURE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MEASURE)


agreement_and_disagreement():
    data = {
        "settings": {"populationRate": 1, "urbanization": 0.5, "urbanDensity": 10},
        "cells": [{"i": 0, "state": 0, "pop": 7, "religion": 0, "burg": 2},
                  {"i": 1, "state": 0, "pop": 3, "religion": 1, "burg": -1}],
        "burgs": [{"i": 2, "cell": 0, "state": 0, "population": 4}],
        "states": [{"i": 0, "rural": 10, "urban": 4}],
        "religions": [{"rural": 7, "urban": 4}, {"rural": 3, "urban": 0}],
    }
    result = MEASURE.measure_export(data)
    assert result["state_comparisons"]["rural"][0]["comparisons"][0]["equal_exactly"]
    urban = result["state_comparisons"]["urban"][0]["comparisons"]
    assert urban[0]["equal_exactly"] and urban[1]["equal_exactly"]
    assert result["burg_cell_checks"]["burg_state_vs_cell_state"]["agreement"] == 1
    assert result["burg_cell_checks"]["cell_burg_vs_explicit_burg_i"]["agreement"] == 1
    assert result["religion_comparisons"]["0"]["rural_comparison"]["equal_exactly"]
    assert result["religion_comparisons"]["0"]["urban_comparison"]["equal_exactly"]


def test_deliberate_disagreement_is_reported():
    result = MEASURE.measure_export({
        "cells": [{"state": 0, "pop": 2, "burg": -1}],
        "burgs": [{"i": 4, "cell": 0, "state": 1, "population": 9}],
        "states": [{"rural": 8, "urban": 3}],
    })
    row = result["state_comparisons"]["rural"][0]["comparisons"][0]
    assert row["computed_sum"] == 2
    assert row["absolute_difference"] == 6
    assert row["equal_exactly"] is False
    assert result["burg_cell_checks"]["burg_state_vs_cell_state"]["disagreement"] == 1


def test_missing_keys_and_collections_are_tolerated():
    result = MEASURE.measure_export({})
    assert result["population_fields"]["cells.pop"]["count"] == 0
    assert result["candidate_references"]["states.capital"]["missing_count"] == 0
    assert result["totals"]["cells_pop_sum"] == 0
    assert result["settings"]["populationRate"]["type"] == "missing"


def test_non_dict_records_are_counted_not_raised():
    result = MEASURE.measure_export({"cells": [None, 4, {"pop": 1}],
                                     "states": ["bad"], "burgs": [False]})
    assert result["malformed_records"]["cells"] == 2
    assert result["malformed_records"]["states"] == 1
    assert result["malformed_records"]["burgs"] == 1
    assert result["population_fields"]["cells.pop"]["count"] == 1


def test_bool_and_string_population_values_are_not_numeric():
    result = MEASURE.measure_export({"cells": [{"pop": True}, {"pop": "12"}, {"pop": 2}]})
    stats = result["population_fields"]["cells.pop"]
    assert stats["count"] == 1
    assert stats["sum"] == 2
    assert stats["malformed_or_non_numeric"] == 2
