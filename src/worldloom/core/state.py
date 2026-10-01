"""Minimal in-memory canonical world state."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any

from .events import Event
from .provenance import Provenance


def _normalise_for_hash(value: Any) -> Any:
    """Convert nested Python data into a stable JSON-compatible form."""
    if isinstance(value, dict):
        return {
            str(key): _normalise_for_hash(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_normalise_for_hash(item) for item in value]
    if isinstance(value, set):
        return sorted(_normalise_for_hash(item) for item in value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


@dataclass(frozen=True)
class WorldSnapshot:
    """A point-in-time snapshot of a world."""

    fields: dict[str, Any]
    entities: dict[str, dict[str, Any]]
    events: list[Event]
    observations: dict[str, Any]
    provenance: dict[str, Provenance]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldState:
    """Authoritative state plus explicitly separate derived observations."""

    fields: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    observations: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Provenance] = field(default_factory=dict)

    @staticmethod
    def fingerprint(value: Any) -> str:
        """Return a stable digest for nested world data."""
        payload = json.dumps(
            _normalise_for_hash(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _with_fingerprint(self, value: Any, provenance: Provenance | None):
        if provenance is None or provenance.fingerprint is not None:
            return provenance
        return replace(provenance, fingerprint=self.fingerprint(value))

    def set_field(self, name: str, value: Any, provenance: Provenance | None = None) -> None:
        self.fields[name] = value
        provenance = self._with_fingerprint(value, provenance)
        if provenance is not None:
            self.provenance[f"field:{name}"] = provenance

    def set_observation(self, name: str, value: Any, provenance: Provenance | None = None) -> None:
        self.observations[name] = value
        provenance = self._with_fingerprint(value, provenance)
        if provenance is not None:
            self.provenance[f"observation:{name}"] = provenance

    def add_entity(self, entity_id: str, value: dict[str, Any], provenance: Provenance | None = None) -> None:
        if entity_id in self.entities:
            raise ValueError(f"Entity already exists: {entity_id}")
        self.entities[entity_id] = value
        provenance = self._with_fingerprint(value, provenance)
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
        )

    def restore(self, snapshot: WorldSnapshot) -> None:
        self.fields = deepcopy(snapshot.fields)
        self.entities = deepcopy(snapshot.entities)
        self.events = deepcopy(snapshot.events)
        self.observations = deepcopy(snapshot.observations)
        self.provenance = deepcopy(snapshot.provenance)
