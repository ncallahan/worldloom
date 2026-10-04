import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from make_slice import make_slice, verify_slice, write_slice


def fixture():
    return {
        "info": {"version": "1.153.1", "width": 10, "height": 10},
        "settings": {"options": {"map": {"graph": {"points": 3}}}},
        "nameBases": {},
        "pack": {
            "cells": [
                {"i": 0, "c": [1], "v": [0, 1, 2], "g": 0, "burg": 1, "state": 0, "province": 1, "culture": 0, "religion": 0},
                {"i": 1, "c": [0, 2], "v": [1, 2, 3], "g": 1, "burg": 0, "state": 1, "province": 0, "culture": 0, "religion": 0},
                {"i": 2, "c": [1], "v": [2, 3, 0], "g": 1, "burg": 0, "state": 0, "province": 1, "culture": 0, "religion": 0},
            ],
            "vertices": [
                {"i": 0, "v": [1, 2], "c": [0, 1, 2]},
                {"i": 1, "v": [0, 2], "c": [0, 1, 2]},
                {"i": 2, "v": [0, 1, 3], "c": [0, 1, 2]},
                {"i": 3, "v": [2], "c": [1, 2]},
            ],
            "burgs": [0, {"i": 1, "cell": 0, "state": 0, "province": 1, "name": "A"}],
            "states": [
                {"i": 0, "neighbors": [1], "provinces": [1], "diplomacy": ["x", "ally"]},
                {"i": 1, "neighbors": [0], "provinces": [], "diplomacy": ["ally", "x"]},
            ],
            "provinces": [0, {"i": 1, "state": 0, "center": 0, "burgs": [1]}],
            "features": [0],
            "biomes": [{"i": 0}],
            "cultures": [{"i": 0}],
            "religions": [{"i": 0}],
            "goods": [{"i": 1, "name": "grain"}],
            "rivers": [{"i": 7, "cells": [1, -1, 2]}],
            "routes": [{"i": 4, "points": [[1.0, 2.0, 0], [2.0, 3.0, 1]]}],
            "markers": [{"i": 1, "cell": 2}],
            "zones": [{"i": 1, "cells": [0, 1]}],
        },
        "grid": {
            "cells": [
                {"i": 0, "v": [0, 1], "c": [1], "b": 0, "temp": 1.0},
                {"i": 1, "v": [1, 2], "c": [0, 2], "b": 0, "temp": 2.0},
                {"i": 2, "v": [2, 3], "c": [1], "b": 0, "temp": 3.0},
            ],
            "vertices": [
                {"i": 0, "p": [0, 0], "v": [1], "c": [0]},
                {"i": 1, "p": [1, 0], "v": [0, 2], "c": [0, 1]},
                {"i": 2, "p": [1, 1], "v": [1, 3], "c": [1, 2]},
                {"i": 3, "p": [0, 1], "v": [2], "c": [2]},
            ],
        },
    }


class SliceTests(unittest.TestCase):
    def test_slice_is_small_and_reproducible(self):
        a = make_slice(fixture(), 1, 1)
        b = make_slice(fixture(), 1, 1)
        sa = json.dumps(a, sort_keys=True, separators=(",", ":")).encode()
        sb = json.dumps(b, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(hashlib.sha256(sa).hexdigest(), hashlib.sha256(sb).hexdigest())
        self.assertEqual(hashlib.sha256(sa).hexdigest(), hashlib.sha256(sb).hexdigest())
        self.assertLess(len(json.dumps(a, indent=2).encode()), 100_000)
        self.assertGreaterEqual(len(a["pack"]["burgs"]), 2)
        self.assertGreaterEqual(len(a["pack"]["provinces"]), 2)
        self.assertEqual(len(a["pack"]["rivers"]), 1)
        self.assertEqual(len(a["pack"]["routes"]), 1)
        self.assertEqual(len(a["pack"]["markers"]), 1)
        self.assertEqual(a["pack"]["routes"][0]["feature"], 0)


    def test_slice_retains_required_structures(self):
        result = make_slice(fixture(), 1, 1)
        cells = result["pack"]["cells"]
        self.assertGreaterEqual(len(cells), 2)
        self.assertEqual(result["pack"]["features"][0], 0)
        self.assertEqual(result["pack"]["burgs"][0], 0)
        self.assertEqual(result["pack"]["provinces"][0], 0)
        self.assertTrue(any(neighbors for cell in cells for neighbors in [cell.get("c", [])]))
        self.assertTrue(any(isinstance(cell.get("g"), int) for cell in cells))
        self.assertEqual(len(result["pack"]["rivers"]), 1)
        self.assertGreaterEqual(len([x for x in result["pack"]["rivers"][0]["cells"] if x >= 0]), 2)
        self.assertIn(-1, result["pack"]["rivers"][0]["cells"])
        self.assertEqual(len(result["pack"]["routes"]), 1)
        self.assertEqual(len(result["pack"]["markers"]), 1)
        self.assertTrue(any(state.get("neighbors") for state in result["pack"]["states"]))
        self.assertTrue(any(state.get("diplomacy") for state in result["pack"]["states"]))
        grid_ids = [cell["g"] for cell in cells if isinstance(cell.get("g"), int)]
        self.assertLess(len(set(grid_ids)), len(grid_ids))

    def test_write_slice_emits_clean_json_and_remap_sidecar(self):
        result = make_slice(fixture(), 1, 1)
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "slice.json"
            size, sidecar = write_slice(result, output)
            written = json.loads(output.read_text())
            remap = json.loads(sidecar.read_text())
            self.assertEqual(size, output.stat().st_size)
            self.assertNotIn("_worldloom_slice", written)
            self.assertIsInstance(written["settings"], dict)
            self.assertIsInstance(written["nameBases"], list)
            self.assertIn("cell_map", remap)
            self.assertLess(size, 100_000)

    def test_references_and_offsets_are_valid(self):
        result = make_slice(fixture(), 1, 1)
        refs = verify_slice(result)
        self.assertTrue(all(value["oob"] == 0 for value in refs.values()))
        self.assertEqual(result["pack"]["burgs"][0], 0)
        self.assertEqual(result["pack"]["burgs"][1]["i"], 1)
        self.assertEqual(result["pack"]["provinces"][0], 0)
        self.assertEqual(result["pack"]["provinces"][1]["i"], 1)
        self.assertEqual(result["pack"]["routes"][0]["points"][0][2], 0)

if __name__ == "__main__":
    unittest.main()
