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

1. **Markdown-vault maintainability — R3a note and import-report rendering (in progress).** Extract `render_note` and `render_import_note` plus focused helpers, preserving output bytes, error behaviour, and generated-file ordering.

## Next work

The planned order for the Markdown-vault maintainability work is:

1. **R1 — managed-tree writer extraction.** Merged in PR #59.
2. **R1b — writer safety fixes.** Merged in PR #60.
3. **R2 — naming and markup helpers.** Complete in PR #61; implementation and final-head CI are complete.
4. **R3a — note and import-report rendering.** In progress in this Draft PR; index rendering and orchestration remain for R3b.
5. **Report-shape unification.** Follow R2/R3.
6. **Step 7.** Return to the planned on-demand local-detail design after the exporter work.

R1, R1b, and R2 are complete. R3a is in progress; R3b (plan builder, index rendering, and orchestration, targeting `export_markdown_vault`) is next, followed by report-shape unification and then step 7.

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
