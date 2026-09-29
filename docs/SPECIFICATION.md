# Worldloom Specification

## Status

This is the initial normative outline. Details remain provisional until exercised by the prototype.

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

## 2. Module contract

A module SHALL expose enough metadata to identify:

- module name and version
- inputs
- outputs
- spatial resolution
- temporal resolution
- dependencies
- uncertainty behaviour

A module SHOULD expose lifecycle operations equivalent to initialise, advance/step, and validate.

## 3. State exchange

Modules SHALL exchange information through canonical world state or explicitly defined adapter contracts rather than hidden direct dependencies.

## 4. Time

The simulation engine SHALL permit modules with different temporal resolutions. It SHALL NOT require every module to execute at every smallest timestep.

### 4.1 Simulation time

Simulation time SHALL be represented as a numeric coordinate. The simulation configuration SHALL identify the unit associated with that coordinate; the unit is configuration rather than encoded into the numeric value.

A module MAY declare a positive numeric temporal interval in the configured simulation-time unit. A module with no temporal interval SHALL be treated as static/one-time for a scheduled run.

### 4.2 Scheduling

When running a bounded scheduled period, the engine SHALL invoke each module when its declared interval is due.

The scheduler SHALL:

- be deterministic;
- preserve declared dependency ordering when multiple modules are due at the same simulation time;
- use the modules' input order as the tie-breaker for otherwise independent modules;
- invoke a module without a temporal interval once at the start of the scheduled period;
- reject non-positive temporal intervals;
- NOT require event-triggered scheduling.

### 4.3 Execution context

Each module invocation SHALL receive:

- the current simulation time;
- the elapsed simulation time since that module's previous invocation;
- the simulation step associated with the scheduler;
- the configured random seed and execution metadata where supplied.

The first invocation of a module in a scheduled run SHALL receive zero elapsed time.

The existing single-cycle execution form remains available: when no scheduling end time is supplied, the engine invokes the modules once in dependency order at the supplied context time.

## 5. Events

Events SHALL be representable as persistent records with enough information to identify their time, effects, and provenance.

## 6. Resolution

The system SHALL distinguish:

- uncertainty about a possible future or unresolved world state
- concrete facts already established in simulated history

Resolution SHALL produce persistent state rather than silently resampling an already-resolved fact.

## 7. Provenance

Derived state SHOULD retain provenance sufficient to identify its producer, inputs, configuration, simulation time, and uncertainty/confidence where available.

## 8. Reproducibility

Experiments SHOULD record configuration, software versions, random seeds, execution parameters, measurements, and outputs.

## 9. External systems

The architecture SHOULD favour adapters to established specialist software over reimplementation when an appropriate system already exists.

The initial GIS adapter SHALL use Rasterio as an optional integration dependency. It SHALL read the first band of a raster source into a canonical Worldloom field and SHALL retain the source identifier and relevant raster metadata in field provenance. Raster decoding and GIS metadata interpretation remain the responsibility of Rasterio; Worldloom SHALL NOT require a general GIS object model for this integration.

## 10. Validation

Architectural changes SHALL be accompanied by tests where behaviour is testable and by corresponding documentation updates.

## 11. Dependency-aware execution

The simulation engine SHALL execute modules according to their declared dependencies rather than relying on caller-provided ordering.

- Module names SHALL be unique within an engine.
- Every declared dependency SHALL refer to a module present in the engine.
- Dependency cycles SHALL be rejected before module execution.
- When multiple modules are ready, execution SHALL be deterministic and preserve the modules' declared input order as the tie-breaker.

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

### 12.4 Module contracts

Module contracts SHOULD make the state/observation boundary explicit.

At minimum, an output declaration should be capable of distinguishing:

- canonical state output;
- derived observation output;
- event output.

The current interface represents this distinction with OutputSpec and DataKind. Further API refinements remain provisional until exercised by additional modules.

### 12.5 Prototype interpretation

In the current prototype:

- terrain.elevation is treated as canonical state.
- hydrology.water is treated as canonical state for the purposes of the prototype.
- settlement.suitability is a derived observation.
- settlement:001 is canonical persistent state.
- settlement.founded is a canonical historical event.

The prototype stores these through the same WorldState object, but in semantically distinct collections; the module contract also declares the distinction explicitly.

## 13. Snapshot semantics

Worldloom SHALL provide snapshots with independent mutable state.

A snapshot:

- SHALL capture fields, entities, events, observations, and provenance;
- SHALL deep-copy captured state so later mutation of the world does not alter the snapshot;
- SHALL be represented by an immutable snapshot container;
- MAY carry optional metadata describing execution context;
- SHALL NOT require metadata to restore world state.

Restoring a snapshot SHALL:

- replace the world's captured state with independent copies of the snapshot contents;
- avoid sharing mutable nested structures between the restored world and the snapshot;
- preserve the semantic distinction between canonical state and derived observations.

Snapshot metadata is contextual rather than canonical world state. The current WorldState.restore() operation intentionally restores world data only; callers may separately retain or interpret snapshot metadata as required.
