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

These are planned experiments only. No results are recorded here until the experiments have actually been run.

### Non-grid FMG spatial representation

**Question:** Can the Worldloom state represent the useful spatial structures in a real FMG full export without prematurely fixing a universal spatial model?

**Input:** a committed FMG full JSON fixture.

**Scope:** cells and adjacency, burg points, river/route polylines, state polygons, and explicit source/internal/target coordinate-transform objects.

**Pass/fail:** the selected structures can be represented, related, and exported without losing required identifiers, geometry, or provenance; failures identify a concrete missing contract.

**Falsification:** required structures cannot be represented without adding a fixture-specific or globally prescriptive spatial abstraction.

### Coordinate transform round trip

**Question:** Can explicit source-to-internal and internal-to-target coordinate transforms preserve enough information for the MVP exports?

**Pass/fail:** representative coordinates round-trip within documented numerical tolerance for the transforms used by the experiment.

**Falsification:** the transform pair loses information required by the source or target representation, or no stable tolerance can be established.

### World save/load round trip

**Question:** Can the minimal versioned JSON world file round-trip the state needed by the MVP?

**Scope:** include current structures that JSON cannot directly encode, especially tuple keys, tuple locations, and sets.

**Pass/fail:** save → load preserves the tested state semantically and the schema version is explicit.

**Falsification:** tested state cannot be round-tripped without silently changing its meaning, identity, or required provenance.

### On-demand detail stability

**Question:** Does one level of generated detail remain stable across persistence and repeated import of the same pinned FMG input?

**Pass/fail:** resolving the same address after save/load, and resolving it again from the same pinned input, yields the same identity and keyed-random results.

**Falsification:** equivalent resolution paths produce different identities or generated values without an explicitly changed input, seed, or version.


## Planned FMG MVP experiments

These entries are plans only; no results are recorded yet.

### Non-grid FMG spatial representation

Question: Can real FMG cells, adjacency, burg points, river/route lines, state polygons, and coordinate transforms be represented without fixing a universal spatial model?

Pass/fail: required structure, relationships, identifiers, geometry, and provenance survive the representation.

### Coordinate transform round trip

Question: Can source/internal/target coordinate transforms round-trip representative coordinates within a documented tolerance?

Pass/fail: round-trip error remains within that tolerance.

### World save/load round trip

Question: Can the versioned JSON world file preserve the MVP state, including tuple keys, tuple locations, and sets?

Pass/fail: save/load preserves semantic state, identity, provenance, and schema version.

### On-demand detail stability

Question: Does generated detail remain stable across save/load and repeated import of the same pinned FMG input?

Pass/fail: the same address produces the same identity and keyed-random values unless an explicit input, seed, or version changes.
