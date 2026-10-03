---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Snapshots

## 13. Snapshot semantics

Snapshots are point-in-time captures of the world state intended to support reproducibility, restoration, and eventually branching.

The current snapshot contract is deliberately narrow:

- fields, entities, events, observations, and provenance are captured;
- captured state is deep-copied so later mutation cannot alter the snapshot;
- the snapshot container is immutable at the container level;
- optional metadata may record execution context;
- restoring a snapshot deep-copies its contents back into the world, so the restored world does not share mutable nested state with the snapshot.

Snapshot metadata is contextual rather than canonical world state. More advanced checkpointing and branching semantics remain future work until they are required by the simulation engine.

## 13. Snapshot semantics

Worldloom SHALL provide snapshots with independent mutable state.

A snapshot:

- SHALL capture fields, entities, events, observations, and provenance;
- SHALL deep-copy captured state so later mutation of the world does not alter the snapshot;
- SHALL be represented by an immutable snapshot container;
- MAY carry optional metadata describing execution context;
- SHALL NOT require metadata to restore world state.

Restoring a snapshot SHALL:

- replace the world's captured state with independent copies of the snapshot contents;
- avoid sharing mutable nested structures between the restored world and the snapshot;
- preserve the semantic distinction between canonical state and derived observations.

Snapshot metadata is contextual rather than canonical world state. The current WorldState.restore() operation intentionally restores world data only; callers may separately retain or interpret snapshot metadata as required.
