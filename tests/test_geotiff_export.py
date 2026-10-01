from pathlib import Path

import numpy as np
import rasterio

from worldloom.adapters import export_world_rasters
from worldloom.core import SpatialGrid, WorldState
from worldloom.interfaces import SimulationConfig, SimulationContext
from worldloom.modules import (
    HydrologyModule,
    SettlementResolutionModule,
    SettlementSuitabilityModule,
    TerrainModule,
)
from worldloom.simulation import SimulationEngine


def make_world() -> WorldState:
    world = WorldState()
    grid = SpatialGrid(
        shape=(10, 10),
        crs="EPSG:4326",
        transform=(0.5, 0.0, 10.0, 0.0, -0.5, 20.0),
    )
    SimulationEngine(
        (
            TerrainModule(spatial_grid=grid),
            HydrologyModule(),
            SettlementSuitabilityModule(),
            SettlementResolutionModule(),
        ),
        SimulationConfig(time_unit="days"),
    ).run(world)
    return world


def test_prototype_pipeline_exports_gis_ready_geotiff(tmp_path: Path):
    world = make_world()
    output = tmp_path / "worldloom-map.tif"

    export_world_rasters(
        world,
        output,
        (
            "terrain.elevation",
            "hydrology.water",
            "settlement.suitability",
        ),
        reference_field="terrain.elevation",
    )

    with rasterio.open(output) as dataset:
        assert dataset.driver == "GTiff"
        assert dataset.width == 10
        assert dataset.height == 10
        assert dataset.count == 3
        assert dataset.crs.to_string() == "EPSG:4326"
        assert tuple(dataset.transform) == (
            0.5,
            0.0,
            10.0,
            0.0,
            -0.5,
            20.0,
            0.0,
            0.0,
            1.0,
        )
        assert dataset.descriptions == (
            "terrain.elevation",
            "hydrology.water",
            "settlement.suitability",
        )

        elevation = dataset.read(1)
        water = dataset.read(2)
        suitability = dataset.read(3)

    assert np.array_equal(elevation, np.asarray(world.fields["terrain.elevation"]))
    assert np.array_equal(water, np.asarray(world.fields["hydrology.water"], dtype=np.float32))
    expected_suitability = np.full((10, 10), np.nan, dtype=np.float32)
    for (x, y), score in world.observations["settlement.suitability"].items():
        expected_suitability[y, x] = score
    assert np.allclose(suitability, expected_suitability, equal_nan=True)


def test_export_uses_reference_spatial_semantics_without_mutating_state(tmp_path: Path):
    world = make_world()
    before = world.snapshot()
    output = tmp_path / "worldloom-map.tif"

    export_world_rasters(
        world,
        output,
        ("settlement.suitability",),
        reference_field="terrain.elevation",
    )

    assert world.snapshot() == before
    assert "settlement.suitability" not in world.spatial_fields
