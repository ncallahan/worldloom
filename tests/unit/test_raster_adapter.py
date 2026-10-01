from dataclasses import replace
from inspect import getsource
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from worldloom.adapters import RasterTerrainAdapter
from worldloom.core import WorldState
from worldloom.interfaces import SimulationConfig, SimulationContext
from worldloom.modules import (
    HydrologyModule,
    SettlementResolutionModule,
    SettlementSuitabilityModule,
    TerrainModule,
)
from worldloom.simulation import SimulationEngine


def write_test_raster(path: Path, low_location: tuple[int, int] = (5, 5)) -> None:
    elevation = np.full((10, 10), 9.0, dtype="float32")
    y, x = low_location
    elevation[y, x] = 4.0

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(10.0, 20.0, 0.5, 0.5),
    ) as dataset:
        dataset.write(elevation, 1)


def make_adapter_terrain_module(source: Path):
    class AdapterTerrainModule:
        spec = replace(TerrainModule.spec, name="prototype.terrain")

        def run(self, world: WorldState, context: SimulationContext) -> None:
            RasterTerrainAdapter(source, source_id="test://terrain.tif").load(
                world,
                time=context.time,
            )

    return AdapterTerrainModule()


def make_adapter_pipeline(source: Path) -> SimulationEngine:
    return SimulationEngine(
        (
            make_adapter_terrain_module(source),
            HydrologyModule(),
            SettlementSuitabilityModule(),
            SettlementResolutionModule(),
        ),
        SimulationConfig(time_unit="days"),
    )


def test_raster_adapter_imports_elevation_and_spatial_metadata(tmp_path: Path):
    source = tmp_path / "terrain.tif"
    write_test_raster(source)
    world = WorldState()

    RasterTerrainAdapter(source, source_id="test://terrain.tif").load(world, time=1847)

    assert world.fields["terrain.elevation"][5][5] == 4.0
    provenance = world.provenance["field:terrain.elevation"]
    assert provenance.producer == "adapter.rasterio.terrain"
    assert provenance.configuration["source"] == "test://terrain.tif"
    assert provenance.configuration["shape"] == [10, 10]
    assert provenance.configuration["crs"] == "EPSG:4326"
    assert provenance.configuration["transform"] == (0.5, 0.0, 10.0, 0.0, -0.5, 20.0, 0.0, 0.0, 1.0)
    assert provenance.time == 1847
    grid = world.spatial_fields["terrain.elevation"]
    assert grid.shape == (10, 10)
    assert grid.crs == "EPSG:4326"
    assert grid.bounds() == (10.0, 15.0, 15.0, 20.0)
    assert world.field_cell_center("terrain.elevation", 5, 5) == (12.75, 17.25)


def test_raster_adapter_reads_only_the_first_band(tmp_path: Path):
    source = tmp_path / "multiband.tif"
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        height=1,
        width=2,
        count=2,
        dtype="float32",
    ) as dataset:
        dataset.write(np.array([[7.0, 8.0]], dtype="float32"), 1)
        dataset.write(np.array([[90.0, 91.0]], dtype="float32"), 2)

    world = WorldState()
    RasterTerrainAdapter(source).load(world)

    assert world.fields["terrain.elevation"] == [[7.0, 8.0]]
    assert world.spatial_fields["terrain.elevation"].shape == (1, 2)


def test_existing_downstream_modules_have_no_raster_dependency():
    hydrology_source = getsource(HydrologyModule)
    suitability_source = getsource(SettlementSuitabilityModule)

    assert "rasterio" not in hydrology_source
    assert "RasterTerrainAdapter" not in hydrology_source
    assert "rasterio" not in suitability_source
    assert "RasterTerrainAdapter" not in suitability_source


def test_adapter_is_in_the_causal_path_through_settlement_resolution(tmp_path: Path):
    source_a = tmp_path / "terrain-a.tif"
    source_b = tmp_path / "terrain-b.tif"
    write_test_raster(source_a, low_location=(5, 5))
    write_test_raster(source_b, low_location=(2, 2))

    world_a = WorldState()
    world_b = WorldState()
    make_adapter_pipeline(source_a).run(world_a, SimulationContext(time=12))
    make_adapter_pipeline(source_b).run(world_b, SimulationContext(time=12))

    assert world_a.fields["hydrology.water"] != world_b.fields["hydrology.water"]
    assert world_a.observations["settlement.suitability"] != world_b.observations[
        "settlement.suitability"
    ]
    assert world_a.entities["settlement:001"]["location"] != world_b.entities[
        "settlement:001"
    ]["location"]
    assert world_a.events[0].data["location"] != world_b.events[0].data["location"]


def test_adapter_pipeline_is_deterministic(tmp_path: Path):
    source = tmp_path / "terrain.tif"
    write_test_raster(source, low_location=(5, 5))

    world_a = WorldState()
    world_b = WorldState()
    context = SimulationContext(time=12)
    make_adapter_pipeline(source).run(world_a, context)
    make_adapter_pipeline(source).run(world_b, context)

    assert world_a.fields == world_b.fields
    assert world_a.observations == world_b.observations
    assert world_a.entities == world_b.entities
    assert world_a.events == world_b.events
    assert world_a.provenance == world_b.provenance


def test_existing_production_vertical_slice_remains_covered(tmp_path: Path):
    source = tmp_path / "terrain.tif"
    write_test_raster(source)

    world = WorldState()
    make_adapter_pipeline(source).run(world, SimulationContext(time=1847))

    assert "terrain.elevation" in world.fields
    assert "hydrology.water" in world.fields
    assert "settlement.suitability" in world.observations
    assert "settlement:001" in world.entities
    assert world.events[0].kind == "settlement.founded"


def test_downstream_module_can_use_spatial_meaning_without_raster_dependency(tmp_path: Path):
    source = tmp_path / "terrain.tif"
    write_test_raster(source, low_location=(2, 7))

    class CellLocationModule:
        spec = replace(TerrainModule.spec, name="test.cell_location")

        def run(self, world: WorldState, context: SimulationContext) -> None:
            location = world.field_cell_center("terrain.elevation", 2, 7)
            world.set_observation(
                "test.low_cell_location",
                location,
            )

    world = WorldState()
    make_adapter_pipeline(source).run(world, SimulationContext(time=12))
    CellLocationModule().run(world, SimulationContext(time=12))

    assert world.observations["test.low_cell_location"] == (13.75, 18.75)


def test_non_spatial_fields_remain_plain_values():
    world = WorldState()
    world.set_field("temperature", 21.5)

    assert world.fields["temperature"] == 21.5
    assert "temperature" not in world.spatial_fields


def test_spatial_semantics_are_captured_and_restored_with_snapshots():
    world = WorldState()
    from worldloom.core import SpatialGrid

    world.set_field(
        "terrain.elevation",
        [[1.0]],
        spatial=SpatialGrid(
            shape=(1, 1),
            crs="EPSG:4326",
            transform=(1.0, 0.0, 10.0, 0.0, -1.0, 20.0),
        ),
    )
    snapshot = world.snapshot()
    world.spatial_fields.clear()

    world.restore(snapshot)

    assert world.field_cell_center("terrain.elevation", 0, 0) == (10.5, 19.5)
