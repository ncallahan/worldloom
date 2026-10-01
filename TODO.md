# Worldloom TODO

This is the active working queue for Worldloom.

## Now

_No active implementation task is selected. Choose the next experiment from the follow-up paths in `docs/EXPERIMENTS.md`._

## Later

- Test the architecture against one established external system, preferably a small GIS/terrain integration.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.

## Questions / Decisions Needed

- How should observation version history and provenance tracing be represented?
- What invalidation semantics apply when a broad observation changes?
- How should already-resolved facts be reconciled after an explicit world change?
- How should per-module seeds and execution configuration support deterministic regeneration?
- Should derived outputs be stored, recomputed, or handled as a combination?
- What should the canonical interface for external specialist systems look like?
- Which state is authoritative, and which values should always be recomputable?
- What minimum snapshot semantics are required for branching and reproducibility?
