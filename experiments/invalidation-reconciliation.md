---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## Invalidation and reconciliation experiment

### Question

When a resolved canonical fact depends on a derived observation, can Worldloom detect that the upstream observation has changed without automatically changing the resolved fact?

### Method

A deterministic toy resolution path creates a `settlement.candidates` observation, resolves the highest-scoring candidate into persistent `settlement:001` state, then replaces the observation with changed scores that would select a different candidate.

The experiment records the observation fingerprint before and after the change and inspects the resolved entity's provenance. A separate snapshot preserves the earlier observation provenance so the two versions can be compared explicitly.

No invalidation, stale-state marker, reconciliation mechanism, or production API is added.

### Measurements / results

The experiment verifies that:

- replacing an observation changes its stored provenance fingerprint;
- the resolved entity remains unchanged when its source observation changes;
- the entity provenance identifies the observation by semantic name;
- the entity provenance does not currently retain the fingerprint or version of the particular observation value that informed the resolution;
- a snapshot can preserve the earlier observation provenance, allowing an external process to compare the old and current fingerprints.

### Interpretation

**Demonstrated**

Worldloom can detect that an observation's current value differs from a previously captured version when the earlier provenance is retained. The existing provenance link also identifies that a resolved fact depends on the observation.

However, the live resolved fact does not itself contain enough information to determine, from current state alone, whether the observation version that informed it has changed. Its provenance records the observation name and the fact's own fingerprint, but not the source observation's historical fingerprint.

The current behaviour therefore preserves canonical stability but does not provide automatic invalidation or reconciliation semantics.

**Still open**

This experiment does not decide:

- whether provenance should retain source-version fingerprints;
- whether observations should have explicit versions or immutable history;
- whether invalidation should be explicit, provenance-driven, event-driven, or on-demand;
- whether a changed observation should mark a resolved fact stale;
- whether stale facts should be removed, replaced, retained with a status, or reconciled by a new resolution process;
- how changes should propagate through multiple layers of derived observations;
- whether snapshots, provenance history, or another mechanism should provide the comparison baseline.

### Scope

This is a feasibility and information-availability experiment. It deliberately does not introduce an invalidation mechanism or make a policy decision about what Worldloom should do when an upstream dependency changes.
