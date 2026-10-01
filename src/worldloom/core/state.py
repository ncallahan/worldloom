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
    """A point-in-time snapshot of a world.

    The snapshot stores the full world state, including observations, with deep-copy
    isolation so mutations in one world do not leak into another. Metadata is optional
    and may be used to record execution context without making it mandatory.
    """

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
        """Return a stable digest for arbitrary world data.

        This is intentionally lightweight and deterministic. The hash is a foundation for
        later provenance and invalidation work without locking in a full versioning model.
        """
        payload = json.dumps(
            _normalise_for_hash(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _with_fingerprint(
        self, value: Any, provenance: Provenance | None
    ) -> Provenance | None:
        if provenance is None or provenance.fingerprint is not None:
            return provenance
        return replace(provenance, fingerprint=self.fingerprint(value))

    def set_field(self, name: str, value: Any, provenance: Provenance | None = None) -> None:
        provenance = self._with_fingerprint(value, provenance)
        self.fields[name] = value
        if provenance is not None:
            self.provenance[f"field:{name}"] = provenance

    def set_observation(
        self, name: str, value: Any, provenance: Provenance | None = None
    ) -> None:
        provenance = self._with_fingerprint(value, provenance)
        self.observations[name] = value
        if provenance is not None:
            self.provenance[f"observation:{name}"] = provenance

    def add_entity(
        self,
        entity_id: str,
        value: dict[str, Any],
        provenance: Provenance | None = None,
    ) -> None:
        provenance = self._with_fingerprint(value, provenance)
        if entity_id in self.entities:
            raise ValueError(f"Entity already exists: {entity_id}")
        self.entities[entity_id] = value
        if provenance is not None:
            self.provenance[f"entity:{entity_id}"] = provenance

    def record_event(self, event: Event) -> None:
        self.events.append(event)

    def snapshot(self, metadata: dict[str, Any] | None = None) -> WorldSnapshot:
        """Return a deep-copied snapshot of the current world state.

        Observations are retained in the snapshot so callers can preserve execution state
        and cached derived values when they need them. Metadata is optional and may be
        used to annotate the snapshot with context such as simulation time or settings.
        """
        return WorldSnapshot(
            fields=deepcopy(self.fields),
            entities=deepcopy(self.entities),
            events=deepcopy(self.events),
            observations=deepcopy(self.observations),
            provenance=deepcopy(self.provenance),
            metadata=deepcopy(metadata) if metadata is not None else {},
        )

    def restore(self, snapshot: WorldSnapshot) -> None:
        """Restore a previously captured snapshot.

        The restore operation is intentionally agnostic about context: callers may decide
        whether to include simulation metadata, but the restore itself only reinstates the
        stored world state.
        """
        self.fields = deepcopy(snapshot.fields)
        self.entities = deepcopy(snapshot.entities)
        self.events = deepcopy(snapshot.events)
        self.observations = deepcopy(snapshot.observations)
        self.provenance = deepcopy(snapshot.provenance)
