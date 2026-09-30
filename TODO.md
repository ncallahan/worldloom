# Worldloom TODO

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

### Investigate progressive resolution consequences

- Determine how invalidation should work when a coarse projection changes after a local fact has been resolved.
- Determine how dependencies between provisional information and resolved facts should be represented.
- Determine what reproducibility information is needed to repeat a selective resolution.
- Do not introduce a dedicated provisional-state representation until an experiment demonstrates that the existing observation/canonical-state boundary is insufficient.

## Later

- Test the architecture against one established external system, preferably a small GIS/terrain integration.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.

## Questions / Decisions Needed

- How should spatial/grid metadata required by specialist systems be represented when it is more than provenance and part of the meaning of a field?
- How should external source identity and versioning be represented so that an imported dataset can be reproduced independently of its original file path?

- How should provisional information be represented: observation, provisional state, generator/prior, or another mechanism?
- How should provisional information and its dependencies be invalidated after an explicit world change?
- How should already-resolved facts be reconciled when a later change makes them inconsistent?
- How much global coherence must a broad projection guarantee before local resolution?
- Should a projection be stored, represented by a reproducible generator, cached, or some combination?
- What should the canonical interface for external specialist systems look like?
- Which state is authoritative, and which values should always be recomputable?
- What minimum snapshot semantics are required for branching and reproducibility?
