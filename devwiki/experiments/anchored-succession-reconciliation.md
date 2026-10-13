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

## Stage 2 — CP-SAT adapter

The experiment-local adapter is `experiments/anchored_succession/cp_sat.py`. Its optional extra is `cp-sat`, pinning OR-Tools `9.15.6755` (Apache-2.0). For the CPython 3.12 Linux CI resolution, the installed distribution metadata captured by `python -m pip inspect` records this dependency set and the following licence fields:

| Package | Resolved version | Declared licence metadata |
| --- | --- | --- |
| OR-Tools | 9.15.6755 | Apache 2.0 |
| absl-py | 2.5.1 | Apache-2.0 |
| immutabledict | 4.3.1 | MIT |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| pandas | 3.0.6 | BSD 3-Clause License |
| protobuf | 6.33.6 | 3-Clause BSD License |
| typing-extensions | 4.16.0 | PSF-2.0 |
| python-dateutil (transitive via pandas) | 2.9.0.post0 | Dual License |
| six (transitive via python-dateutil) | 1.17.0 | MIT |

OR-Tools declares the first six packages as direct requirements. In this Linux/Python 3.12 resolution, pandas adds `python-dateutil`, which adds `six`; pandas' `tzdata` requirement is conditional on Windows or Emscripten and was not installed in this CI environment. These names, versions, and licence fields were read from the installed distributions' metadata in the CPython 3.12 CI job; `stage2_pip_inspect.json` preserves the full metadata snapshot. The dedicated `CP-SAT solver gate` CI job sets `WORLDLOOM_REQUIRE_CP_SAT=1`; backend absence is a test failure in that job, not a skip. The default experiment suite may skip solver-specific tests when the optional dependency is absent.

The adapter models each layer as a non-empty, contiguous chain, enforces reign lengths, ages/deaths, genealogy, anchor layers, reveal divergence, record/reveal contradiction semantics, and conditional anchored-span occupancy. The independent checker validates every returned incumbent. The solver-reported unperturbed objective is reconstructed from the objective variables and must equal `evaluate_objective` exactly in tests.

Keyed perturbation coefficients use `rng_for` and semantic keys. The real integer objective is multiplied by one more than the sum of all possible tie coefficients, so the perturbation cannot offset even a one-unit increase in the real objective. Solver comparisons use objective equality and membership in the oracle's optimal solution set, not exact equality with the oracle's selected tie-break.

Scenario 2's conflict core and anchor-removal suggestions are exploratory. The core is deletion-checked for subset minimality. Smallest removal sets are searched by increasing cardinality with assumptions fixing each anchor active or inactive; the report includes the resulting unperturbed objective. Suggestions are authorial interventions only and never mutate the problem automatically. Softening is not yet enumerated as a distinct intervention operation.

## Results

The previous traversal reached 1,000,000 diagnostic nodes at depth 19 with 5,977 candidate reign intervals under default rules. **This figure is exploratory and not reproducible from the repository.** It came from an uncommitted diagnostic and is retained only as a caveated historical observation.

For the small-rule diagnostic problem, the recorded enumeration was 159 candidate reign intervals, 1,128 nodes explored, and 173 chains. These counts describe that small-problem diagnostic, not a solver benchmark.

**Stage 2 CI findings (small scenarios only):** the dedicated CP-SAT gate passed all 8 solver tests. Scenarios 1–5 completed, including objective parity with the oracle, independent-checker validation, reveal-only semantics, marked/unmarked record interactions, and deterministic order-independent selection. Additional objective-parity tests cover sibling-transition and stability terms and a missing soft-anchored ruler with positive tolerance. These are correctness tests on toy instances, not scale or performance evidence.

For the deliberately conflicting two-anchor scenario, CP-SAT returned the conflicting anchor subset `{pin-A, pin-B}`; deletion checks found it subset-minimal. Exhaustive removal-set search by increasing cardinality found the two smallest repairs, `{pin-A}` and `{pin-B}`, each restoring feasibility with unperturbed objective 0. This is exploratory decision support only. The tool does not alter anchors, and softening anchors is not yet enumerated as a separate repair operation.

The Stage 2 model-size measurement is emitted as `stage2_model_size.json` by the dedicated CI job. It counts variables and constraints from the CP-SAT model proto for each scenario; those counts describe only these toy encodings and are not scale evidence. No scale benchmark is claimed.

## Interpretation

**DEMONSTRATED**

- The test oracle has an explicit node cap and rejects repeated rulers during chain extension.
- Marked records still constrain the titular layer, while only unmarked record/reveal conflicts trigger the contradiction diagnostic.
- Anchor layers and anchored-span occupancy are represented in the independent checker and tested against hand-built cases.
- A direct independent-checker test demonstrates that a reveal can be satisfied while the titular throne is empty during the reveal years unless an interval-form hard or record anchor causes those years to be covered by the occupancy-span rule.

**STILL OPEN**

Large-instance solver performance, broader conflict-core quality, reconciliation lifecycle, hard-anchor-pair feasibility rates, and scale remain unmeasured. The conflict core and minimal removal sets have only been demonstrated on the small synthetic infeasible scenario.

## Scope

Experiment only. No changes to src/worldloom/, WorldState, engine integration, question pages, glossary, architecture pages, or current.md. No unresolved/projection representation decision is made. The brute-force enumerator is a test oracle only.

## Artifacts

- Code and raw results: `experiments/anchored_succession/`
- Tests: `tests/experiments/test_anchored_succession.py`

## Stage 2 comparison criterion

Implemented in `tests/experiments/test_anchored_succession_cp_sat.py`: compare solver results with the oracle by optimal objective value and by membership of each solver-selected solution in the oracle's optimal solution set, not by exact equality. The oracle's lexicographic tie-break and solver keyed perturbation may select different members of the same optimal set.
