"""First-class simulation events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    """A persistent occurrence in simulated history."""

    kind: str
    time: float
    data: dict[str, Any] = field(default_factory=dict)
