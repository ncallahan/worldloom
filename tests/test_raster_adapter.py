from pathlib import Path

import rasterio
from rasterio.transform import from_origin

from worldloom.adapters import RasterTerrainAdapter
from worldloom.core import WorldState


def write_test_raster(path: Path) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=3,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(10.0, 20.0, 0.5, 0.5),
    ) as dataset:
        dataset.write([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], 1)


def test_raster_adapter_imports_elevation_into_canonical_state(tmp_path: Path):
    source = tmp_path / "terrain.tif"
    write_test_raster(source)
    world = WorldState()

    RasterTerrainAdapter(source, source_id="test://terrain.tif").load(world, time=1847)

    assert world.fields["terrain.elevation"] == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    provenance = world.provenance["field:terrain.elevation"]
    assert provenance.producer == "adapter.rasterio.terrain"
    assert provenance.configuration["source"] == "test://terrain.tif"
    assert provenance.configuration["shape"] == [2, 3]
    assert provenance.configuration["crs"] == "EPSG:4326"
    assert provenance.time == 1847


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
        dataset.write([[7.0, 8.0]], 1)
        dataset.write([[90.0, 91.0]], 2)

    world = WorldState()
    RasterTerrainAdapter(source).load(world)

    assert world.fields["terrain.elevation"] == [[7.0, 8.0]]
