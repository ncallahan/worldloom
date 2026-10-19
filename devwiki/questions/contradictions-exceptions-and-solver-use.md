---
type: question
status: open
summary: Owner stance and open design questions for contradiction handling, exceptions, and solver use.
related: ["[[devwiki/index]]", "[[devwiki/questions/anchored-history-reconciliation]]", "[[devwiki/questions/resolution-attempt-outcomes]]", "[[devwiki/experiments/anchored-succession-reconciliation]]"]
---

# Contradictions, exceptions, and solver use

## Owner stance

- **OWNER DECISION** — Worldloom should generally avoid using constraint solvers, but be liberal and allow exceptions to be put in place with explanations.
- **OWNER DECISION** — It is a fictional world: fictional solutions, or solutions that do not map to the parameters Worldloom tracks, are acceptable.
- **OWNER DECISION** — Highlighting contradictions is more important than solving them.
- **OWNER DECISION** — Finding constrained solutions remains an important ability.
- **OWNER DECISION** — The owner likes the ideas of solving local questions and of cheap pre-checks.

## Experiment evidence (not architecture)

The following records evidence from Stage 5 of [[devwiki/experiments/anchored-succession-reconciliation]]; it is experiment evidence, not an architecture decision.

- **FACT** — A graph-reachability check identified 15 of 20 generated larger instances as having no kin path between anchored rulers, without using a solver.
- **FACT** — The other five instances were infeasible because of a fixture defect, established by a hand argument rather than a solver conflict core.
- **FACT** — Solver-emitted conflict cores and exact removal sets were checked only on tiny cases.
- **FACT** — Stage 5 compared no feasible larger instance.
- **FACT** — The planted-chain parity results at 12, 30, and 100 people use one planted structure at three pool sizes.
- **FACT** — Timeouts and unknown solver outcomes are inconclusive and do not prove infeasibility.

## Possible direction for confirmation

The items below are options for owner confirmation, not settled design.

- **PROPOSED (pending owner confirmation)** — Make contradiction detection and explanation the primary contract, with solving as an opt-in capability that is never run by default.
- **PROPOSED (pending owner confirmation)** — Run cheap pre-checks before any solver, with reachability, age/lifespan eligibility, and interval overlap as examples to consider.
- **PROPOSED (pending owner confirmation)** — Solve local questions, such as a region, layer, or interval, with outer constraints used as anchors rather than solving the whole world at once.
- **PROPOSED (pending owner confirmation)** — Keep solver outputs as projections, with any promotion to canonical state explicit and separate.
- **PROPOSED (pending owner confirmation)** — Investigate whether hard anchors can decompose a problem into independent segments; this has not been tested.
- **PROPOSED (pending owner confirmation)** — Consider an exception as a first-class, authored record with an explanation.
- **PROPOSED (pending owner confirmation)** — One possible exception meaning is waiving a rule at a specific place.
- **PROPOSED (pending owner confirmation)** — A distinct possible exception meaning is marking a fact as outside the parameters Worldloom checks.
- **FACT** — Soft anchors already exist as a concept in anchored-history reconciliation; see [[devwiki/questions/anchored-history-reconciliation]].
- **OPEN** — Whether waiving a rule at a specific place and marking a fact outside checked parameters are separate concepts remains open.

## Open questions

- **OPEN** — Exception lifetime: does an exception survive reopening of projections, or must it be re-validated when anchors change?
- **OPEN** — Is an exception canonical state or a provenance annotation on a fact?
- **OPEN** — What is the minimal useful set of cheap pre-checks?
- **OPEN** — May a result with no proven status ever be promoted to canon, given that the current reconciliation design treats timeouts as inconclusive?
- **OPEN** — How should exceptions interact with Hand-of-God interventions and soft anchors?

## Related pages

- **FACT** — [[devwiki/questions/anchored-history-reconciliation]] records the existing owner decisions about infeasibility, Hand-of-God interventions, soft anchors, and solver use; this page does not restate that page's full treatment.
- **FACT** — [[devwiki/experiments/anchored-succession-reconciliation]] records the Stage 5 experiment evidence and its limitations.
