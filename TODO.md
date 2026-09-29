# Worldloom TODO

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

### State versus derived observation boundary

- Define what constitutes authoritative canonical world state.
- Distinguish persistent state from derived observations/calculations in the interfaces.
- Establish the semantics before implementing further domain modules.
- Add tests demonstrating that derived observations do not accidentally become persistent world facts.

## Next

### Multi-timescale scheduling

- Replace the prototype's sequential execution model with a minimal scheduler capable of invoking modules according to declared temporal requirements.
- Start with deterministic scheduling.
- Defer sophisticated event prioritisation until the basic scheduling semantics are tested.

### First external-system adapter

- Test the architecture against one established external system, preferably a small GIS/terrain integration.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.

## Later

- Expand uncertainty and statistical-state resolution machinery.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.

## Questions / Decisions Needed

- What should the canonical interface for derived observations look like?
- Which state is authoritative, and which values should always be recomputable?
- How should observations relate to module inputs/outputs and provenance?
- What minimum snapshot semantics are required for branching and reproducibility?
