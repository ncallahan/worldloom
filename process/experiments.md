---
type: process
status: process
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Experiments

## Experiments

Experimental work belongs under `process/experiments.md` conventions and should not silently become normative architecture.

Record random seeds and relevant software/configuration versions.

### Keep experiments separate

Experiments are evidence about models and architecture. They are not automatically normative architecture. Keep experimental code/configuration/results separate from the stable framework.


## Planned FMG MVP experiments

The following experiments are planned for the FMG MVP. They are intentionally recorded as questions and falsification criteria only; no result is claimed here.

### FMG non-grid spatial representation

**Question**

Can a real FMG full export be represented as a useful non-grid Worldloom spatial model containing cells with adjacency, burg point locations, river/route polylines, and state polygons without prematurely fixing a universal spatial representation?

**Pass/fail**

Pass if the experiment can represent these spatial relationships faithfully enough to support the MVP import/export path while keeping the representation independent of a regular grid.

Fail if a representation requires hidden assumptions about a universal Worldloom grid or loses required FMG relationships.

**Falsification**

A real fixture that cannot be represented without material loss of adjacency, point, line, or polygon relationships falsifies the current experimental representation.

### Coordinate-transform round trip

**Question**

Can explicit source → internal and internal → target coordinate-transform objects support a reversible round trip for the spatial data needed by the MVP?

**Pass/fail**

Pass if representative coordinates can be transformed to internal space and back to the source/target space within an explicitly recorded tolerance.

Fail if the transformation boundary cannot be made explicit and replaceable, or if round-trip error is uncontrolled for the intended output.

**Falsification**

A representative fixture requiring undocumented special cases in the transform path, or an unacceptable round-trip error under the stated tolerance, falsifies the tested transform design.

### World save/load round trip

**Question**

Can the MVP world be saved as versioned JSON and restored without changing the semantic state, including the current Worldloom structures that JSON cannot directly encode such as tuple keys, tuple locations, and sets?

**Pass/fail**

Pass if save → load preserves the semantic state and a second save produces an equivalent canonical representation under the chosen schema.

Fail if data is lost, types change unexpectedly, or the representation cannot round-trip.

**Falsification**

A fixture containing supported Worldloom state that cannot be encoded and restored without semantic loss falsifies the current save representation.

### Stable on-demand detail

**Question**

Does on-demand detail remain stable across save/load and repeated import of the same pinned FMG source when address-derived identity and keyed randomness are used?

**Pass/fail**

Pass if the same address and pinned inputs reproduce the same entity identity and generated detail after save/load and repeated import, while distinct addresses remain independently resolvable.

Fail if detail changes unexpectedly, collides across addresses, or depends on incidental iteration order.

**Falsification**

A controlled repeat using identical source hash, address, configuration, and seed that produces a different identity or detail falsifies the tested stability mechanism.
