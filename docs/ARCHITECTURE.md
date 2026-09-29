# Worldloom Architecture

## 1. Purpose

Worldloom provides the **loom**, not every thread. It is an orchestration and interoperability layer for constructing persistent computational worlds from specialised systems.

The architecture should make it possible to combine existing geospatial, environmental, demographic, economic, linguistic, social, historical, numerical, and visualisation systems without requiring those systems to become one monolithic simulator.

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

## 3. Modules

A module declares at least:

- inputs
- outputs, with each output identified as canonical state, derived observation, or event
- spatial resolution
- temporal resolution
- uncertainty characteristics
- dependencies
- lifecycle/step behaviour

A module may be an in-process Python component, an external executable, a GIS workflow, a numerical model, or an adapter around an existing application.

## 4. State and observation boundary

The canonical state is authoritative simulated reality. A derived observation is a calculation made from canonical state or other declared inputs. Storing an observation does not promote it to world state.

Promotion is explicit: an observation may inform a resolution or simulation process that creates a persistent fact, with provenance linking the new fact to the observation and its underlying inputs.

The prototype represents this distinction directly: WorldState.fields and WorldState.entities hold canonical state, while WorldState.observations holds derived observations. ModuleSpec uses OutputSpec and DataKind to declare output semantics.

## 5. Adapters

Worldloom should preferentially reuse established systems rather than reproduce them.

An adapter translates between a specialist system's native representation and the canonical Worldloom representation. For example, GIS data may be exchanged with QGIS or other established GIS tooling rather than having a new GIS engine built inside Worldloom.

Adapters should be thin where possible and should preserve provenance about external calculations and source data.

The first concrete adapter uses Rasterio for single-band raster input. It loads the first raster band into the canonical `field:terrain.elevation` representation and records the source identifier and relevant raster metadata in provenance. Rasterio remains responsible for raster decoding and geospatial metadata; Worldloom does not introduce a GIS-specific canonical object model. The adapter is an optional GIS integration rather than a core runtime dependency.

## 6. Time and orchestration

Modules operate at different natural temporal resolutions. For example:

- weather: minutes
- rivers and hydrology: hours/days
- economy: days/months
- population: months/years
- politics: days/years
- culture: decades
- geography: centuries/millennia

Simulation time is a numeric coordinate whose unit is supplied by simulation configuration. A module may declare a positive numeric temporal interval in those simulation-time units. The scheduler invokes each module when its interval is due rather than forcing every module through one universal timestep.

The scheduler is deterministic: when multiple modules are due at the same simulation time, declared dependency order is respected and the original module input order remains the tie-breaker for otherwise independent modules.

Each invocation receives the current simulation time and the elapsed time since that module's previous invocation. A module without a temporal interval is treated as a one-time/static module during a scheduled run.

Event-triggered scheduling is intentionally outside the current scheduler contract and remains future work.

## 7. Statistical states and resolution

A world may begin with uncertain or statistical states. A resolution mechanism turns an uncertainty into a concrete persistent fact when the simulation requires it.

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

## 8. Events

Events are first-class records. An event may:

- change canonical state
- trigger dependent modules
- resolve an uncertainty
- record an external or endogenous occurrence
- carry provenance and uncertainty

This allows long-running simulations to explain how present state emerged from earlier state transitions.

## 9. Provenance

Worldloom should retain enough provenance to answer questions such as "Why does the world believe this?"

A derived value should be traceable to its producing module/version, inputs, event history, simulation time, configuration, and confidence/uncertainty where applicable.

## 10. Prototype path

The first end-to-end prototype should be deliberately small:

    module A
        ↓
    canonical state
        ↓
    module B
        ↓
    canonical state
        ↓
    module C
        ↓
    persistent fact
        ↓
    event
        ↓
    new state

A useful early domain example is terrain → water → settlement suitability → persistent settlement, with GIS interoperability tested as an adapter rather than recreated internally. The current raster adapter can provide the terrain field directly to the existing hydrology and settlement prototype modules.

## 11. Architectural boundary

Worldloom defines interoperability and orchestration contracts. Specialist domain models remain independently replaceable.

The principal architectural asset is therefore the interface between systems, not any one particular domain model.

## 12. Snapshot semantics

Snapshots are point-in-time captures of the world state intended to support reproducibility, restoration, and eventually branching.

The current snapshot contract is deliberately narrow:

- fields, entities, events, observations, and provenance are captured;
- captured state is deep-copied so later mutation cannot alter the snapshot;
- the snapshot container is immutable at the container level;
- optional metadata may record execution context;
- restoring a snapshot deep-copies its contents back into the world, so the restored world does not share mutable nested state with the snapshot.

Snapshot metadata is contextual rather than canonical world state. More advanced checkpointing and branching semantics remain future work until they are required by the simulation engine.
