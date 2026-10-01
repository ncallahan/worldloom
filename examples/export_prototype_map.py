"""Generate the prototype world and export a GIS-ready GeoTIFF."""

from __future__ import annotations

import argparse
from pathlib import Path

from rasterio.transform import from_origin

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


def build_world() -> WorldState:
    """Run the existing prototype pipeline on a small georeferenced grid."""
    world = WorldState()
    grid = SpatialGrid(
        shape=(10, 10),
        crs="EPSG:4326",
        transform=tuple(from_origin(10.0, 20.0, 0.5, 0.5)),
    )

    TerrainModule(spatial_grid=grid).run(world, SimulationContext(time=0))
    engine = SimulationEngine(
        (
            HydrologyModule(),
            SettlementSuitabilityModule(),
            SettlementResolutionModule(),
        ),
        SimulationConfig(time_unit="days"),
    )
    engine.run(world)
    return world


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Output GeoTIFF path")
    args = parser.parse_args()

    world = build_world()
    export_world_rasters(
        world,
        args.output,
        (
            "terrain.elevation",
            "hydrology.water",
            "settlement.suitability",
        ),
        reference_field="terrain.elevation",
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
