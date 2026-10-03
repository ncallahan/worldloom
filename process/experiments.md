---
type: process
status: process
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Experiments

## Experiments

Experimental work belongs under `docs/EXPERIMENTS.md` conventions and should not silently become normative architecture.

Record random seeds and relevant software/configuration versions.

### Keep experiments separate

Experiments are evidence about models and architecture. They are not automatically normative architecture. Keep experimental code/configuration/results separate from the stable framework.


## Planned: non-grid spatial representation on the real FMG fixture

### Status

**PLANNED ONLY. No results recorded.**

### Question

Can the observed FMG spatial structures be represented without forcing them into the existing grid-only representation? The experiment should cover cell adjacency, burg point locations, river paths represented by ordered cell IDs, route polylines represented by [x, y, cell] points, and state polygons/areas, while keeping specialist-source details behind an explicit Worldloom representation.

### Pass/fail criteria

**Pass** if the same real fixture can be represented with explicit, inspectable relationships for cells/adjacency, burg locations, river paths, route geometry, and state regions, and downstream inspection does not require direct knowledge of FMG record layout.

**Fail** if any required structure cannot be represented without silently flattening its spatial meaning, if relationships are ambiguous or lossy, or if downstream consumers must depend on FMG-specific field names or container conventions.

### Falsification condition

The experiment falsifies the candidate non-grid representation if at least one required FMG structure can only be represented by discarding information needed for spatial interpretation or by exposing FMG-specific storage semantics as the Worldloom contract.

## Planned: coordinate-transform round trip

### Status

**PLANNED ONLY. No results recorded.**

### Question

Can the intended import-space → internal-space → target-space pipeline preserve coordinates through explicit, replaceable transform objects, using the real FMG fixture and the provisional identity transform for internal space?

### Pass/fail criteria

**Pass** if representative FMG cell, vertex, burg and route coordinates can be transformed into internal space and then a target space and round-tripped back within an explicitly defined tolerance, with the identity internal transform behaving exactly as expected.

**Fail** if a transform loses required coordinate information, if the transform chain cannot be composed/replaced independently, or if the round trip requires hidden assumptions about the final Worldloom coordinate system.

### Falsification condition

The transform design is falsified if round-trip error cannot be bounded by a documented tolerance for the tested coordinates, or if changing one transform requires changing unrelated import/export logic.

## Planned: world save/load round trip and JSON encoding

### Status

**PLANNED ONLY. No results recorded.**

### Question

Can the MVP world representation be saved to versioned JSON and loaded without changing canonical meaning, including current tuple-key, tuple-location and set values?

### Pass/fail criteria

**Pass** if save → load preserves canonical entities, fields, relationships, provenance, tuple-key mappings, tuple locations, sets, and schema-version metadata without relying on Python-specific object encodings.

**Fail** if any supported value changes meaning, loses identity, changes key semantics, or cannot be represented and reconstructed deterministically.

### Falsification condition

The JSON persistence design is falsified if a supported canonical value cannot be round-tripped without a lossy or ambiguous encoding, or if two distinct in-memory values collapse to the same saved representation.

## Planned: stability of on-demand detail across persistence and repeated import

### Status

**PLANNED ONLY. No results recorded.**

### Question

Does on-demand detail remain stable when generated from the same address and pinned inputs, after save/load and after a repeated one-time import of the same FMG source file?

### Pass/fail criteria

**Pass** if the same resolution question/address and pinned source inputs produce the same Worldloom entity identity and generated detail after save/load, and the same source snapshot can reproduce the same result without dependence on unrelated generation order.

**Fail** if identity or generated detail changes because of save/load ordering, entity enumeration order, unrelated generated detail, or equivalent re-import of the same pinned source.

### Falsification condition

The address-derived identity/keyed-randomness approach is falsified for the tested detail level if any controlled repetition with identical pinned inputs produces a different identity or detail, or if unrelated generation order changes the result.
