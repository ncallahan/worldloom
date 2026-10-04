---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Events And History

## 9. Events

Events are first-class records. An event may:

- change canonical state
- trigger dependent modules
- resolve an uncertainty
- record an external or endogenous occurrence
- carry provenance and uncertainty

This allows long-running simulations to explain how present state emerged from earlier state transitions.

## 5. Events

Events SHALL be representable as persistent records with enough information to identify their time, effects, and provenance.

### Time and events

Do not assume one universal simulation timestep. Different domains naturally operate at different temporal resolutions, and the orchestrator should schedule work accordingly.

Events are first-class records and may change state, trigger dependent work, resolve uncertainty, or record external/endogenous occurrences.
