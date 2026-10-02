"""Provisional hierarchical addresses for deterministic world experiments.

This module is experimental and does not define Worldloom's final identifier,
tile, or spatial-data architecture.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, unquote

_SAFE_SEGMENT = "-._~"
_SEPARATOR = "/"
_CELL_PREFIX = "cell"


@dataclass(frozen=True)
class Address:
    """Immutable, hashable hierarchical address.

    Grid-cell addresses use zero-based (row, column) coordinates. Existing
    Worldloom observation keys that use (x, y) are intentionally unchanged.
    """

    segments: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.segments, tuple):
            raise TypeError("Address segments must be a tuple")
        if any(not isinstance(segment, str) for segment in self.segments):
            raise TypeError("Address segments must be strings")
        if any(segment == "" for segment in self.segments):
            raise ValueError("Address segments must not be empty")

    @property
    def canonical(self) -> str:
        """Return the canonical escaped path representation."""
        if not self.segments:
            return _SEPARATOR
        return _SEPARATOR + _SEPARATOR.join(
            quote(segment, safe=_SAFE_SEGMENT) for segment in self.segments
        )

    @classmethod
    def parse(cls, value: str) -> "Address":
        """Parse a canonical address string."""
        if not isinstance(value, str):
            raise TypeError("Address must be parsed from a string")
        if value == _SEPARATOR:
            return cls(())
        if not value.startswith(_SEPARATOR) or value.endswith(_SEPARATOR):
            raise ValueError("Address must use a canonical slash-prefixed path")
        raw_segments = value[1:].split(_SEPARATOR)
        segments = tuple(unquote(segment) for segment in raw_segments)
        if any(segment == "" for segment in segments):
            raise ValueError("Address segments must not be empty")
        canonical = cls(segments)
        if canonical.canonical != value:
            raise ValueError("Address is not in canonical form")
        return canonical

    def parent(self) -> "Address":
        """Return the containing address."""
        if not self.segments:
            raise ValueError("Root address has no parent")
        return Address(self.segments[:-1])

    def child(self, segment: str) -> "Address":
        """Return a child address with one additional segment."""
        if not isinstance(segment, str):
            raise TypeError("Address child segment must be a string")
        if not segment:
            raise ValueError("Address child segment must not be empty")
        return Address(self.segments + (segment,))

    @classmethod
    def cell(cls, row: int, column: int) -> "Address":
        """Return an address for a zero-based (row, column) grid cell."""
        _validate_cell_coordinate(row, "row")
        _validate_cell_coordinate(column, "column")
        return cls((_CELL_PREFIX, str(row), str(column)))

    def as_cell(self) -> tuple[int, int]:
        """Return a cell address as a zero-based (row, column) pair."""
        if len(self.segments) != 3 or self.segments[0] != _CELL_PREFIX:
            raise ValueError("Address is not a grid-cell address")
        row, column = self.segments[1:]
        try:
            row_value = int(row)
            column_value = int(column)
        except ValueError as exc:
            raise ValueError("Cell address contains non-integer coordinates") from exc
        _validate_cell_coordinate(row_value, "row")
        _validate_cell_coordinate(column_value, "column")
        if (str(row_value), str(column_value)) != (row, column):
            raise ValueError("Cell address is not canonical")
        return row_value, column_value

    def __str__(self) -> str:
        return self.canonical


def _validate_cell_coordinate(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def xy_to_row_column(x: int, y: int) -> tuple[int, int]:
    """Convert existing (x, y) cell keys to Worldloom's (row, column) form."""
    _validate_cell_coordinate(x, "x")
    _validate_cell_coordinate(y, "y")
    return y, x


def row_column_to_xy(row: int, column: int) -> tuple[int, int]:
    """Convert Worldloom's (row, column) form to existing (x, y) cell keys."""
    _validate_cell_coordinate(row, "row")
    _validate_cell_coordinate(column, "column")
    return column, row
