"""Provenance records for derived world facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Provenance:
    """Records where a world fact came from."""

    producer: str
    inputs: tuple[str, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)
    time: float = 0.0
    fingerprint: str | None = None
