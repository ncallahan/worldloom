---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Progressive Generation And Resolution

## 1. Purpose

Worldloom provides the **loom**, not every thread. It is an orchestration and interoperability layer for constructing persistent computational worlds from specialised systems.

The architecture should make it possible to combine existing geospatial, environmental, demographic, economic, linguistic, social, historical, numerical, and visualisation systems without requiring those systems to become one monolithic simulator.

Worldloom is also a **progressive procedural world model**. It should be possible to obtain a useful broad representation of a world quickly, without first resolving every local detail or simulating its entire history. As the world is explored, queried, edited, or required by another process, selected parts can be resolved to greater detail and made persistent.

The architectural principle is:

> **Generate broadly; resolve deeply where needed.**

This is a system property, not merely a performance optimisation.

## 4. State, observation, and provisional information

The canonical state is authoritative simulated reality. A derived observation is a calculation made from canonical state or other declared inputs. Storing an observation does not promote it to world state.

Promotion is explicit: an observation may inform a resolution or simulation process that creates a persistent fact, with provenance linking the new fact to the observation and its underlying inputs.

The prototype represents this distinction directly: WorldState.fields and WorldState.entities hold canonical state, while WorldState.observations holds derived observations. ModuleSpec uses OutputSpec and DataKind to declare output semantics.

Worldloom also needs to represent information that is useful before it has been resolved into a concrete persistent fact. This may include broad statistical projections, candidate entities, probability distributions, or other provisional descriptions. **The representation of this information is intentionally not yet fixed.**

In particular, the architecture does not currently decide whether provisional information should be represented as:

- a special form of observation;
- first-class provisional state;
- generator/prior information from which canonical state is resolved;
- or another mechanism.

The important current requirement is behavioural: provisional information must be usable to produce a useful world representation, and selected portions must be able to become persistent facts without requiring unrelated portions of the world to be fully resolved.

## 7. Projection and resolution

Worldloom should distinguish two related activities:

**Projection** produces a broad, useful representation of what the world probably looks like. It may be generated at coarse spatial or temporal resolution and may contain unresolved or statistical information. Projection should be cheap enough that a user can obtain something useful to inspect without waiting for complete world generation.

**Resolution** turns selected provisional or uncertain information into concrete persistent facts. Resolution may be requested because a user asks about something, edits the world, a simulation step requires the information, or another module depends on it.

For example:

    broad world projection
      terrain / climate / broad regions
                |
                v
        user explores a river
                |
                v
       local hydrology resolved
                |
                v
       settlement history queried
                |
                v
      local demographic facts resolved

Resolution is selective. Unrelated parts of the world should not need to be fully resolved before a local question can be answered.

A resolved result becomes part of the world's history. Later modules consume that fact rather than independently resampling it.

## 8. Statistical states and resolution

A world may begin with uncertain, statistical, or otherwise provisional information. A resolution mechanism turns selected uncertainty into concrete persistent facts when the simulation requires it.

Example:

    Before:
    village candidate
      location: probability distribution
      population: distribution
      founding date: distribution

    After resolution:
    village
      location: concrete coordinate
      population: concrete value
      founded: concrete simulated date

Once resolved, the result is part of the world's history. Later modules consume that fact rather than independently resampling it.

The unresolved-state representation, invalidation rules, and dependency tracking required to support this behaviour remain open architectural questions until experiments provide enough evidence to choose among alternatives.

## 6. Progressive generation and resolution

Worldloom SHALL support **progressive generation**: a world MAY be initially represented by broad, statistically plausible, or otherwise provisional information without requiring complete local resolution.

Worldloom SHALL permit selected parts of the world to be resolved or refined without requiring complete resolution of unrelated parts.

Resolution SHALL produce persistent canonical state rather than silently resampling an already-resolved fact.

Once a provisional result has been promoted to canonical state, subsequent modules SHALL treat the resolved value as authoritative unless an explicit state-changing process modifies it.

The system SHALL preserve enough provenance to relate a resolved fact to the provisional information, observations, rules, models, configuration, and/or events that produced it.

### 6.1 Projection

A **projection** is a useful broad representation of the world produced without requiring every local fact or historical detail to be resolved.

A projection MAY contain statistical, uncertain, candidate, or coarse-resolution information. The implementation and storage representation of a projection are intentionally unspecified.

A projection SHALL be usable as input to processes that request further resolution or refinement.

### 6.2 Resolution triggers

Resolution MAY be initiated by:

- explicit user inquiry or exploration;
- explicit editing;
- simulation requirements;
- dependency requirements from another module;
- other explicitly defined world-building processes.

The mechanism by which these triggers request resolution is not yet fixed.

### 6.3 Open representation question

The specification intentionally does not currently require one particular representation for provisional information.

Candidates include:

- a special class of observation;
- first-class provisional state;
- generator/prior information;
- a hybrid or another representation.

This is an experiment-driven architectural question. The prototype should establish which semantics and operations are actually required before the representation is fixed.

### 6.4 Open consistency questions

The following consequences are recognised but not yet specified:

- how provisional values and their dependencies are invalidated after an explicit world change;
- how already-resolved facts are reconciled when a later change makes them inconsistent;
- how much global coherence a broad projection must guarantee before local resolution;
- whether projections are stored, reproducible generators, cached results, or some combination.

These questions SHALL remain explicit until experiments provide evidence for a design.

## Progressive world generation

A central Worldloom idea is:

> Generate broadly; resolve deeply where needed.

A world may first have a useful broad statistical/coarse representation. Exploration, editing, simulation, or module dependencies can request local resolution. Once a result is explicitly resolved into canonical state, it becomes part of the world's history and should not be silently regenerated.

The exact representation of provisional information remains an experiment-driven open question.

### Uncertainty becomes history

Worldloom must distinguish an unresolved probability/distribution from a concrete fact established in simulated history.

Once an uncertainty is resolved into a persistent fact, later simulation should consume that fact rather than silently resampling it.
