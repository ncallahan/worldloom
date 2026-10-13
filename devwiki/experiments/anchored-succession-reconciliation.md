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

The oracle is test-only and limited to six people, with an explicit node cap. A solution is any valid chain satisfying all hard rules and anchors; it need not span the entire horizon. Tiny oracle tests use a 31-year horizon and reign bounds of 3–8 years.

The canonical problem fingerprint deliberately excludes `seed`, `generator_id`, and `generator_version`: these identify how input was generated, not the semantic constraints. This is a known limitation for tie-breaking: changing the seed may change the selected tied solution without changing the feasibility verdict. Scenario 8 must treat that distinction explicitly.

Raw measurements will be stored under `experiments/anchored_succession/`. No solver results or scale measurements are claimed yet.

## Results

Stage 1 is awaiting CI confirmation for the fix commit. The previous traversal reached 1,000,000 diagnostic nodes at depth 19 with 5,977 candidate reign intervals under default rules before a diagnostic cap stopped it. This confirms that the previous immediate-repeat-only search was impractical for the tiny test.

## Interpretation

**DEMONSTRATED**

- Pending CI: bounded diagnostic instrumentation reproduced the previous oracle's node explosion.

**STILL OPEN**

Solver parity, conflict-core quality, order independence, reveal semantics in solver outputs, reconciliation lifecycle, and scale remain unmeasured.

## Scope

Experiment only. No changes to `src/worldloom/`, WorldState, engine integration, question pages, glossary, architecture pages, or `current.md`. No unresolved/projection representation decision is made. The brute-force enumerator is a test oracle only.

## Artifacts

- Code and raw results: `experiments/anchored_succession/`
- Tests: `tests/experiments/test_anchored_succession.py`
