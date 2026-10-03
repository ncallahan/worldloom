---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## Competing canonical-state producers experiment

### Question

What happens when multiple independent modules write the same canonical field, and does the current model provide an ownership or arbitration rule for that shared output?

### Method

Two deterministic toy producer modules both declare `field:shared.value` as an output, but write distinguishable values. A consumer declares the same field as its input. The experiment runs the same three modules twice, reversing the producer order between runs.

No routing, validation, ownership, or identifier mechanism is added.

### Measurements / results

The final canonical value is the value written by the producer that executes last. Reversing the producer order therefore reverses the final value seen by the consumer.

The experiment demonstrates that the earlier model permitted multiple writers to the same field without detecting the collision.

### Interpretation

**Demonstrated**

The pre-ownership model had no intrinsic single-producer rule for canonical field names. When competing producers wrote the same field, ordinary execution order determined which value remained in `WorldState`.

This result is superseded for the ownership experiment by the provisional EXCLUSIVE rule documented below: canonical outputs now default to EXCLUSIVE, so two producers declaring the same non-event output are rejected during declaration-time validation rather than arbitrated by execution order.

This supersession is intentionally limited. It does not establish a general validation framework, and it does not retroactively change the historical result recorded by this experiment.

**Still open**

This earlier experiment does not decide:

- whether a canonical output should have exactly one producer;
- whether multiple producers should coexist under distinct semantic identities;
- whether arbitration or composition belongs in module contracts, scheduling, or another layer;
- whether competing outputs should be represented as separate values and combined explicitly;
- what provenance should mean when several producers contribute to one resulting value.

The ownership experiment addresses only a provisional subset of these questions.

### Scope

This section records the historical last-writer-wins behaviour observed before ownership declarations were introduced. It is not a proposal that last-writer-wins should become Worldloom architecture.
