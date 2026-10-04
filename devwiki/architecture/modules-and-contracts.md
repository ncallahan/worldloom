---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Modules And Contracts

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

Modules may consume outputs from other modules and may cause further parts of the world to be resolved. The dependency mechanism therefore represents more than execution order: it is one of the ways in which local world knowledge can become available to later processes.

## 12. Architectural boundary

Worldloom defines interoperability and orchestration contracts. Specialist domain models remain independently replaceable.

The principal architectural asset is therefore the interface between systems, not any one particular domain model.

This also means that broad projection and later local resolution should not force every specialist system into one common internal simulation model. Specialist systems may remain coarse, deterministic, statistical, static, dynamic, or external as appropriate, provided their Worldloom contract is explicit.

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

Modules SHALL be able to consume declared outputs from other modules through Worldloom contracts rather than hidden direct dependencies.

## 3. State exchange

Modules SHALL exchange information through canonical world state or explicitly defined adapter contracts rather than hidden direct dependencies.

A module MAY cause further state to be resolved as a consequence of consuming another module's output.

## 11. Dependency-aware execution

The simulation engine SHALL execute modules according to their declared dependencies rather than relying on caller-provided ordering.

- Module names SHALL be unique within an engine.
- Every declared dependency SHALL refer to a module present in the engine.
- Dependency cycles SHALL be rejected before module execution.
- When multiple modules are ready, execution SHALL be deterministic and preserve the modules' declared input order as the tie-breaker.

### 12.4 Module contracts

Module contracts SHOULD make the state/observation boundary explicit.

At minimum, an output declaration should be capable of distinguishing:

- canonical state output;
- derived observation output;
- event output.

The current interface represents this distinction with OutputSpec and DataKind. Further API refinements remain provisional until exercised by additional modules.

## Adding a module

A new module should document:

- purpose
- inputs
- outputs
- spatial and temporal resolution
- dependencies
- uncertainty
- lifecycle
- provenance
- validation strategy

Keep the implementation replaceable behind its contract.

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

### Replaceable modules

Modules may be:

- Python components
- external executables
- GIS workflows
- numerical models
- agent-based models
- field/graph models
- hybrid systems
- adapters around existing applications

Keep module interfaces smaller and more stable than their implementations.
