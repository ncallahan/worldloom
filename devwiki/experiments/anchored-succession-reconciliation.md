---
type: experiment
status: experiment
summary: Measurement-only study of solver-neutral anchored succession reconciliation.
related: ["[[devwiki/process/experiments]]", "[[devwiki/questions/anchored-history-reconciliation]]", "[[devwiki/questions/in-world-time-and-dating]]", "[[devwiki/experiments/invalidation-reconciliation]]"]
---

# Anchored succession reconciliation experiment

## Question

Can discrete anchored history be described once in a solver-neutral form and solved through multiple solver adapters with reproducible, order-independent, explainable results and projections that become stale, reopen, or obsolete after anchor changes?

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

### Stage 2 CP-SAT model sizes (CI run 38389536025; 13 October 2026)

Counts were read from the stage2_model_size.json artifact produced by the CP-SAT solver gate. The artifact and stage2_pip_inspect.json were retained for 30 days and may expire; the repository page preserves the summarized findings.

| Scenario | Variables | Constraints |
| --- | ---: | ---: |
| 1 — Hard anchors only | 697 | 1,597 |
| 2 — Conflicting hard anchors | 448 | 1,112 |
| 3 — Soft-anchor tolerance | 319 | 697 |
| 4 — Reveal only | 451 | 1,028 |
| 5 — Repeatability | 700 | 1,601 |

These are construction sizes for the small 31-year toy scenarios only. They are not solve-time measurements or scale evidence.

The Stage 2 model-size measurement is emitted as `stage2_model_size.json` by the dedicated CI job. It counts variables and constraints from the CP-SAT model proto for each scenario; those counts describe only these toy encodings and are not scale evidence. The raw artifact from CI run `38389536025` (13 October 2026) is retained for 30 days by GitHub Actions; artifacts may expire and must not be treated as permanent records. No scale benchmark is claimed.

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


## Stage 3 — clingo / ASP adapter (provisional experiment)

The optional `clingo` extra pins `clingo==5.8.2`. The CPython 3.12 Linux CI job installed and recorded the following dependency chain from distribution metadata using `python -m pip inspect` (artifact: `stage3_pip_inspect.json`):

| Package | Resolved version | Relationship | Licence metadata |
| --- | --- | --- | --- |
| clingo | 5.8.2 | Direct optional dependency | `License: MIT` |
| cffi | 2.1.1 | Direct dependency of clingo | `License-Expression: MIT-0` |
| pycparser | 3.11 | Transitive via cffi on CPython | `License-Expression: BSD-3-Clause` |

The metadata reports `clingo` requiring `cffi`, and `cffi` requiring `pycparser` except on PyPy. This table records the actual CI resolution, not every platform's conditional dependency set.

The ASP encoding uses lexicographic optimization priorities: the unperturbed real objective is at priority 2 and keyed `rng_for`-derived tie-breaking is at priority 1. This intentionally differs from CP-SAT's subordinate integer scaling. Cross-backend selected solutions are recorded for comparison; only feasibility, optimal objective, and membership in the oracle's optimal set are required for cross-backend correctness. Grounding size/time is reported for these toy scenarios only; no scale claim is made.

Infeasible anchor cores are obtained from clingo's solve assumptions, then deletion-checked for subset-minimality. Smallest anchor-removal sets are exploratory authorial decision support; the adapter first disables every non-soft anchor and reports infeasibility independent of anchors if that baseline remains infeasible.


### Stage 3 CI results (2026-10-13; clingo 5.8.2)

Grounding size is the number of grounded symbolic atoms and normal/choice rules counted by the clingo observer; times are seconds from the CI run. These tiny synthetic scenarios are not a scale benchmark.

| Scenario | Case | Status / unperturbed objective | Ground atoms | Ground rules | Grounding (s) | Solve (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Hard anchors only | solved / 0 | 1,644 | 6,051 | 0.020566 | 0.001778 |
| 2 | Conflicting hard anchors | infeasible | 1,090 | 4,180 | 0.013932 | 0.001183 |
| 3 | Soft-anchor tolerance | solved / 0 | 676 | 2,105 | 0.007663 | 0.001400 |
| 4 | Reveal only | solved / 0 | 1,095 | 4,093 | 0.013536 | 0.001373 |
| 5 | Repeatability | solved / 0 | 1,667 | 6,086 | 0.019382 | 0.001912 |
| 6 | Declaration shuffle, seed 3 | solved / 0 | 1,667 | 6,086 | 0.019166 | 0.002941 |
| 6 | Declaration shuffle, seed 17 | solved / 0 | 1,667 | 6,086 | 0.019083 | 0.002972 |
| 6 | Declaration shuffle, seed 2026 | solved / 0 | 1,667 | 6,086 | 0.019532 | 0.002328 |
| 6 | Declaration shuffle, seed 91003 | solved / 0 | 1,667 | 6,086 | 0.019340 | 0.002071 |
| 7 | Hard anchors | solved / 0 | 1,644 | 6,051 | 0.019245 | 0.001739 |
| 7 | Reveal only | solved / 0 | 1,095 | 4,093 | 0.014188 | 0.001631 |
| 7 | Soft tolerance | solved / 0 | 676 | 2,105 | 0.007974 | 0.001462 |
| 7 | Conflicting anchors | infeasible | 1,090 | 4,180 | 0.013632 | 0.001157 |
| 7 | Marked record/reveal | solved / 0 | 1,096 | 4,106 | 0.013372 | 0.001233 |
| 7 | Sibling and stability costs | solved / 26 | 1,707 | 6,106 | 0.020353 | 0.002288 |

Scenario 2's assumption core was `{pin-A, pin-B}`; deletion checks established subset-minimality. The two smallest removal suggestions were `{pin-A}` and `{pin-B}`, each restoring feasibility with objective 0. They remain exploratory authorial interventions.

**Scenario 6:** CP-SAT and clingo each returned the same selected solution and objective as their own canonical-order run for all four shuffled seeds. The two backends also selected the same solution on this feasible scenario.

**Scenario 7:** across six tiny cross-backend cases, both backends agreed with the oracle on feasibility and optimal objective, and each feasible solver result belonged to the oracle's optimal-solution set. No disagreement findings were recorded. For the infeasible case, neither backend returns a solution, so selected-solution equality is not applicable. The selected solutions also happened to agree between CP-SAT and clingo in all five feasible cases; this is an observation, not the cross-backend acceptance criterion.

The run's raw JSON records all scenario-level comparisons and timings in the `clingo-stage3-measurements` artifact, along with the resolved `pip inspect` metadata. The artifact is from CI run `38389536025` (13 October 2026) and is retained for 30 days; GitHub Actions artifacts may expire. No scale result is inferred from these timings.

**Tie-sensitive order-independence follow-up:** scenario 5/6 tests previously used a unique optimum, so order independence did not establish tie-breaking invariance. A dedicated two-soft-window single-ruler case guards that its oracle optimal set has multiple members, checks membership and unchanged selection under four declaration/model shuffles for each backend, and uses ten distinct `problem.seed` values as a positive control. CP-SAT and clingo use different keyed coefficient sets; their selected tied solutions may legitimately differ, while each must remain in the oracle optimal set and preserve the unperturbed objective. Results for these stronger controls are pending CI.
