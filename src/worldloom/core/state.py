"""Minimal in-memory canonical world state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .events import Event
from .provenance import Provenance


@dataclass
class WorldState:
    """Authoritative state plus explicitly separate derived observations."""

    fields: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    observations: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Provenance] = field(default_factory=dict)

    def set_field(self, name: str, value: Any, provenance: Provenance | None = None) -> None:
        self.fields[name] = value
        if provenance is not None:
            self.provenance[f"field:{name}"] = provenance

    def set_observation(
        self, name: str, value: Any, provenance: Provenance | None = None
    ) -> None:
        self.observations[name] = value
        if provenance is not None:
            self.provenance[f"observation:{name}"] = provenance

    def add_entity(
        self,
        entity_id: str,
        value: dict[str, Any],
        provenance: Provenance | None = None,
    ) -> None:
        if entity_id in self.entities:
            raise ValueError(f"Entity already exists: {entity_id}")
        self.entities[entity_id] = value
        if provenance is not None:
            self.provenance[f"entity:{entity_id}"] = provenance

    def record_event(self, event: Event) -> None:
        self.events.append(event)

    def snapshot(self) -> dict[str, Any]:
        return {
            "fields": self.fields.copy(),
            "entities": self.entities.copy(),
            "events": self.events.copy(),
            "observations": self.observations.copy(),
            "provenance": self.provenance.copy(),
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        self.fields = snapshot["fields"].copy()
        self.entities = snapshot["entities"].copy()
        self.events = snapshot["events"].copy()
        self.observations = snapshot["observations"].copy()
        self.provenance = snapshot["provenance"].copy()
