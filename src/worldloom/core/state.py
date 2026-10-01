"""Minimal in-memory canonical world state."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Any, Hashable, Iterable

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
    overlays: dict[str, dict[str, dict[Hashable, Any]]] = field(default_factory=dict)
    overlay_priorities: dict[str, dict[str, int]] = field(default_factory=dict)
    overlay_provenance: dict[str, dict[str, dict[Hashable, Provenance]]] = field(default_factory=dict)


@dataclass
class WorldState:
    """Authoritative state plus explicitly separate derived observations."""

    fields: dict[str, Any] = field(default_factory=dict)
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    observations: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Provenance] = field(default_factory=dict)
    spatial_fields: dict[str, SpatialGrid] = field(default_factory=dict)
    overlays: dict[str, dict[str, dict[Hashable, Any]]] = field(default_factory=dict)
    overlay_priorities: dict[str, dict[str, int]] = field(default_factory=dict)
    overlay_provenance: dict[str, dict[str, dict[Hashable, Provenance]]] = field(default_factory=dict)
    _declared_outputs: frozenset[str] | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )
    _declared_overlay_layers: dict[str, frozenset[str]] | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )
    _active_module_name: str | None = field(
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
        outputs = tuple(outputs)
        self._active_module_name = module_name
        self._declared_outputs = frozenset(output.name for output in outputs)
        declared_overlay_layers: dict[str, set[str]] = {}
        for output in outputs:
            layer = getattr(output, "layer", None)
            if layer is None:
                continue
            declared_overlay_layers.setdefault(output.name, set()).add(layer)
        self._declared_overlay_layers = {
            name: frozenset(layers)
            for name, layers in declared_overlay_layers.items()
        }

    def _end_module_execution(self) -> None:
        """Disable provisional output enforcement after a module invocation."""
        self._declared_outputs = None
        self._declared_overlay_layers = None
        self._active_module_name = None

    def _assert_declared_output_name(self, name: str) -> None:
        """Reject an output name not declared by the active module."""
        if self._declared_outputs is None:
            return
        if name not in self._declared_outputs:
            module = self._active_module_name or "<unknown>"
            raise ValueError(
                f"Module '{module}' attempted undeclared overlay output '{name}'"
            )

    def _assert_declared_overlay_layer(self, name: str, layer: str) -> None:
        """Reject overlay-layer writes not declared by the active module."""
        if self._declared_overlay_layers is None:
            return
        declared_layers = self._declared_overlay_layers.get(name)
        if declared_layers is None or layer not in declared_layers:
            module = self._active_module_name or "<unknown>"
            raise ValueError(
                f"Module '{module}' attempted undeclared layer '{layer}' "
                f"for overlay '{name}'"
            )

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

        module = self._active_module_name or "<unknown>"
        raise ValueError(
            f"Module '{module}' attempted undeclared {kind} output '{name}'"
        )

    def register_overlay(self, name: str, layers: dict[str, int]) -> None:
        """Register the fixed priority order for an overlay output."""
        if not layers:
            raise ValueError(f"Overlay '{name}' must have at least one layer")
        if len(set(layers.values())) != len(layers):
            raise ValueError(f"Overlay '{name}' has duplicate priorities")
        if any(isinstance(priority, bool) or not isinstance(priority, int) for priority in layers.values()):
            raise ValueError(f"Overlay '{name}' priorities must be integers")
        existing = self.overlay_priorities.get(name)
        if existing is not None and existing != layers:
            raise ValueError(f"Overlay '{name}' is already registered with different layers")
        self.overlay_priorities[name] = deepcopy(layers)
        self.overlays.setdefault(name, {layer: {} for layer in layers})
        self.overlay_provenance.setdefault(name, {layer: {} for layer in layers})

    def set_layer_value(
        self,
        name: str,
        layer: str,
        address: Hashable,
        value: Any,
        provenance: Provenance | None = None,
    ) -> None:
        """Store an overlay layer value without materialising it into fields."""
        self._assert_declared_output_name(name)
        self._assert_declared_overlay_layer(name, layer)
        if name not in self.overlay_priorities:
            raise ValueError(f"Overlay '{name}' is not registered")
        if layer not in self.overlay_priorities[name]:
            raise ValueError(f"Layer '{layer}' is not registered for overlay '{name}'")
        try:
            hash(address)
        except TypeError as exc:
            raise TypeError("Overlay address must be hashable") from exc
        stored = deepcopy(value)
        self.overlays[name][layer][address] = stored
        if provenance is not None:
            self.overlay_provenance[name][layer][address] = deepcopy(
                self._with_fingerprint(stored, provenance)
            )
        else:
            self.overlay_provenance[name][layer].pop(address, None)
        self._update_overlay_provenance(name, address)

    def _update_overlay_provenance(self, name: str, address: Hashable) -> None:
        """Record the current winner and contributing losing layers for an address."""
        available = [
            layer for layer, values in self.overlays[name].items() if address in values
        ]
        if not available:
            return
        winner = max(available, key=lambda layer: self.overlay_priorities[name][layer])
        # Address keys currently use repr() in the provenance namespace;
        # this is provisional until the identity scheme is settled.
        provenance_key = f"overlay:{name}:{address!r}"
        winner_provenance = self.overlay_provenance[name][winner].get(address)
        if winner_provenance is None:
            self.provenance.pop(provenance_key, None)
            return
        losers = sorted(
            (layer for layer in available if layer != winner),
            key=lambda layer: self.overlay_priorities[name][layer],
            reverse=True,
        )
        loser_producers = [
            self.overlay_provenance[name][layer][address].producer
            for layer in losers
            if address in self.overlay_provenance[name][layer]
        ]
        configuration = deepcopy(winner_provenance.configuration)
        configuration["_worldloom_overlay"] = {
            "layer": winner,
            "losing_layers": losers,
            "losing_producers": loser_producers,
        }
        self.provenance[provenance_key] = replace(
            winner_provenance,
            configuration=configuration,
        )

    def layer_values(self, name: str, address: Hashable) -> dict[str, Any]:
        """Return all layer values available at an overlay address."""
        if name not in self.overlay_priorities:
            raise KeyError(f"Unknown overlay: {name}")
        return {
            layer: deepcopy(values[address])
            for layer, values in self.overlays[name].items()
            if address in values
        }

    def effective(self, name: str, address: Hashable) -> tuple[Any, str]:
        """Return the highest-priority available value and its layer."""
        values = self.layer_values(name, address)
        if not values:
            raise KeyError(f"No value for overlay '{name}' at address {address!r}")
        layer = max(values, key=lambda candidate: self.overlay_priorities[name][candidate])
        return values[layer], layer

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
            overlays=deepcopy(self.overlays),
            overlay_priorities=deepcopy(self.overlay_priorities),
            overlay_provenance=deepcopy(self.overlay_provenance),
        )

    def restore(self, snapshot: WorldSnapshot) -> None:
        self.fields = deepcopy(snapshot.fields)
        self.entities = deepcopy(snapshot.entities)
        self.events = deepcopy(snapshot.events)
        self.observations = deepcopy(snapshot.observations)
        self.provenance = deepcopy(snapshot.provenance)
        self.spatial_fields = deepcopy(snapshot.spatial_fields)
        self.overlays = deepcopy(snapshot.overlays)
        self.overlay_priorities = deepcopy(snapshot.overlay_priorities)
        self.overlay_provenance = deepcopy(snapshot.overlay_provenance)
