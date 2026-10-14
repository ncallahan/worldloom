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

**Stage 2 CI findings (small scenarios only):** the CP-SAT gate passed 12 tests in CI run [#1626](https://github.com/ncallahan/worldloom/actions/runs/38487233516). Scenarios 1–5 completed, including objective parity with the oracle, independent-checker validation, reveal-only semantics, marked/unmarked record interactions, and order-independent selection. Additional objective-parity tests cover sibling-transition and stability terms and a missing soft-anchored ruler with positive tolerance. These are correctness tests on toy instances, not scale or performance evidence.

For the deliberately conflicting two-anchor scenario, CP-SAT returned the conflicting anchor subset `{pin-A, pin-B}`; deletion checks found it subset-minimal. Exhaustive removal-set search by increasing cardinality found the two smallest repairs, `{pin-A}` and `{pin-B}`, each restoring feasibility with unperturbed objective 0. This is exploratory decision support only. The tool does not alter anchors, and softening anchors is not yet enumerated as a separate repair operation.

### Stage 2 CP-SAT model sizes (CI run [#1626](https://github.com/ncallahan/worldloom/actions/runs/38487233516); UTC date 2026-10-13)

Counts were read from the stage2_model_size.json artifact produced by the CP-SAT solver gate. The artifact and stage2_pip_inspect.json were retained for 30 days and may expire; the repository page preserves the summarized findings.

| Scenario | Variables | Constraints |
| --- | ---: | ---: |
| 1 — Hard anchors only | 697 | 1,597 |
| 2 — Conflicting hard anchors | 448 | 1,112 |
| 3 — Soft-anchor tolerance | 319 | 697 |
| 4 — Reveal only | 451 | 1,028 |
| 5 — Repeatability | 700 | 1,601 |

These are construction sizes for the small 31-year toy scenarios only. They are not solve-time measurements or scale evidence.

The table above was read from `stage2_model_size.json` in CI run [#1626](https://github.com/ncallahan/worldloom/actions/runs/38487233516), not reconstructed from another run. The artifact was uploaded on 2026-10-13 UTC and expires after 30 days (2026-11-12 UTC); preserve this page's summary because the raw artifact may expire.

## Interpretation

**DEMONSTRATED**

- The test oracle has an explicit node cap and rejects repeated rulers during chain extension.
- Marked records still constrain the titular layer, while only unmarked record/reveal conflicts trigger the contradiction diagnostic.
- Anchor layers and anchored-span occupancy are represented in the independent checker and tested against hand-built cases.
- A direct independent-checker test demonstrates that a reveal can be satisfied while the titular throne is empty during the reveal years unless an interval-form hard or record anchor causes those years to be covered by the occupancy-span rule.

**STILL OPEN**

Large-instance solve performance and broad conflict-core quality remain unmeasured. The lifecycle tests cover synthetic tiny instances only. Construction-size measurements are separate from solve performance and do not establish that large instances can be solved within practical time or memory.

## Stage 4 — projection reconciliation lifecycle

A projection stores the fingerprint of the problem that produced its solution and a separate fingerprint for the last problem checked. Rechecking an unchanged fingerprint preserves the complete prior record and never invokes a solver, regardless of whether its status is `current`, `reopened`, or `obsolete`. A changed problem with a proven infeasibility retains the previous solution as `obsolete`; its producing fingerprint is preserved and only the last-checked fingerprint advances. A changed feasible incumbent that passes the independent checker becomes a `reopened` proposal even when optimality was not proven. A timeout without an incumbent or an unknown result raises an explicit inconclusive error and leaves the previous projection unchanged.

Promotion is a separate authorial operation: `promote(projection, years)` emits hard anchors whose source is `promoted:<fingerprint>`. Reconciliation never promotes a proposal implicitly. Tests cover the `current → obsolete → reopened` lifecycle, exact conflict-core/removal-set text on tiny cases, and a promotion conflict where the promoted anchor is not redundant with a pre-existing hard anchor.

The CI workflow emits raw construction-size and stability-measurement JSON alongside the clingo dependency snapshot. GitHub Actions artifacts have 30-day retention and may expire. The repository's measurement tables must cite the exact CI run that produced their underlying artifact; scenario timings are run-specific and should not be copied across runs.

### Stage 4 construction-only size measurements (CI run [#1626](https://github.com/ncallahan/worldloom/actions/runs/38487233516))

These measurements use `generated_pool(size)`, a 300-year horizon (years 0–299), and three fixed hard anchors on existing person IDs. **No solver search or optimization was invoked.** The worker's wall-clock guard is 70 seconds per child and its generous data-segment cap is 6 GiB; peak RSS was measured in the child with `resource.getrusage`. All six builds completed; no resource guard was hit and no non-resource failure was recorded.

CP-SAT constraint counts below are from the model proto. The succession-family count is **analytic**, computed as `layers × (years − 1) × ordered non-kin pairs`; it is not a separately instrumented per-family count in clingo's ground rules.

| People | Build (s) | Variables | Constraints by proto type | Total constraints | Proto bytes | Peak RSS (MB) | Analytic succession count |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 12 | 1.116 | 17,471 | linear 107,924; bool_and 1,196; bool_or 1,196; lin_max 24 | 110,340 | 3,829,767 | 139.8 | 71,760 |
| 30 | 4.217 | 51,139 | linear 573,938; bool_and 13,156; bool_or 13,156; lin_max 60 | 600,310 | 19,480,109 | 320.0 | 490,958 |
| 100 | 37.327 | 175,027 | linear 6,078,600; bool_and 52,624; bool_or 52,624; lin_max 200 | 6,184,048 | 186,853,178 | 2,208.5 | 5,813,756 |

| People | Program build (s) | Grounding (s) | Ground atoms | Ground rules | Program bytes | Peak RSS (MB) | Analytic succession count |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | 0.137 | 3.319 | 53,300 | 1,253,208 | 313,730 | 46.7 | 71,760 |
| 30 | 0.326 | 8.888 | 140,267 | 3,446,835 | 687,676 | 69.8 | 490,958 |
| 100 | 1.060 | 36.906 | 471,414 | 15,662,934 | 2,141,801 | 173.3 | 5,813,756 |

The CP-SAT proto is dominated by `linear` constraints at every size. The analytic non-kin succession family rises from 71,760 to 5,813,756 across these pools and accounts for most of the linear-constraint growth (5,813,756 analytic succession constraints versus 6,078,600 total linear constraints at 100 people). Clingo's total ground rules grow from 1.25 million to 15.66 million; the succession count shown is analytic rather than a direct per-family observer count. These are construction/grounding measurements only and provide **no evidence that solving the 100-person instance is practical**.

### Stage 3 isolated ASP rule-family measurements (final-SHA CI run [#1642](https://github.com/ncallahan/worldloom/actions/runs/38495816117), artifact `clingo-stage3-measurements`, artifact ID `11864415078`; first corrected run [#1641](https://github.com/ncallahan/worldloom/actions/runs/38495329411), artifact ID `11862534646`)

Both artifacts contain identical measured counts. The final-SHA run's `stage3_rule_family_results.json` records the full-program ground-rule totals and the three family counts for `generated_pool` at 12, 30, and 100 people, with a 300-year horizon. The measurement does not change the ASP encoding.

Each named constraint's count is measured by incremental isolated grounding: ground its minimal supporting program, then ground that support program with the target constraint and take the difference. **Everything else is measured independently** by grounding the complete source with both target constraint templates removed; it is not computed by subtracting the two target counts from the full-program total. The counts below are taken directly from the artifact.

| People | Full-program ground rules | At-most-once ruler constraint | Non-kin succession constraint | Everything else (direct grounding) |
| ---: | ---: | ---: | ---: | ---: |
| 12 | 1,253,208 | 1,076,400 | 71,760 | 105,048 |
| 30 | 3,446,835 | 2,691,000 | 490,958 | 264,877 |
| 100 | 15,662,934 | 8,970,000 | 5,813,756 | 879,178 |

The at-most-once family is the ground instances of `:- start(L,P,Y), start(L,P,Z), Y < Z.` The non-kin family is the ground instances of the adjacent-year succession constraint that excludes parent/child-ineligible and non-sibling succession. At 100 people, the isolated measurement confirms the estimate of **8.97 million** at-most-once instances out of 15.66 million full-program rules. The directly measured “everything else” values happen to equal the arithmetic residual at all three sizes; the artifact's independent grounding run found no difference from that residual. Thus no grounding-simplification discrepancy was observed in these fixtures.

The CP-SAT model proto can count constraints by proto type (for example, `linear`, `bool_and`, `bool_or`, and `lin_max`), as shown in the construction table above, but does not retain semantic source-family labels. Therefore the current proto measurements cannot reliably attribute CP-SAT constraints to the corresponding ASP rule families without additional model-builder instrumentation.

**Interpretation — STILL OPEN (encoding finding, not a paradigm verdict).** The current ASP encoding has two large ground-rule families, especially the at-most-once ruler constraint, and its rule count grows substantially with the year horizon and pool size. This is a finding about this encoding and its grounding strategy, not evidence that ASP as a paradigm is unsuitable; nor do these counts establish that CP-SAT is preferable. Scale-related encoding growth remains open.

### Stage 4 stability baseline (final-SHA CI run [#1642](https://github.com/ncallahan/worldloom/actions/runs/38495816117), artifact `clingo-stage3-measurements`, artifact ID `11864415078`)

The existing three anchor changes are retained unchanged for comparison. Two additional weight-1 cases target A at year 20 and B at year 24. For each change and backend, the oracle enumerated 173 feasible solutions and found the minimum churn among all feasible solutions and among real-objective-optimal solutions. All 10 cases fit the oracle's limits; no churn-only solver fallback was needed. The artifact `stage4_stability_results.json` contains all 20 backend/change/weight rows. The measurement script round-trips the serialized JSON through `json.loads` and validates the change and row counts before writing the artifact; the final-SHA CI artifact was also loaded and parsed successfully. The tables below match its weight-0, weight-2, and weight-1000 rows.

The churn metric is the number of added plus removed `(layer,ruler,start,end)` facts across **both titular and effective layers**. The objective's stability term penalises **titular mismatches only**. Minimum real-objective-optimal churn is computed with stability disabled. “All feasible” is 0 for every row because the previous solution remains feasible after these soft-anchor-only changes; the more discriminating baseline is the minimum churn among real-objective-optimal solutions.

| Backend | Anchor change | Weight 0 | Weight 2 | Minimum over all feasible | Minimum among real-objective optima | Weight 1000 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| CP-SAT | soft-C-20 | 2 | 2 | 0 | 2 | 0 |
| CP-SAT | soft-B-24 | 4 | 2 | 0 | 4 | 0 |
| CP-SAT | soft-C-26 | 8 | 8 | 0 | 4 | 0 |
| CP-SAT | sensitive-A-20 | 0 | 0 | 0 | 0 | 0 |
| CP-SAT | sensitive-B-24 | 4 | 2 | 0 | 4 | 0 |
| clingo | soft-C-20 | 2 | 2 | 0 | 2 | 0 |
| clingo | soft-B-24 | 4 | 2 | 0 | 4 | 0 |
| clingo | soft-C-26 | 4 | 4 | 0 | 4 | 0 |
| clingo | sensitive-A-20 | 0 | 0 | 0 | 0 | 0 |
| clingo | sensitive-B-24 | 4 | 2 | 0 | 4 | 0 |

The three existing soft-C/B cases use weights 2, 2, and 4 respectively. Their missing-ruler penalties can be 62 or 124, so a stability weight of 2 is too small to reliably compete. The added `sensitive-A-20` and `sensitive-B-24` cases use soft-anchor weight 1, with the target ruler present; the corresponding soft penalties are small (the B-at-24 case has a real-objective optimum of 2, while a shifted/missing-B alternative incurs a modest penalty). These cases make the weight-2 trade-off observable without removing the original comparisons.

Real objectives below are evaluated under the **same changed problem with stability disabled**, so they are comparable. The final column is the changed-fact count at stability weight 1000, a weight chosen above the conservative upper bound for the real objective in these three-person, 31-year fixtures.

| Backend | Anchor change | Real objective, weight 0 | Real objective of weight-2 solution | Real objective of weight-1000 solution |
| --- | --- | ---: | ---: | ---: |
| CP-SAT | soft-C-20 | 0 | 2 | 62 |
| CP-SAT | soft-B-24 | 2 | 8 | 62 |
| CP-SAT | soft-C-26 | 6 | 8 | 124 |
| CP-SAT | sensitive-A-20 | 4 | 4 | 4 |
| CP-SAT | sensitive-B-24 | 2 | 6 | 31 |
| clingo | soft-C-20 | 0 | 2 | 62 |
| clingo | soft-B-24 | 2 | 8 | 62 |
| clingo | soft-C-26 | 6 | 12 | 124 |
| clingo | sensitive-A-20 | 4 | 4 | 4 |
| clingo | sensitive-B-24 | 2 | 6 | 31 |

The weight-2 results are not a universal reduction: `soft-C-20` cannot improve on the minimum churn of 2 among real-objective-optimal solutions; `sensitive-A-20` already has zero churn; and `soft-C-26` remains at 8 for CP-SAT while clingo remains at 4. For `soft-B-24` and `sensitive-B-24`, weight 2 reduces churn from 4 to 2 but accepts a worse real objective (2 to 8, or 2 to 6 respectively). Thus “helped” is a trade-off, not a free improvement.

At weight 1000, every case keeps the previous solution with zero changed facts, at the cost of the real-objective increases shown above. This is the intended dominance control for these bounded fixtures, not a recommended production weight.

**Cross-backend tie-selection finding.** For `soft-C-26` at weight 0, CP-SAT changes 8 facts while clingo changes 4, even though both solutions pass the independent checker and have the same real objective 6. The oracle finds real-objective-optimal solutions with churn 4. Thus clingo selected a lower-churn member of the tied optimal set while CP-SAT selected a different tied optimum; the count difference is evidence of tie selection, not a disagreement about feasibility or the real optimum. The same 8-versus-4 difference persists at weight 2, indicating that this weight does not pull CP-SAT to the lower-churn tied solution.

### CI record correction: merge commit `f3842f8`

The GitHub run record for [run #1620](https://github.com/ncallahan/worldloom/actions/runs/38485781198), whose PR head was `f3842f81181e8dec8e4d7fccb42a78253038da60`, has an overall conclusion of **cancelled**. At the job level, `lint`, `CP-SAT solver gate`, and `clingo ASP solver gate` had already concluded **failure**; the other completed non-coverage jobs succeeded, and the informational coverage job was cancelled. The earlier report mixed the overall run conclusion with those individual job conclusions. Correct wording: **the workflow run was cancelled overall, with three failed jobs recorded before cancellation**.

### Stage 4 completion boundary and open owner questions

Stage 4 is demonstrated only for the tested reconciliation lifecycle, checker-valid feasible/timeout incumbents, explicit promotion and its discriminating controls, objective/checker disagreement handling, the bounded construction measurements, and the bounded stability comparisons above. Construction and grounding were measured without solver search at 12, 30, and 100 people; **solving those scale instances remains unmeasured**. Encoding growth remains open, and the findings do not decide between solver paradigms.

Open questions for the owner (not implemented):

1. **Owner preference (deferred; not implemented in this PR):** when a problem returns to exactly the fingerprint that produced a retained projection's solution, reconcile should return `current` without re-solving. This remains deferred and is not implemented here.
2. There is no operation to move a `reopened` proposal to `current` after the GM accepts it. What explicit authorial acceptance operation and provenance should represent that transition?

**Stage 5 — NOT STARTED.** No Stage 5 work is claimed by this round.

## Scope

Experiment only. No changes to src/worldloom/, WorldState, engine integration, question pages, glossary, architecture pages, or current.md. No unresolved/projection representation decision is made. The brute-force enumerator is a test oracle only.

## Artifacts

- Code and raw results: `experiments/anchored_succession/`
- Tests: `tests/experiments/test_anchored_succession.py`

## Stage 2 comparison criterion

Implemented in `tests/experiments/test_anchored_succession_cp_sat.py`: compare solver results with the oracle by optimal objective value and by membership of each solver-selected solution in the oracle's optimal solution set, not by exact equality. The oracle's lexicographic tie-break and solver keyed perturbation may select different members of the same optimal set.


## Stage 3 — clingo / ASP adapter (provisional experiment)

The optional `clingo` extra pins `clingo==5.8.2`. The CPython 3.12 Linux CI job in run [#1626](https://github.com/ncallahan/worldloom/actions/runs/38487233516) installed and recorded the following dependency chain from distribution metadata using `python -m pip inspect` (artifact: `stage3_pip_inspect.json`):

| Package | Resolved version | Relationship | Licence metadata |
| --- | --- | --- | --- |
| clingo | 5.8.2 | Direct optional dependency | `License: MIT` |
| cffi | 2.1.1 | Direct dependency of clingo | `License-Expression: MIT-0` |
| pycparser | 3.11 | Transitive via cffi on CPython | `License-Expression: BSD-3-Clause` |

The metadata reports `clingo` requiring `cffi`, and `cffi` requiring `pycparser` except on PyPy. This table records the actual CI resolution, not every platform's conditional dependency set.

The ASP encoding uses lexicographic optimization priorities: the unperturbed real objective is at priority 2 and keyed `rng_for`-derived tie-breaking is at priority 1. This intentionally differs from CP-SAT's subordinate integer scaling. Cross-backend selected solutions are recorded for comparison; only feasibility, optimal objective, and membership in the oracle's optimal set are required for cross-backend correctness. Grounding size/time is reported for these toy scenarios only; no scale claim is made.

Infeasible anchor cores are obtained from clingo's solve assumptions, then deletion-checked for subset-minimality. Smallest anchor-removal sets are exploratory authorial decision support; the adapter first disables every non-soft anchor and reports infeasibility independent of anchors if that baseline remains infeasible.


### Stage 3 CI results (run [#1626](https://github.com/ncallahan/worldloom/actions/runs/38487233516); UTC date 2026-10-13; clingo 5.8.2)

Grounding size is the number of grounded symbolic atoms and normal/choice rules counted by the clingo observer; times are seconds from this exact CI run's `stage3_clingo_results.json` artifact. These tiny synthetic scenarios are not a scale benchmark.

| Scenario | Case | Status / unperturbed objective | Ground atoms | Ground rules | Grounding (s) | Solve (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Hard anchors only | solved / 0 | 1,644 | 6,051 | 0.020603 | 0.001779 |
| 2 | Conflicting hard anchors | infeasible | 1,090 | 4,180 | 0.020017 | 0.001210 |
| 3 | Soft-anchor tolerance | solved / 0 | 676 | 2,105 | 0.008163 | 0.001390 |
| 4 | Reveal only | solved / 0 | 1,095 | 4,093 | 0.013563 | 0.001275 |
| 5 | Repeatability | solved / 0 | 1,667 | 6,086 | 0.019346 | 0.001934 |
| 6 | Declaration shuffle, seed 3 | solved / 0 | 1,667 | 6,086 | 0.020830 | 0.003628 |
| 6 | Declaration shuffle, seed 17 | solved / 0 | 1,667 | 6,086 | 0.019458 | 0.003096 |
| 6 | Declaration shuffle, seed 2026 | solved / 0 | 1,667 | 6,086 | 0.019478 | 0.002345 |
| 6 | Declaration shuffle, seed 91003 | solved / 0 | 1,667 | 6,086 | 0.019689 | 0.002355 |
| 7 | Hard anchors | solved / 0 | 1,644 | 6,051 | 0.019647 | 0.001838 |
| 7 | Reveal only | solved / 0 | 1,095 | 4,093 | 0.013716 | 0.001443 |
| 7 | Soft tolerance | solved / 0 | 676 | 2,105 | 0.007980 | 0.001369 |
| 7 | Conflicting anchors | infeasible | 1,090 | 4,180 | 0.014344 | 0.001172 |
| 7 | Marked record/reveal | solved / 0 | 1,096 | 4,106 | 0.013374 | 0.001209 |
| 7 | Sibling and stability costs | solved / 26 | 1,707 | 6,106 | 0.019846 | 0.001754 |

Scenario 2's assumption core was `{pin-A, pin-B}`; deletion checks established subset-minimality. The two smallest removal suggestions were `{pin-A}` and `{pin-B}`, each restoring feasibility with objective 0. They remain exploratory authorial interventions.

**Scenario 6:** CP-SAT and clingo each returned the same selected solution and objective as their own canonical-order run for all four shuffled seeds. The two backends also selected the same solution on this feasible scenario.

**Scenario 7:** across six tiny cross-backend cases, both backends agreed with the oracle on feasibility and optimal objective, and each feasible solver result belonged to the oracle's optimal-solution set. No disagreement findings were recorded. For the infeasible case, neither backend returns a solution, so selected-solution equality is not applicable. The selected solutions also happened to agree between CP-SAT and clingo in all five feasible cases; this is an observation, not the cross-backend acceptance criterion.

The raw `stage3_clingo_results.json`, `stage3_pip_inspect.json`, `stage4_construction_size.json`, and `stage4_stability_results.json` files all came from CI run [#1626](https://github.com/ncallahan/worldloom/actions/runs/38487233516). The combined artifact expires after 30 days (2026-11-13 UTC). The table timings above are from this run only; they are not borrowed from earlier runs.

**Tie-sensitive order-independence follow-up:** scenario 5/6's original unique-optimum cases alone could not establish tie-breaking invariance. The dedicated two-soft-window single-ruler case confirmed a multi-member oracle-optimal set, unchanged selection under four declaration/model shuffles for each backend, and variation across ten distinct `problem.seed` values as a positive control. For the baseline and every tested problem seed, the minimum keyed tie weight among oracle-optimal solutions was unique for each backend; no residual minimum-weight collisions were found. CP-SAT and clingo use different keyed coefficient sets, so their selected tied solutions may legitimately differ between backends. Each backend's selected solutions passed its oracle membership and unperturbed-objective checks.


## Stage 5 — succession encoding experiment (provisional)

This stage changes only experiment-local solver encodings. The original pairwise rules remain selectable as `legacy` parity references; improved encodings are not adopted as normative architecture.

### Hypotheses and encodings

**CP-SAT `linear-successor`.** The legacy encoding forbids each disallowed ordered pair of rulers across each adjacent year. The improved encoding adds one constraint for each `(layer, previous ruler p, year y)`:

`presence[p,y] - presence[p,y+1] <= sum(presence[q,y+1] for allowed successors q) + (1 - occupied[y+1])`

Allowed successors are children or siblings. Under the existing at-most-one-ruler and occupancy-equivalence constraints, this is intended to be equivalent to the pairwise exclusions: if p leaves an occupied throne, the incoming ruler must be an allowed successor; if the throne is empty, no successor is required. This equivalence remains a hypothesis until the Stage 5 CI parity tests pass across the oracle pool.

**clingo `aggregate-successor`.** The legacy rule preventing multiple reign starts per person is pairwise over start years. The improved rule uses a per-person aggregate count. Succession is expressed using `end(L,P,Y)` and the next year's occupant, with `succ(P,Q)` defined from child and sibling facts. This is intended to ground by layer/person/year rather than by all person pairs. Both rules remain selectable for parity checks.

### Verification plan

- Compare each improved encoding against its legacy counterpart on the same small oracle cases and seeded generated pools. Compare feasibility, real objective, checker validity, and membership in the oracle's optimal set; do not require tied solutions to be identical.
- The construction harness accepts `--encoding both`; the solver CI job emits `stage5_construction_size.json` alongside the historical Stage 4 artifact. This measures construction/grounding only, not solve performance.
- The bounded solve harness uses a 60-second per-solve limit and a deterministic three-anchor set sampled with `rng_for`. The three overlapping anchors pin P0 over a five-year union, chosen within P0's age/death bounds so the benchmark anchor set is feasible by construction. It records backend status, real objective, wall time, peak RSS, and clingo grounding/solve timings. CP-SAT also runs a diagnostic solve without the tie-break multiplier to compare time and objective.
- The hard-anchor-pair report samples three pairs per seed for three seeds at each pool size; each pair uses different people and different years. It records proven infeasibility separately from timeout/unknown and reports the feasible fraction only among decided cases. These random pairs are a stress sample, not a claim that the generator's arbitrary anchors are normally feasible.
- CI results and measured counts are intentionally not asserted here until a final-commit run and its artifacts can be inspected. The pre-existing Stage 4 table remains the historical baseline and must not be replaced with measurements from another run.

### Stage 5 CI verification

The parity tests and both solver gates passed in CI run [#1665](https://github.com/ncallahan/worldloom/actions/runs/38555379556), head commit `513718e47b54554bf52b19823c503f8226109662`. The run's dedicated Stage 5 measurement job also completed successfully and uploaded artifact `anchored-succession-stage5-measurements` (artifact ID `11890656822`) containing `stage5_solve_results.json` and `stage5_anchor_pair_results.json`. The clingo solver-gate artifact `clingo-stage3-measurements` (artifact ID `11890001407`) contains `stage5_construction_size.json`. The results are summarized in the final Stage 5 evidence section below.

**DEMONSTRATED, within the tested scope:** legacy/improved parity tests passed; the measured alternative encodings materially reduce construction/grounding size for generated pools of 12, 30, and 100 people; the six 300-year solve cases all solved within their 60-second per-solve limit with objective 0; and CP-SAT's no-multiplier diagnostic also returned objective 0 in all three pools.

**STILL OPEN:** broad external validity beyond the generated pools/rules and fixed anchor procedure; the cause/general prevalence of arbitrary hard-anchor conflicts; and 100-person clingo hard-anchor-pair results, because that batch hit the harness's wall-clock guard before completing. The evidence does not justify a solver-paradigm verdict.


## Stage 5 — alternative succession encodings (provisional)

Status: **measured; experiment remains provisional**. CI run [#1665](https://github.com/ncallahan/worldloom/actions/runs/38555379556) passed the parity tests and both solver gates. The existing pairwise encodings remain selectable as parity baselines; the alternatives are opt-in and do not change the default.



### Stage 5 final-commit measurements (CI run [#1665](https://github.com/ncallahan/worldloom/actions/runs/38555379556), head `513718e47b54554bf52b19823c503f8226109662`)

The construction artifact used a 300-year horizon and three hard anchors. Construction/grounding measurements do not invoke solver search. “Succession-family size” is the analytic number of pairwise exclusions for the legacy encoding and the corresponding per-ruler/year family for the improved encoding; it is not a direct clingo rule-family observer count.

| People | Backend / encoding | Build or program-build (s) | Constraints / ground rules | Proto bytes / ground atoms | Grounding (s) | Peak RSS (MiB) |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 12 | CP-SAT legacy | 0.736 | 110,340 constraints | 3,829,767 proto bytes | — | 133.9 |
| 12 | CP-SAT linear-successor | 0.543 | 45,756 constraints | 2,260,588 proto bytes | — | 114.5 |
| 12 | clingo legacy | 0.094 | 1,253,220 ground rules | 53,312 atoms | 1.749 | 44.7 |
| 12 | clingo aggregate-successor | 0.094 | 113,480 ground rules | 53,312 atoms | 0.928 | 53.4 |
| 30 | CP-SAT legacy | 2.790 | 600,310 constraints | 19,480,109 proto bytes | — | 304.4 |
| 30 | CP-SAT linear-successor | 1.362 | 127,292 constraints | 6,801,400 proto bytes | — | 160.0 |
| 30 | clingo legacy | 0.226 | 3,446,884 ground rules | 140,316 atoms | 4.750 | 66.9 |
| 30 | clingo aggregate-successor | 0.229 | 291,956 ground rules | 140,316 atoms | 2.436 | 90.6 |
| 100 | CP-SAT legacy | 23.031 | 6,184,048 constraints | 186,853,178 proto bytes | — | 2,106.4 |
| 100 | CP-SAT linear-successor | 6.459 | 430,092 constraints | 23,736,147 proto bytes | — | 326.4 |
| 100 | clingo legacy | 0.781 | 15,663,112 ground rules | 471,592 atoms | 19.900 | 162.7 |
| 100 | clingo aggregate-successor | 0.730 | 971,250 ground rules | 471,592 atoms | 8.223 | 237.0 |

Relative to legacy at the same pool size, the CP-SAT improved encoding reduced total model constraints by **58.5%, 78.8%, and 93.0%** at 12, 30, and 100 people, respectively. Its serialized model proto shrank by **41.0%, 65.1%, and 87.3%**. The clingo improved encoding reduced ground rules by **90.9%, 91.5%, and 93.8%**, and grounding time by **46.9%, 48.7%, and 58.7%**. Ground atom counts were unchanged in each legacy/improved pair. The improved encodings also reduced the measured succession-family size from 71,760 / 490,958 / 5,813,756 to 7,176 / 17,940 / 59,800 across the three pool sizes.

These are construction/grounding results for this experiment's generated pools, rules, and 300-year horizon. They do not imply equivalent reductions in solve time for arbitrary problems.

#### 300-year solve measurements

The solve harness used one deterministic anchor sample per pool size, generated with `rng_for`; three overlapping interval anchors pin P0 over a five-year union. Each solve had a 60-second limit. All six primary solves returned a solution and real objective 0. Times below are seconds; RSS is peak resident set size from the worker process, reported in MiB (bytes divided by 1024²).

| People | Backend / encoding | Status / objective | Wall time (s) | Peak RSS (MiB) | Clingo grounding (s) | Clingo solve (s) |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 12 | CP-SAT linear-successor | solved / 0 | 3.827 | 154.2 | — | — |
| 12 | clingo aggregate-successor | solved / 0 | 2.166 | 91.7 | 1.848 | 0.131 |
| 30 | CP-SAT linear-successor | solved / 0 | 5.649 | 239.1 | — | — |
| 30 | clingo aggregate-successor | solved / 0 | 5.564 | 190.1 | 4.780 | 0.335 |
| 100 | CP-SAT linear-successor | solved / 0 | 40.398 | 609.4 | — | — |
| 100 | clingo aggregate-successor | solved / 0 | 19.293 | 568.2 | 16.054 | 1.786 |

The CP-SAT no-multiplier diagnostic also solved all three cases with objective 0: 1.633 s at 12 people, 2.574 s at 30, and 19.961 s at 100, versus 3.827 s, 5.649 s, and 40.398 s with the multiplier. This is a single diagnostic comparison per size, so it suggests the multiplier has measurable overhead here but is not a general timing conclusion.

#### Hard-anchor-pair feasibility sample

The harness sampled three pairs per seed for three seeds (20261014, 20261015, 20261016), at each pool size. Each pair pinned different people in different years. Each individual solve had a 5-second limit. The sample was generated as a stress test of arbitrary hard anchors, not from a distribution known to represent normal user-authored inputs.

| People | Backend / encoding | Completed pair samples | Proven infeasible | Feasible | Timeout/unknown | Result |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 12 | CP-SAT linear-successor | 9 | 9 | 0 | 0 | 0/9 feasible |
| 12 | clingo aggregate-successor | 9 | 9 | 0 | 0 | 0/9 feasible |
| 30 | CP-SAT linear-successor | 9 | 9 | 0 | 0 | 0/9 feasible |
| 30 | clingo aggregate-successor | 9 | 9 | 0 | 0 | 0/9 feasible |
| 100 | CP-SAT linear-successor | 9 | 9 | 0 | 0 | 0/9 feasible |
| 100 | clingo aggregate-successor | 0 | 0 | 0 | 0 | Batch harness timeout before per-pair results |

At 100 people, the CP-SAT batch completed all nine samples and proved all nine infeasible. The clingo batch exceeded the harness wall-clock guard at about 145 seconds and produced only a batch-level `harness_timeout` record; **there are no valid per-pair results for that backend/size**. That batch timeout is not evidence that any individual anchor pair is infeasible or that an individual solve exceeded its own limit.

The 45 completed pair samples all proved infeasibility, with no feasible or timeout/unknown individual results among those completed. This indicates that the sampled arbitrary cross-person/cross-year hard anchors are highly conflict-prone under these rules, but the sampling is small and deliberately adversarial; it must not be interpreted as an estimate of the feasibility rate of GM-authored anchors. The 100-person clingo gap remains open.

Raw measurement JSON was produced by CI run #1665. GitHub Actions artifacts are retained temporarily; this page preserves the summarized results so that conclusions do not depend on artifact availability.

### Encoding changes under test

- CP-SAT `linear-successor`: replace the disallowed-pair family with one implication per layer, previous ruler, and adjacent year. Given at-most-one occupancy and the equivalence between `occupied(L,Y)` and the sum of that year's presence variables, the intended constraint is `presence(p,y) - presence(p,y+1) <= sum(allowed_successor_presence(q,y+1)) + 1 - occupied(y+1)`. If p's reign ends and the next year is occupied, an allowed child/sibling successor must occupy it; an empty next year is allowed. This derivation still requires exhaustive small-instance parity evidence.
- clingo `aggregate-successor`: replace the pairwise multiple-start prohibition with a per-person/layer aggregate, and express succession at a reign end using a child/sibling successor relation. The original rules remain selectable for parity comparison.

### Evidence ledger

| Criterion | Status | Evidence |
|---|---|---|
| Legacy encodings preserved | DEMONSTRATED | `legacy` remains selectable and default; the improved alternatives are opt-in |
| Improved encoding equals legacy/oracle on small instances | DEMONSTRATED for tested fixtures | CP-SAT and clingo parity tests, generated-pool tests, independent checker, objective evaluator, and oracle optimal-set checks passed in CI run #1665; tied solutions need not be identical |
| Construction size at 12/30/100 people | DEMONSTRATED for measured generated pools | See the comparative construction table below; each improved encoding sharply reduces its measured constraint/rule family and overall construction size |
| 300-year solve scale | DEMONSTRATED for this fixed feasible anchor set | All six backend/pool-size cases solved with objective 0 within 60 seconds; this is one deterministic sample per size/backend, not broad performance evidence |
| Hard-anchor-pair feasibility report | PARTIAL | 9/9 sampled pairs were proven infeasible for each backend at 12 and 30 people, and CP-SAT proved 9/9 infeasible at 100 people. The 100-person clingo batch hit the harness wall-clock guard and yielded no per-pair outcomes |
| Tie-break multiplier diagnostic | DEMONSTRATED for these three samples | CP-SAT with and without multiplier returned objective 0 at all sizes; the no-multiplier diagnostic was faster in each single run |
| Reconcile retained-solution reuse | DEFERRED | Optional owner-preferred behavior remains unimplemented and outside this Stage 5 scope |

These results support a construction/grounding improvement for the two tested alternative encodings, and successful solves for the fixed feasible anchors used here. They do not establish general feasibility rates for arbitrary hard anchors, broad scale performance, or superiority of one solver paradigm. Timeouts and unknown outcomes remain inconclusive findings, not proof of infeasibility.
