"""Raster terrain adapter built on Rasterio."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import rasterio

from worldloom.core import Provenance, SpatialGrid, WorldState


class RasterTerrainAdapter:
    """Load a single-band raster into canonical terrain elevation state.

    Rasterio remains responsible for raster decoding and geospatial metadata.
    Worldloom receives only the canonical elevation values; source metadata is
    retained in provenance rather than becoming a new GIS-specific state model.
    """

    producer = "adapter.rasterio.terrain"

    def __init__(self, path: str | Path, source_id: str | None = None) -> None:
        self.path = Path(path)
        self.source_id = source_id or str(self.path)

    def load(
        self,
        world: WorldState,
        *,
        field_name: str = "terrain.elevation",
        time: float = 0.0,
    ) -> None:
        """Load the first raster band into a canonical Worldloom field."""
        with rasterio.open(self.path) as dataset:
            if dataset.count < 1:
                raise ValueError("Raster terrain source must contain at least one band")

            elevation = dataset.read(1).tolist()
            shape = (dataset.height, dataset.width)
            crs = dataset.crs.to_string() if dataset.crs else None
            transform = (
                dataset.transform.a,
                dataset.transform.b,
                dataset.transform.c,
                dataset.transform.d,
                dataset.transform.e,
                dataset.transform.f,
            )
            configuration: dict[str, Any] = {
                "source": self.source_id,
                "shape": list(shape),
                "crs": crs,
                "transform": tuple(dataset.transform),
            }

        world.set_field(
            field_name,
            elevation,
            Provenance(
                self.producer,
                configuration=configuration,
                time=time,
            ),
            spatial=SpatialGrid(
                shape=shape,
                crs=crs,
                transform=transform,
            ),
        )
