import json
from pathlib import Path

import numpy as np
import rasterio

from worldloom.core import derive_entity_id

from worldloom.config import load_run_config
from worldloom.runner import execute_run


def test_json_run_config_reproduces_prototype(tmp_path: Path):
    config_path = tmp_path / "prototype.json"
    config_path.write_text(
        json.dumps(
            {
                "simulation": {
                    "time_unit": "days",
                    "start": 0,
                    "end": 10,
                },
                "modules": [
                    {
                        "module": "prototype.terrain",
                        "config": {
                            "spatial_grid": {
                                "shape": [10, 10],
                                "crs": "EPSG:4326",
                                "transform": [0.5, 0, 10, 0, -0.5, 20],
                            }
                        },
                    },
                    {"module": "prototype.hydrology"},
                    {"module": "prototype.settlement_suitability"},
                    {"module": "prototype.settlement_resolution"},
                ],
                "outputs": [
                    {
                        "adapter": "geotiff",
                        "path": "world.tif",
                        "fields": [
                            "terrain.elevation",
                            "hydrology.water",
                            "settlement.suitability",
                        ],
                        "reference_field": "terrain.elevation",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    config = load_run_config(config_path)
    world = execute_run(config)

    assert derive_entity_id("settlement", "question:settlement.founding", "role:founding", "slot:001") in world.entities
    assert world.entities[derive_entity_id("settlement", "question:settlement.founding", "role:founding", "slot:001")]["location"] == (4, 2)

    output = tmp_path / "world.tif"
    assert output.exists()

    with rasterio.open(output) as dataset:
        assert dataset.count == 3
        assert dataset.descriptions == (
            "terrain.elevation",
            "hydrology.water",
            "settlement.suitability",
        )
        assert np.array_equal(
            dataset.read(1),
            np.asarray(world.fields["terrain.elevation"]),
        )


def test_module_configuration_is_not_inter_module_wiring(tmp_path: Path):
    config_path = tmp_path / "minimal.json"
    config_path.write_text(
        json.dumps(
            {
                "simulation": {"time_unit": "days", "start": 0, "end": 0},
                "modules": [
                    {
                        "module": "prototype.terrain",
                        "config": {
                            "spatial_grid": {
                                "shape": [10, 10],
                                "crs": "EPSG:4326",
                                "transform": [1, 0, 0, 0, -1, 0],
                            }
                        },
                    },
                    {"module": "prototype.hydrology"},
                ],
            }
        ),
        encoding="utf-8",
    )

    world = execute_run(load_run_config(config_path))

    assert "terrain.elevation" in world.fields
    assert "hydrology.water" in world.fields
