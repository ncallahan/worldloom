---
type: process
status: process
summary: Active working queue migrated from the repository TODO.
related: ["[[index]]", "[[process/development-workflow]]", "[[questions/identifier-address-model]]", "[[questions/fmg-import-scope]]"]
---

# Current work

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

1. **Finish identity work.** PR #19 (question-derived identity and address-keyed randomness) is merged. The remaining work is the still-open owner decisions in [[questions/identifier-address-model]]; no further identity implementation should be inferred from the experiment until those decisions are resolved.

2. **Exclusive-producer validation only.** Complete the narrow validation work for producer ownership; do not add runtime guards, REFINES, or overlay-store semantics unless separately authorised.

3. **Non-grid spatial experiment on a real FMG slice.** Exercise a real committed FMG slice with explicit import/export coordinate-transform objects, keeping the spatial representation experimental rather than settling the canonical coordinate space.

4. **Minimal world save/load.** Define and test a minimal save/load representation, including an explicit encoding for tuple keys and sets.

5. **FMG importer.** With the scope in [[questions/fmg-import-scope]] resolved as the current MVP boundary, plan and implement the first snapshot importer after the preceding identity, producer, spatial, and save/load work is complete.

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

## Follow-up

- If the MVP design note and planned experiment stubs from the earlier documentation work are still absent, create them in a separate documentation/experiment-planning PR rather than adding them to this measurement/tooling PR.
