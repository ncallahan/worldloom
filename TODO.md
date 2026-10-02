# Worldloom TODO

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

**Active:** strengthen and verify the question-derived identity and address-keyed randomness experiment before human review.

## Later

- Inspect the generated GeoTIFF in an external GIS application and use the result to inform the next interface/internal-model experiment.

- Use the raster and spatial-field experiments to inform the eventual spatial-data contract without prematurely fixing it.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.

## Questions / Decisions Needed

- How should the minimal grid semantics demonstrated by the spatial-field experiment generalise to other spatial data without prematurely fixing a universal spatial model?
- How should external source identity and versioning be represented so that an imported dataset can be reproduced independently of its original file path?

- How should observation version history and provenance tracing be represented?
- What invalidation semantics apply when a broad observation changes?
- How should already-resolved facts be reconciled after an explicit world change?
- How should per-module seeds and execution configuration support deterministic regeneration?
- Should overlay provenance in PR #20 adopt `Address.canonical` once both PRs are on `main`?
- Should address-keyed randomness and resolution-question-derived identity become required mechanisms for modules that need order-independent reproducibility, or remain optional tools?
- Should the identity digest remain 48 bits, or be lengthened after collision-detection evidence is established?
- Should entity aliases become unique at `WorldState.add_entity` time rather than only at lookup?
- Should address segments be NFC-normalised, or should NFC and NFD remain distinct canonical addresses?
- What world/seed scope, if any, should be included in entity identity?
- Should overlay provenance in PR #20 adopt `Address.canonical` once both PRs are on `main`?
- Should derived outputs be stored, recomputed, or handled as a combination?
- What should the canonical interface for external specialist systems look like?
- Which state is authoritative, and which values should always be recomputable?
- What minimum snapshot semantics are required for branching and reproducibility?
