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

**Stage 1 — model and independent checks.** The experiment-local problem/result records, deterministic fixtures, independent hard-rule checker, and a brute-force oracle restricted to instances of at most six people are being established before solver adapters. Integer years in [0, 300] are a toy convenience, not a date-model decision.

The implementation will use worldloom.core.rng_for for keyed tie-breaking and worldloom.core.hashing.fingerprint for projection fingerprints. Raw measurements will be stored under experiments/anchored_succession/.

## Results

Stage 1 results are pending CI for the first commit. No solver outcomes or measurements are claimed yet.

## Interpretation

**DEMONSTRATED**

Nothing demonstrated yet; this section will be updated from CI-confirmed results.

**STILL OPEN**

Solver parity, conflict-core quality, order independence, reveal semantics, reconciliation lifecycle, and scale remain unmeasured.

## Scope

Experiment only. No changes to src/worldloom/, WorldState, engine integration, question pages, glossary, architecture pages, or current.md. No unresolved/projection representation decision is made. The brute-force enumerator is a test oracle only.

## Artifacts

- Code and raw results: experiments/anchored_succession/
- Tests: tests/experiments/test_anchored_succession.py
