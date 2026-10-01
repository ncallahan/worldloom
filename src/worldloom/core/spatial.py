"""Minimal spatial semantics for grid-backed world fields.

This module intentionally avoids a dependency on Rasterio or another GIS
implementation. It describes the spatial meaning required by Worldloom for a
grid-backed field and provides the smallest useful coordinate operation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpatialGrid:
    """Spatial meaning for a two-dimensional field.

    The transform uses six affine coefficients (a, b, c, d, e, f) mapping a
    zero-based grid column/row coordinate to the corresponding world coordinate
    at the cell corner:

        x = a * column + b * row + c
        y = d * column + e * row + f

    Cell coordinates exposed by cell_center refer to cell centres. The
    representation is deliberately small and independent of any GIS library.
    """

    shape: tuple[int, int]
    crs: str | None
    transform: tuple[float, float, float, float, float, float]

    def __post_init__(self) -> None:
        if len(self.shape) != 2 or any(size <= 0 for size in self.shape):
            raise ValueError("SpatialGrid shape must contain two positive dimensions")
        if len(self.transform) != 6:
            raise ValueError("SpatialGrid transform must contain six affine coefficients")

    def cell_center(self, row: int, column: int) -> tuple[float, float]:
        """Return the world coordinate of a cell centre."""
        height, width = self.shape
        if not 0 <= row < height or not 0 <= column < width:
            raise IndexError("Grid cell is outside the spatial grid")

        a, b, c, d, e, f = self.transform
        column_center = column + 0.5
        row_center = row + 0.5
        return (
            a * column_center + b * row_center + c,
            d * column_center + e * row_center + f,
        )

    def bounds(self) -> tuple[float, float, float, float]:
        """Return an axis-aligned bounding box around the grid corners."""
        height, width = self.shape
        a, b, c, d, e, f = self.transform
        corners = (
            (c, f),
            (a * width + c, d * width + f),
            (b * height + c, e * height + f),
            (a * width + b * height + c, d * width + e * height + f),
        )
        xs = [corner[0] for corner in corners]
        ys = [corner[1] for corner in corners]
        return min(xs), min(ys), max(xs), max(ys)
