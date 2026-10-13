---
type: question
status: open
summary: Design question for reconciling projections with dated canonical-history anchors.
related: ["[[index]]", "[[devwiki/experiments/invalidation-reconciliation]]", "[[devwiki/architecture/events-and-history]]", "[[devwiki/architecture/provenance]]", "[[devwiki/architecture/canonical-state-vs-observation]]", "[[devwiki/architecture/progressive-generation-and-resolution]]", "[[devwiki/architecture/snapshots]]", "[[devwiki/references/procedural-constraints]]"]
---

# Anchored history reconciliation

## Purpose and motivating use

**OWNER DECISION** — The first real-world use is constructing canonical history and known facts for Scadrial, the world of the Mistborn RPG, and projecting actions across roughly 300 years while respecting those constraints. This is an ongoing capability, not a one-off reconstruction. Scadrial data will come later, after more simulation elements exist.

**OWNER DECISION** — No copyrighted data will be committed to this repository. A private repository may be created for that data.

## Problem

**PROPOSED (pending owner confirmation)** — Anchored-history reconciliation means finding a coherent history or projection between dated facts that are treated as anchors. It is not merely forward simulation from one initial state: a forward-only engine cannot guarantee that its result reaches a later anchor. The task must account for constraints at both ends and between them.

**PROPOSED (pending owner confirmation)** — This is related to, but distinct from, invalidation. Invalidation asks whether a downstream fact has become stale because an upstream input changed. Anchored-history reconciliation asks how a projection can satisfy a set of dated anchors and constraints. They meet when an anchor is added or changed: existing projections may no longer fit and must be reconsidered.

**FACT** — The invalidation/reconciliation experiment demonstrated that replacing an observation changes its stored provenance fingerprint while a previously resolved canonical entity remains unchanged. It also showed that the resolved entity's provenance identifies its source observation by semantic name but does not retain that observation's historical fingerprint; retaining a snapshot of earlier observation provenance permits an external comparison. The experiment did not implement automatic invalidation or reconciliation, and left source-version history, stale marking, propagation, and handling of stale facts open. See [[devwiki/experiments/invalidation-reconciliation]].

**FACT** — The burg-to-ward resolver records `input_fingerprints` for entity inputs: each generated ward's provenance configuration includes the fingerprint of its source burg entity. The resolver's recorded provenance inputs identify the entity input; the prior observation and events used by the resolver are not recorded as provenance inputs for each generated ward. See `src/worldloom/detail/burg_wards.py`, especially `_add_wards`, `_resolve_one`, and `resolve_burg_wards`.

**FACT** — The simulation engine schedules modules using each module's declared `temporal_interval`; a scheduled run invokes modules when their intervals are due. See `src/worldloom/simulation/engine.py` and [[devwiki/architecture/time-and-scheduling]].

## Scope and owner decisions

**OWNER DECISION** — When no valid projection or repair exists, a Hand-of-God (authorial) intervention is required: the author adds fixed points or removes or loosens some to create a valid option. The system reports infeasibility and never fudges or silently chooses. The intervention is a recorded, visible event.

**OWNER DECISION** — Soft anchors express uncertainty generally: the author may not yet have decided, only a rough high-level emulation may have been done, or map resolution or scale may not justify exact placement.

**OWNER DECISION** — Coarse constraints are fuzzy. What is resolved at lower levels from the outer constraints is the closest thing to truth; discrepancies with coarse claims are reported, not enforced. See [[devwiki/vision/gm-campaign-continuity]].

**OWNER DECISION** — Some anchors are soft rather than absolute.

**OWNER DECISION** — “It looked like X, but was actually Y” scenarios are wanted if they can be implemented.

**OWNER DECISION** — The first scope is discrete facts and historical events. Quantities such as population may be added later.

**OWNER DECISION** — When anchors change, affected projections are reopened, or marked obsolete if reopening is not possible.

**OWNER DECISION** — Avoid hand-rolling solvers. Prefer wrapping one broad library if a suitable one exists; otherwise wrap solvers by constraint type. Keep the solving methods flexible.

**OWNER DECISION** — Succession (rulers and reigns) is the first toy domain.

**OWNER DECISION** — An unsatisfiable anchor set is a reported result that explains which anchors conflict; it must never be silently repaired.

**PROPOSED (pending owner confirmation)** — The infeasibility report names conflicting anchors and the smallest sets of anchors whose removal or loosening would restore feasibility. Solver support should be assessed in the experiment.

**PROPOSED (pending owner confirmation)** — “Obsolete” is not terminal: a projection can be re-solved after authorial intervention. A reopened solution is a proposal; only the GM promotes it to an anchor.

**OWNER DECISION** — Promoting an adopted projection makes it an anchor, consistent with explicit promotion of provisional information to canonical state.

**OWNER DECISION** — Projection lifecycle states are current, reopened, and obsolete. Staleness should be detected from a recorded fingerprint of the anchor set and constraints, reusing the `input_fingerprints` idea.

**OWNER DECISION** — Solvers should be reached through a solver-neutral problem description and adapter, consistent with the existing adapter principle.

**OWNER DECISION** — Reproducibility should use keyed randomness (`rng_for`) rather than solver-internal randomness.

## Approaches to compare

**OPEN** — The following are candidates for comparison, not decisions.

| Approach | Potential fit | Main weakness / question |
|---|---|---|
| Constraint propagation or collapse (WFC / Model Synthesis style) over dated facts | Can enforce local compatibility and progressively settle unknowns around anchors. | Global temporal constraints and explaining conflicts may be difficult; suitability for event histories is unproven. |
| Forward simulation with reject/resample, segmented between consecutive anchors | Reuses forward dynamics while treating each pair of anchors as a bounded segment. | May be inefficient when anchors are far apart or constraints are rare; reaching both anchors is not guaranteed without a workable search strategy. |
| Backward chaining / abduction | Starts from an observed or required later fact and seeks plausible causes or prior states. | May produce multiple explanations and needs a way to compare or reconcile them with forward dynamics. |
| Coarse-to-fine hybrid matching progressive resolution | Could use broad constraints first, then resolve detail where anchors or contradictions require it. | Coordination between scales, consistency guarantees, and when to refine remain unspecified. |

**FACT** — The entries in [[devwiki/references/procedural-constraints]] are research references only. Their presence is not evidence that Worldloom should copy any listed architecture.

## Open design questions

**OPEN** — Anchor representation: hard or soft status, strength, source, and tolerance.

**OPEN** — Relationship between soft anchors and the vision note's “declared degrees of freedom”; they may be distinct concepts.

**OPEN** — Naming overlap between “Hand-of-God” (authorial intervention) and “hand of the gods” (in-world feasible repair); no term is selected.

**OPEN** — Representation of “apparent versus actual”: separate layers, claims carrying source or perspective, or another model; and how this relates to the canonical-state-versus-observation boundary.

**OPEN** — How to report and handle contradictions between anchors, including contradictions between canon sources.

**OPEN** — Whether counterfactual alternatives should be represented through snapshot branching. Current snapshots capture and restore state independently, while advanced checkpointing and branching semantics remain future work; see [[devwiki/architecture/snapshots]].

**OPEN** — How coarse-to-fine solving should work and what consistency it must guarantee at each resolution.

## First experiment

**OWNER DECISION** — The first toy domain is succession: rulers and reigns.

**PROPOSED (pending owner confirmation)** — Use a small dated succession timeline with anchors and constraints to compare candidate reconciliation approaches, including a deliberately conflicting anchor set. The experiment should report conflicts rather than silently alter anchors.

**FACT** — This toy succession experiment is not started and is not specified in this page.