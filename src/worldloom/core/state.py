"""Minimal in-memory canonical world state."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any

from .events import Event
from .hashing import fingerprint
from .provenance import Provenance
from .spatial import SpatialGrid


@dataclass(frozen=True)
class WorldSnapshot:
    """A point-in-time snapshot of a world."""

    fields: dict[str, Any]
    entities: dict[str, dict[str, Any]]
    events: list[Event]
    observations: dict[str, Any]
    provenance: dict[str, Provenance]
    metadata: dict[str, Any] = field(default_factory=dict)
    spatial_fields: dict[str, SpatialGrid] = field(default_factory=dict)


@dataclass
class WorldState:
    """Authoritative state plus explicitly separate derived observations."""

    fields: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    observations: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Provenance] = field(default_factory=dict)
    spatial_fields: dict[str, SpatialGrid] = field(default_factory=dict)

    @staticmethod
    def fingerprint(value: Any) -> str:
        """Return a stable digest for supported nested world data."""
        return fingerprint(value)

    def _with_fingerprint(self, value: Any, provenance: Provenance | None):
        if provenance is None or provenance.fingerprint is not None:
            return provenance
        return replace(provenance, fingerprint=self.fingerprint(value))

    def set_field(
        self,
        name: str,
        value: Any,
        provenance: Provenance | None = None,
        *,
        spatial: SpatialGrid | None = None,
    ) -> None:
        stored = deepcopy(value)
        self.fields[name] = stored
        provenance = self._with_fingerprint(stored, provenance)
        if provenance is not None:
            self.provenance[f"field:{name}"] = provenance
        if spatial is not None:
            self.spatial_fields[name] = spatial

    def field_cell_center(self, field_name: str, row: int, column: int) -> tuple[float, float]:
        """Return a spatial field cell's world coordinate without GIS dependencies."""
        try:
            grid = self.spatial_fields[field_name]
        except KeyError as exc:
            raise KeyError(f"Field has no spatial semantics: {field_name}") from exc
        return grid.cell_center(row, column)

    def set_observation(self, name: str, value: Any, provenance: Provenance | None = None) -> None:
        stored = deepcopy(value)
        self.observations[name] = stored
        provenance = self._with_fingerprint(stored, provenance)
        if provenance is not None:
            self.provenance[f"observation:{name}"] = provenance

    def add_entity(self, entity_id: str, value: dict[str, Any], provenance: Provenance | None = None) -> None:
        if entity_id in self.entities:
            raise ValueError(f"Entity already exists: {entity_id}")
        stored = deepcopy(value)
        self.entities[entity_id] = stored
        provenance = self._with_fingerprint(stored, provenance)
        if provenance is not None:
            self.provenance[f"entity:{entity_id}"] = provenance

    def record_event(self, event: Event) -> None:
        self.events.append(event)

    def snapshot(self, metadata: dict[str, Any] | None = None) -> WorldSnapshot:
        return WorldSnapshot(
            fields=deepcopy(self.fields), entities=deepcopy(self.entities),
            events=deepcopy(self.events), observations=deepcopy(self.observations),
            provenance=deepcopy(self.provenance),
            metadata=deepcopy(metadata) if metadata is not None else {},
            spatial_fields=deepcopy(self.spatial_fields),
        )

    def restore(self, snapshot: WorldSnapshot) -> None:
        self.fields = deepcopy(snapshot.fields)
        self.entities = deepcopy(snapshot.entities)
        self.events = deepcopy(snapshot.events)
        self.observations = deepcopy(snapshot.observations)
        self.provenance = deepcopy(snapshot.provenance)
        self.spatial_fields = deepcopy(snapshot.spatial_fields)
