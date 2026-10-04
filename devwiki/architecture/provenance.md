---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Provenance

## 10. Provenance

Worldloom should retain enough provenance to answer questions such as "Why does the world believe this?"

A derived value should be traceable to its producing module/version, inputs, event history, simulation time, configuration, and confidence/uncertainty where applicable.

Progressive resolution adds a further requirement: when a provisional result becomes canonical, its provenance should preserve the relationship between the resolved fact and the information or process from which it was resolved.

## 7. Provenance

Derived state SHOULD retain provenance sufficient to identify its producer, inputs, configuration, simulation time, and uncertainty/confidence where available.

Resolved state SHOULD retain provenance that explains the transition from provisional or derived information to persistent fact.

### Provenance matters

Derived state should be traceable to its producer, inputs, configuration, simulation time, and uncertainty/confidence where available.

The system should eventually make it possible to ask:

> Why does the world believe this?
