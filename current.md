---
type: process
status: process
summary: Active working queue migrated from the repository TODO.
related: ["[[index]]", "[[process/development-workflow]]"]
---

# Current work

This is the active working queue. Completed work belongs in Git history rather than remaining here.

## Now

Strengthen and verify the question-derived identity and address-keyed randomness experiment before human review.

## Later

- Inspect the generated GeoTIFF in an external GIS application and use the result to inform the next interface/internal-model experiment.
- Use the raster and spatial-field experiments to inform the eventual spatial-data contract without prematurely fixing it.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.

## Questions / Decisions Needed

- How should the minimal grid semantics demonstrated by the spatial-field experiment generalise to other spatial data without prematurely fixing a universal spatial model?
- How should external source identity and versioning be represented so that an imported dataset can be reproduced independently of its original file path?
- How should observation version history and provenance tracing be represented?
- What invalidation semantics apply when a broad observation changes?
- How should already-resolved facts be reconciled after an explicit world change?
- How should per-module seeds and execution configuration support deterministic regeneration?
- Should address-keyed randomness and resolution-question-derived identity become required mechanisms for modules that need order-independent reproducibility, or remain optional tools?
- What should the canonical interface for external specialist systems look like?
- Which state is authoritative, and which values should always be recomputable?
- What minimum snapshot semantics are required for branching and reproducibility?

<!-- Migration source heading: # Worldloom TODO -->
<!-- Migration source heading: ## Now -->
<!-- Migration source heading: ## Later -->
<!-- Migration source heading: ## Questions / Decisions Needed -->
