# Worldloom TODO

This is the active working queue for Worldloom.

Unlike the long-term roadmap, this document records work that has been consciously selected for near-term implementation or design. Completed work should be removed from this file; the Git history is the record of what was done.

## Now

### Exercise the first external-system adapter

- Run the raster terrain adapter against a small realistic terrain dataset.
- Check the reproducibility and provenance implications of using an external raster source.
- Use the result to decide whether the adapter boundary needs refinement before adding another specialist system.

## Later

- Expand uncertainty and statistical-state resolution machinery.
- Expand event semantics and event consequences.
- Expand provenance and dependency history.
- Add versioned snapshots/checkpoints.
- Add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.

## Questions / Decisions Needed

- What should the general canonical interface for external specialist systems look like beyond the initial raster integration?
