"""Minimal in-memory canonical world state."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any, Iterable

from .events import Event
from .provenance import Provenance
from .spatial import SpatialGrid


def _normalise_for_hash(value: Any) -> Any:
    """Normalise the supported world-data domain for deterministic hashing.

    Supported values are JSON-like scalars, lists/tuples, sets, and dictionaries
    with supported keys. Unsupported objects raise TypeError rather than falling
    back to an object's potentially process-dependent repr().
    """
    if isinstance(value, dict):
        entries = [
            [_normalise_for_hash(key), _normalise_for_hash(item)]
            for key, item in value.items()
        ]
        return sorted(
            entries,
            key=lambda entry: json.dumps(entry[0], sort_keys=True, separators=(",", ":")),
        )
    if isinstance(value, (list, tuple)):
        return [_normalise_for_hash(item) for item in value]
    if isinstance(value, set):
        normalised = [_normalise_for_hash(item) for item in value]
        return sorted(
            normalised,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"Unsupported value type for fingerprinting: {type(value).__name__}")


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
    _declared_outputs: frozenset[str] | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    @staticmethod
    def fingerprint(value: Any) -> str:
        """Return a stable digest for supported nested world data."""
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

    def _begin_module_execution(self, module_name: str, outputs: Iterable[Any]) -> None:
        """Enable provisional output enforcement for one module invocation."""
        self._declared_outputs = frozenset(output.name for output in outputs)

    def _end_module_execution(self) -> None:
        """Disable provisional output enforcement after a module invocation."""
        self._declared_outputs = None

    def _assert_declared_output(self, kind: str, name: str) -> None:
        """Reject writes not declared by the currently executing module."""
        if self._declared_outputs is None:
            return

        semantic_name = f"{kind}:{name}"
        if semantic_name in self._declared_outputs:
            return

        if kind == "entity":
            for declared in self._declared_outputs:
                if not declared.startswith("entity:"):
                    continue
                declared_id = declared.removeprefix("entity:")
                if name == declared_id or name.startswith(f"{declared_id}:"):
                    return

        raise ValueError(
            f"Module attempted undeclared {kind} output '{name}'"
        )

    def set_field(
        self,
        name: str,
        value: Any,
        provenance: Provenance | None = None,
        *,
        spatial: SpatialGrid | None = None,
    ) -> None:
        self._assert_declared_output("field", name)
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
        self._assert_declared_output("observation", name)
        stored = deepcopy(value)
        self.observations[name] = stored
        provenance = self._with_fingerprint(stored, provenance)
        if provenance is not None:
            self.provenance[f"observation:{name}"] = provenance

    def add_entity(self, entity_id: str, value: dict[str, Any], provenance: Provenance | None = None) -> None:
        self._assert_declared_output("entity", entity_id)
        if entity_id in self.entities:
            raise ValueError(f"Entity already exists: {entity_id}")
        stored = deepcopy(value)
        self.entities[entity_id] = stored
        provenance = self._with_fingerprint(stored, provenance)
        if provenance is not None:
            self.provenance[f"entity:{entity_id}"] = provenance

    def record_event(self, event: Event) -> None:
        self._assert_declared_output("event", event.kind)
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
