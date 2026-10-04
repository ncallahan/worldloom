---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## Canonical-state data routing and propagation experiment

### Question

Can the current dependency-aware engine exchange data between modules through canonical Worldloom state across direct chains, fan-out, state → observation → resolution boundaries, and differing temporal cadences without introducing an explicit routing layer?

### Method

A small Python-only experiment harness defines deterministic toy modules with explicit semantic input/output contracts. The modules exchange values only through `WorldState`; no module calls another module directly and no general router is added.

The harness tests four shapes:

- A → B state propagation;
- A → B + C fan-out from one state output;
- A → B → C chained propagation;
- state → observation → resolution into a persistent entity and event.

A fifth test runs producer/consumer modules at different fixed temporal intervals to observe which previously-produced value a slower consumer receives.

### Measurements / results

The experiment records whether:

- dependency ordering is sufficient to make upstream outputs available to downstream modules;
- one canonical state value can be consumed by multiple downstream modules;
- state can cross multiple dependency edges without direct module-to-module calls;
- the state/observation boundary remains explicit before resolution creates persistent state;
- a slower module consumes the latest available canonical output rather than requiring a same-timestep message.

### Interpretation

**Demonstrated**

The current Worldloom execution model is sufficient for these small routing shapes without a general data-routing mechanism. Module dependencies determine execution order, while canonical field/observation names provide the data exchange surface.

Fan-out requires no special mechanism: multiple modules can independently consume the same canonical output. Chaining likewise requires no intermediate router.

The cadence test demonstrates a useful current semantic: with fixed intervals, a slower consumer reads the value currently present in canonical state. It therefore can consume an upstream result produced at an earlier simulation time.

**Still open**

This experiment does not settle:

- whether canonical field names are sufficient when multiple module instances provide competing values;
- how explicit routing should work when several producers or consumers share related semantic names;
- whether dependencies and data contracts should be validated against the actual world state;
- whether consumers should be allowed to read stale upstream values across temporal cadences;
- how event-triggered propagation should interact with fixed-interval scheduling;
- how invalidation and recomputation should operate when an upstream value changes;
- identifier semantics;
- a general validation architecture.

### Scope

This is deliberately an experiment, not a proposal for a general router or a final composition model. The harness and tests exist to expose current engine behaviour before those broader architectural decisions are made.
