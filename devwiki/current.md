---
type: process
status: process
summary: Active working queue for Worldloom.
related: ["[[index]]", "[[devwiki/process/development-workflow]]", "[[devwiki/questions/identifier-address-model]]", "[[devwiki/questions/fmg-import-scope]]", "[[devwiki/questions/contradictions-exceptions-and-solver-use]]", "[[devwiki/questions/anchored-history-reconciliation]]", "[[devwiki/questions/in-world-time-and-dating]]", "[[devwiki/questions/resolution-attempt-outcomes]]", "[[devwiki/questions/canon-amendment]]", "[[devwiki/experiments/anchored-succession-reconciliation]]", "[[devwiki/experiments/fmg-layering-and-references]]", "[[devwiki/vision/interfaces]]"]
---

# Current work

This document records work selected for near-term implementation or design. Completed work is removed from the active queue; durable decisions and outcomes belong in their relevant documentation.

## Now

**Direction (agreed; each step's design remains open).** Work toward a constrained simulation of a published world and adventure with events over a 300-year span. The emphasis is on detecting and explaining contradictions; solving constraints is an opt-in capability, used with authored, explained exceptions. Progress is a sequence of small experiments, each preceded by a question page where an architectural decision is needed. Nothing below is normative architecture.

**State.** The anchored-succession experiment (stages 1–5) is merged. Its evidence and open items are recorded in [[devwiki/experiments/anchored-succession-reconciliation]]; in short, solvers matched an oracle on small instances and on one planted chain, no feasible larger instance has been compared, and the larger-instance fixture needs a feasible generator. Contradiction handling, exceptions, and solver use are recorded in [[devwiki/questions/contradictions-exceptions-and-solver-use]].

## Next work

Ordered; each item needs its own brief.

1. **Contradiction reporter without a solver.** Cheap pre-checks (age and lifespan eligibility, interval overlap, kin reachability) over historical events, each contradiction reported with an explanation. Test on the existing planted chain and the infeasible generated instances, whose causes are known.
2. **Exceptions and "stated as fact to the audience."** Record both as events; test that an authored exception suppresses a reported contradiction with its explanation, and that a conflict with an item already stated as fact is flagged distinctly. Likely forces the exception-representation question.
3. **Feasible larger-instance generator, then local solving.** Fix the Stage 5 fixture defect; compare solving a local interval against the whole problem; test whether hard anchors decompose the problem.
4. **In-world time and dating.** Design first; see [[devwiki/questions/in-world-time-and-dating]].
5. **Coarse-to-fine coherence.** Resolve a broad claim down to finer facts without contradicting what has already been stated.
6. **Synthetic 300-year dry run.** A synthetic scenario for a published world and adventure with events over a 300-year span, run through steps 1–5. Setting-specific data stays in a private repository; no copyrighted source data enters this repository.

Unscheduled, separate from the path above:

- **Persist skipped-burg information from resolve runs.** Design first. See [[devwiki/questions/resolution-attempt-outcomes]].
- **FMG reference-field measurement.** Measurement only; no implementation or schema decision implied. Tracked in [[devwiki/experiments/fmg-layering-and-references]]; its hypotheses are not results.

## Questions / Decisions Needed

- How should explicit authorial amendments to canonical state be represented, including provenance and precedence, and how should dependent derived values become stale? See [[devwiki/questions/canon-amendment]].
- Exceptions, contradictions with items already stated as fact, and the relation between audience-committed canon and canonical state. See [[devwiki/questions/contradictions-exceptions-and-solver-use]].
- Ratify or revise the placeholder resolver defaults (burg_sigma 0.15, ward_sigma 0.5, target_ward_size 2.0, max_wards 12); population units are unverified; hamlets/rural remain deferred.
- Identity, addresses, coordinates, world-file format, and uncertainty representation remain open architecture questions. Decide each deliberately at the step that first needs it; do not settle incidentally.

## Later

- **Deferred: exclusive-producer validation.** Revisit after the MVP path is further established. Do not add runtime guards, REFINES, or overlay-store semantics without separate authorisation.
- Inspect the generated GeoTIFF in an external GIS application to inform the next interface/internal-model experiment.
- Use the raster and spatial-field experiments to inform the eventual spatial-data contract without prematurely fixing it.
- Prefer an adapter and standard data exchange over implementing equivalent specialist functionality inside Worldloom.
- Expand event semantics and event consequences; expand provenance and dependency history.
- Add versioned snapshots/checkpoints; add event-triggered scheduling after the fixed-interval scheduler has been exercised.
- Test composition with increasingly realistic specialist systems.
- Add architectural, integration, reproducibility, performance, and domain-model validation as appropriate.
- Server, API, CLI client, and MCP access surfaces are direction only (see [[devwiki/vision/interfaces]]).
