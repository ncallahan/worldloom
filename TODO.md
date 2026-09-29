# Worldloom TODO

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

### First external-system adapter

- Test the architecture against one established external system, preferably a small GIS/terrain integration.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.

## Later

- Expand uncertainty and statistical-state resolution machinery.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.

## Questions / Decisions Needed

- What should the canonical interface for external specialist systems look like?
- Which state is authoritative, and which values should always be recomputable?
- What minimum snapshot semantics are required for branching and reproducibility?
