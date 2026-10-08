---
type: process
status: process
summary: Active working queue migrated from the repository TODO.
related: ["[[index]]", "[[devwiki/process/development-workflow]]", "[[devwiki/questions/identifier-address-model]]", "[[devwiki/questions/fmg-import-scope]]"]
---

# Current work

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

1. **Markdown vault projection.** Implemented: readable long/multi-line text fields and deterministic group-by indexes for the presentation-only `type` and `group` attribute names.

## Next work

The planned order for the Markdown-vault maintainability work is:

1. **R1 — managed-tree writer extraction.** Merged in PR #59.
2. **R1b — writer safety fixes.** Implemented in the current Draft PR; record the final-head CI result here after CI completes.
3. **R2 — naming and escaping helpers.** Next, preserving output behavior.
4. **R3 — note/index/report rendering.** Follow R2, preserving output behavior.
5. **Report-shape unification.** Follow R2/R3.
6. **Step 7.** Return to the planned on-demand local-detail design after the exporter work.

These are planned steps, not completed work.

The existing FMG reference-field measurement remains separate: measurement only; no implementation or schema decision is implied.

## Questions / Decisions Needed

- How should explicit authorial amendments to canonical state be represented, including provenance and precedence, and how should dependent derived values become stale? See [[devwiki/questions/canon-amendment]].

## Later

- **Deferred: exclusive-producer validation.** The narrow validation step was deliberately skipped in favour of the spatial experiment; revisit it after the MVP path is further established. Do not add runtime guards, REFINES, or overlay-store semantics without separate authorisation.

- Inspect the generated GeoTIFF in an external GIS application and use the result to inform the next interface/internal-model experiment.
- Use the raster and spatial-field experiments to inform the eventual spatial-data contract without prematurely fixing it.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.
