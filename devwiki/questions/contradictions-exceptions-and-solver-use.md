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
- **OWNER DECISION** — Something becomes canon when it is published as fact / stated as fact to the audience (players/readers).
- **OWNER DECISION** — This applies to an unproven (no proven status) solver result as well: an unproven result becomes canon if and only if it is so stated.
- **OWNER DECISION** — Until something is actually given to the audience, it is not canon in principle.
- **OPEN** — In practice there are probably linchpins: facts that would alter the world too much or cause inconsistencies if changed before they are given to the audience. This is an owner remark, not a settled decision.

## Experiment evidence (not architecture)

- **FACT** — The following is experiment evidence from Stage 5 of [[devwiki/experiments/anchored-succession-reconciliation]], not an architecture decision.
- **FACT** — A graph-reachability check identified 15 of 20 generated larger instances as having no kin path between anchored rulers, without a solver.
- **FACT** — The other five instances were infeasible by a fixture defect, established by a hand argument rather than a solver conflict core.
- **FACT** — Solver-emitted conflict cores and exact removal sets were checked only on tiny cases.
- **FACT** — Stage 5 compared no feasible larger instance.
- **FACT** — The planted-chain parity results at 12, 30, and 100 people use one planted structure at three pool sizes.
- **FACT** — Timeouts and unknown solver outcomes are inconclusive and do not prove infeasibility.

## Possible direction for confirmation

- **PROPOSED (pending owner confirmation)** — Make contradiction detection and explanation the primary contract, with solving as an opt-in capability that is never run by default.
- **PROPOSED (pending owner confirmation)** — Run cheap pre-checks before any solver, with reachability, age/lifespan eligibility, and interval overlap as examples to consider.
- **PROPOSED (pending owner confirmation)** — Solve local questions, such as a region, layer, or interval, with outer constraints used as anchors rather than solving the whole world at once.
- **PROPOSED (pending owner confirmation)** — Keep solver outputs as projections, with any promotion to canonical state explicit and separate.
- **PROPOSED (pending owner confirmation)** — Investigate whether hard anchors can decompose a problem into independent segments; this has not been tested.
- **PROPOSED (pending owner confirmation)** — Consider an exception as a first-class, authored record with an explanation.
- **PROPOSED (pending owner confirmation)** — One possible exception meaning is waiving a rule at a specific place.
- **PROPOSED (pending owner confirmation)** — A distinct possible exception meaning is marking a fact as outside the parameters Worldloom checks.
- **PROPOSED (pending owner confirmation)** — Stating something as fact to the audience could count as the explicit, provenance-retaining promotion required by architecture.
- **PROPOSED (pending owner confirmation)** — Record "stated as fact to the audience" as an event, without modelling table/session time; the distinction between historical events and process events is already provisional.
- **FACT** — Soft anchors already exist as a concept in anchored-history reconciliation; see [[devwiki/questions/anchored-history-reconciliation]].
- **OPEN** — Whether waiving a rule at a specific place and marking a fact outside checked parameters are separate concepts remains open.
- **OPEN** — Whether stating something as fact to the audience is itself the required promotion act, or whether promotion needs a separate act, remains open.

## Terminology boundary

- **OPEN** — The architecture uses "derived observation" for a calculation from canonical state or other declared inputs, and "canonical state" for authoritative simulated reality.
- **OPEN** — "Stated as fact to the audience" means audience commitment in the owner's description and must remain visibly distinct from the architecture term "derived observation".
- **OPEN** — Whether the owner's notion of canon (audience-committed) and the architecture's "canonical state" are one concept, two concepts, or one refining the other is unresolved here; this page does not reconcile them.

## Open questions

- **OPEN** — Exception lifetime: does an exception survive reopening of projections, or must it be re-validated when anchors change?
- **OPEN** — Is an exception canonical state or a provenance annotation on a fact?
- **OPEN** — What is the minimal useful set of cheap pre-checks?
- **OPEN** — When a new or changed anchor conflicts with something already stated as fact to the audience, what does the system do, and who resolves it (Hand-of-God, an exception, a retcon)? How does this relate to "reopen vs obsolete"?
- **OPEN** — How are linchpins identified or represented, if at all?
- **OPEN** — Does the solver-status vocabulary (proven optimal, feasible-unproven, timeout) need to be recorded alongside a fact that was stated to the audience while unproven?
- **OPEN** — How is audience publication recorded without modelling session time?
- **OPEN** — How should exceptions interact with Hand-of-God interventions and soft anchors?

## Related pages

- **FACT** — [[devwiki/questions/anchored-history-reconciliation]] records the existing owner decisions about infeasibility, Hand-of-God interventions, soft anchors, and solver use; this page does not restate that page's full treatment.
- **FACT** — [[devwiki/experiments/anchored-succession-reconciliation]] records the Stage 5 experiment evidence and its limitations.
