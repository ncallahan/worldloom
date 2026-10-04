---
type: reference
status: reference
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# README

# Worldloom Research and Reference Backlog

## Status

This is a **research/reference backlog**, not a dependency list and not an architecture specification.

The projects and resources below were identified during early Worldloom research because they may provide useful algorithms, domain models, interfaces, data structures, or implementation ideas. They should be investigated when a relevant Worldloom module is being designed.

No item here is a commitment to integrate, depend on, reproduce, or emulate the referenced system.

## 6. Reference policy

When a concrete Worldloom module is proposed:

1. Search this backlog for relevant established systems.
2. Investigate whether one or more can supply the required capability.
3. Compare their data model, resolution, determinism, licensing, performance, and interoperability characteristics with the Worldloom contract.
4. Prefer a thin adapter when a system is suitable.
5. Keep the Worldloom contract independent of the external implementation.
6. If none is suitable, document why before reimplementing substantial specialist functionality.

A reference becoming technically useful does not automatically make it an architectural decision.

## 7. Relationship to architecture

The backlog deliberately does not determine:

- the module graph;
- the canonical data model;
- the identifier scheme;
- validation architecture;
- storage technology;
- UI technology;
- dependency choices;
- implementation order.

Those decisions belong in the architecture/specification and should be made from demonstrated requirements and experiments.
