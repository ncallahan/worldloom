---
type: experiment
status: experiment
summary: Measurement-only study of solver-neutral anchored succession reconciliation.
related: ["[[devwiki/process/experiments]]", "[[devwiki/questions/anchored-history-reconciliation]]", "[[devwiki/questions/in-world-time-and-dating]]", "[[devwiki/experiments/invalidation-reconciliation]]"]
---

# Anchored succession reconciliation experiment

## Question

Can discrete anchored history be described once in a solver-neutral form and solved through two solver adapters with reproducible, order-independent, explainable results and projections that become stale, reopen, or obsolete after anchor changes?

## Method

**Stage 1 — model and independent checks.** The experiment-local problem/result records, deterministic fixtures, independent hard-rule checker, objective evaluator, and brute-force oracle are established before solver adapters. Integer years are a toy convenience, not a date-model decision.

The oracle is test-only and limited to six people, with an explicit node cap. A solution is any valid chain satisfying all hard rules and anchors; it need not span the entire horizon. Tiny oracle tests use a 31-year horizon and reign bounds of 3–8 years. Bounds-form anchors constrain a reign's start year but do not contribute to the anchored-span occupancy rule; only interval-form hard and record anchors do.

**Anchored-span occupancy rule:** on each layer, the throne must be occupied in every year from the earliest to latest year covered by any hard or record anchor. If there are no hard or record anchors, no coverage is required. This avoids a degenerate objective that rewards leaving years empty by selecting fewer rulers.

**Objective layer accounting:** reign-length deviation and sibling-transition preference costs are counted on both titular and effective layers (so identical layers count those costs twice). Soft-anchor penalties apply on the anchor's specified layer(s), with a missing ruler penalized by inclusive horizon length per targeted layer; tolerance reduces the penalty only when the ruler exists. Stability mismatch is counted on the titular layer only. The independent evaluator is the objective reference for later solver comparisons.

The canonical problem fingerprint excludes seed, generator ID/version, and stability reference. Generation metadata is not semantic constraint input, and stability reference is an input to re-solving rather than a constraint. A seed change may change the selected tied solution without changing the feasibility verdict; this remains a known limitation.

The hard-anchor-pair feasibility report is deferred to Stage 2, when a solver exists. Exploratory pair counts are not reported here.

## Results

The previous traversal reached 1,000,000 diagnostic nodes at depth 19 with 5,977 candidate reign intervals under default rules. **This figure is exploratory and not reproducible from the repository.** It came from an uncommitted diagnostic and is retained only as a caveated historical observation.

For the small-rule diagnostic problem, the recorded enumeration was 159 candidate reign intervals, 1,128 nodes explored, and 173 chains. These counts describe that small-problem diagnostic, not a solver benchmark.

Stage 1 CI is required to validate every code commit; no solver results or scale measurements are claimed yet.

## Interpretation

**DEMONSTRATED**

- The test oracle has an explicit node cap and rejects repeated rulers during chain extension.
- Marked records still constrain the titular layer, while only unmarked record/reveal conflicts trigger the contradiction diagnostic.
- Anchor layers and anchored-span occupancy are represented in the independent checker and tested against hand-built cases.
- A reveal can be satisfied while the titular throne is empty during the reveal years unless an interval-form hard or record anchor causes those years to be covered by the occupancy-span rule.

**STILL OPEN**

Solver parity, conflict-core quality, order independence, reconciliation lifecycle, hard-anchor-pair feasibility rates, and scale remain unmeasured.

## Scope

Experiment only. No changes to src/worldloom/, WorldState, engine integration, question pages, glossary, architecture pages, or current.md. No unresolved/projection representation decision is made. The brute-force enumerator is a test oracle only.

## Artifacts

- Code and raw results: `experiments/anchored_succession/`
- Tests: `tests/experiments/test_anchored_succession.py`

## Stage 2 comparison criterion (not implemented here)

Compare solver results with the oracle by optimal objective value and by membership of each solver-selected solution in the oracle's optimal solution set, not by exact equality. The oracle's lexicographic tie-break and solver keyed perturbation may select different members of the same optimal set.
