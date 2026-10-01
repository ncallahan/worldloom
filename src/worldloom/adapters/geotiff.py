"""GeoTIFF export adapter for Worldloom raster state."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np
import rasterio
from rasterio.transform import Affine

from worldloom.core import WorldState


def _as_raster(value: Any, shape: tuple[int, int], name: str) -> np.ndarray:
    """Convert a Worldloom raster-like value into a 2D numeric array."""
    if isinstance(value, dict):
        raster = np.full(shape, np.nan, dtype="float32")
        for key, item in value.items():
            if not isinstance(key, tuple) or len(key) != 2:
                raise ValueError(f"Observation '{name}' is not indexed by (x, y) cells")
            x, y = key
            if not isinstance(x, int) or not isinstance(y, int):
                raise ValueError(f"Observation '{name}' has a non-integer cell index")
            if not 0 <= y < shape[0] or not 0 <= x < shape[1]:
                raise ValueError(f"Observation '{name}' contains a cell outside {shape}")
            raster[y, x] = float(item)
        return raster

    raster = np.asarray(value)
    if raster.ndim != 2 or tuple(raster.shape) != shape:
        raise ValueError(
            f"Raster '{name}' has shape {tuple(raster.shape)}; expected {shape}"
        )
    if not np.issubdtype(raster.dtype, np.number) and raster.dtype != np.bool_:
        raise TypeError(f"Raster '{name}' must contain numeric or boolean values")
    return raster.astype("float32", copy=False)


def export_world_rasters(
    world: WorldState,
    path: str | Path,
    names: Sequence[str],
    *,
    reference_field: str,
) -> None:
    """Export selected fields/observations as bands in a small GeoTIFF.

    reference_field supplies the spatial semantics for the exported map.
    This keeps the exporter as a projection boundary: an observation can be
    rendered on a known grid without pretending that the observation itself
    has become canonical spatial state.
    """
    if not names:
        raise ValueError("At least one raster name must be supplied")

    try:
        grid = world.spatial_fields[reference_field]
    except KeyError as exc:
        raise KeyError(
            f"Reference field has no spatial semantics: {reference_field}"
        ) from exc

    arrays = []
    for name in names:
        if name in world.fields:
            value = world.fields[name]
        elif name in world.observations:
            value = world.observations[name]
        else:
            raise KeyError(f"Worldloom value not found: {name}")
        arrays.append((name, _as_raster(value, grid.shape, name)))

    transform = Affine(*grid.transform)
    profile = {
        "driver": "GTiff",
        "height": grid.shape[0],
        "width": grid.shape[1],
        "count": len(arrays),
        "dtype": "float32",
        "transform": transform,
        "crs": grid.crs,
    }

    with rasterio.open(Path(path), "w", **profile) as dataset:
        for band_number, (name, array) in enumerate(arrays, start=1):
            dataset.write(array, band_number)
            dataset.set_band_description(band_number, name)
