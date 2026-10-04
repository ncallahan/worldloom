---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Canonical State Vs Observation

## 2. Canonical world state

The simulated world has an authoritative canonical state. Conceptually it contains:

- entities
- fields
- events
- relationships
- constraints
- distributions and other uncertain states
- provenance

Modules read and write canonical state through explicit contracts. Derived observations are kept semantically separate from authoritative state and may be recomputed or cached without becoming world history. A module should not need to know the implementation details of another module.

The canonical state is the persistent part of the world: once a provisional result has been explicitly resolved into canonical state, subsequent modules should consume that established fact rather than independently regenerating it.

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

## 1. World state

The canonical world state SHALL support, directly or through extensible representations:

1. entities
2. fields
3. events
4. relationships
5. constraints
6. uncertain/statistical states
7. provenance

State must have stable identity so that facts can persist across simulation steps.

Worldloom SHALL be capable of providing a useful broad representation of a world before all local history and fine-grained state has been resolved.

## 12. Canonical state versus derived observations

Worldloom SHALL distinguish **authoritative canonical state** from **derived observations**.

### 12.1 Canonical state

Canonical state is the simulation's authoritative representation of what is true in the world at a given simulation time.

Canonical state:

- MAY be created or changed by simulation processes, events, or explicit resolution of uncertainty.
- SHALL have persistent identity where the represented fact is an entity or other persistent fact.
- SHALL be available as input to other modules through the canonical world-state interface.
- SHALL be reproducible from the simulation history, configuration, and relevant inputs to the extent required by the project's reproducibility guarantees.
- SHALL NOT be silently regenerated from a derived observation merely because a module needs it.

Examples include:

- a settlement's established location;
- a settlement's established population;
- a river or other persistent entity once established by the simulation;
- a historical event that has occurred;
- a persistent world field whose values are themselves part of the simulated state.

### 12.2 Derived observations

A derived observation is a value calculated from canonical state, external data, or other explicitly declared inputs for measurement, analysis, decision support, or module operation.

Derived observations:

- SHALL NOT become canonical state merely because they are stored or passed through an interface.
- SHOULD identify their inputs and producer through provenance where practical.
- MAY be recomputed when their inputs or computation change.
- MAY be cached for performance, but a cache SHALL NOT be treated as authoritative world history unless explicitly promoted to canonical state.
- SHOULD be distinguishable from canonical state in module contracts and APIs.

Examples include:

- settlement suitability calculated from terrain and water;
- a map projection or visualisation;
- a statistic such as population density;
- an analytical risk score;
- a model's prediction about a possible future state.

### 12.3 Promotion from observation to state

A derived observation MAY be used to create or modify canonical state, but this transition SHALL be explicit.

For example:

    canonical terrain + canonical water
                |
                v
       derived suitability
                |
                v
       explicit resolution rule
                |
                v
       canonical settlement

The promotion step SHOULD record:

- the observation or observations used;
- the rule, model, or decision process that performed the promotion;
- the simulation time;
- relevant configuration and random seed;
- provenance linking the resulting state back to its inputs.

This distinction is particularly important for uncertainty resolution: a probability distribution or suitability calculation describes possibilities or evaluations, while the resolved result becomes a persistent fact.

### 12.5 Prototype interpretation

In the current prototype:

- terrain.elevation is treated as canonical state.
- hydrology.water is treated as canonical state for the purposes of the prototype.
- settlement.suitability is a derived observation.
- settlement:001 is canonical persistent state.
- settlement.founded is a canonical historical event.

The prototype stores these through the same WorldState object, but in semantically distinct collections; the module contract also declares the distinction explicitly.

## Architectural consequence

Do not build the core around any one interface.

Prefer a canonical world representation with:

- persistent entities and identity;
- fields;
- events/history;
- relationships and constraints;
- uncertainty/statistical/provisional information;
- provenance;
- spatial and temporal semantics;
- reproducible snapshots/checkpoints.

Derived observations, projections, visualisations, and observer knowledge must remain distinguishable from canonical world state.

A future wiki, GIS, chatbot, GM interface, or 3D client should be able to query the same world rather than maintaining a second competing representation.

### Canonical world state

The simulated world has an authoritative canonical state containing, conceptually:

- entities
- fields
- events
- relationships
- constraints
- uncertain/statistical states
- provenance

Specialist modules should exchange information through canonical state or explicit adapter contracts rather than hidden direct dependencies.
