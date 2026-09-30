# Worldloom — Copilot Instructions

## Read this first

Worldloom is a **modular framework for constructing, simulating, and exploring persistent computational worlds**.

Before making architectural changes, read these documents in order:

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/SPECIFICATION.md`
4. `docs/ROADMAP.md`
5. `docs/DEVELOPMENT.md`
6. `docs/INTERFACES.md`
7. `docs/COPILOT_CONTEXT.md`

`docs/ARCHITECTURE.md` and `docs/SPECIFICATION.md` describe current architectural decisions and normative requirements. `docs/ROADMAP.md`, `docs/INTERFACES.md`, and `docs/COPILOT_CONTEXT.md` preserve longer-term context so local implementation does not accidentally narrow the design.

## Testing is mandatory

**Every code change must be accompanied by appropriate automated tests.**

- Add or update unit tests for changed behaviour.
- Run the test suite before considering a change complete.
- Do not claim tests pass unless they were actually run.
- Preserve existing tests unless a change in behaviour deliberately requires updating them.
- Prefer small, deterministic, fast unit tests.
- Test architectural contracts and interfaces, not only implementation details.
- For integration/adaptor work, add focused tests for the adapter contract and use fixtures/mocks where practical rather than requiring external services in ordinary unit tests.
- Experimental code must not weaken the project's normal test suite.
- A failing test is a development problem to investigate, not something to hide or bypass.

The repository's CI workflow runs the test suite automatically for pushes and pull requests. A green local test run is useful, but CI is the authoritative check for commits entering shared repository history.

## Architectural principles

### The loom, not every thread

Worldloom should provide interoperability, orchestration, canonical state, provenance, scheduling, and stable interfaces. It should **not** attempt to reimplement every specialist domain model.

When an established system can provide a capability, prefer a thin adapter/interface layer over reproducing that capability inside Worldloom.

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

### Time and events

Do not assume one universal simulation timestep. Different domains naturally operate at different temporal resolutions, and the orchestrator should schedule work accordingly.

Events are first-class records and may change state, trigger dependent work, resolve uncertainty, or record external/endogenous occurrences.

### Uncertainty becomes history

Worldloom must distinguish an unresolved probability/distribution from a concrete fact established in simulated history.

Once an uncertainty is resolved into a persistent fact, later simulation should consume that fact rather than silently resampling it.

### Provenance matters

Derived state should be traceable to its producer, inputs, configuration, simulation time, and uncertainty/confidence where available.

The system should eventually make it possible to ask:

> Why does the world believe this?

### Interfaces are projections, not separate worlds

The long-term user experience includes a world-guide/wiki, GIS maps, natural-language queries and controlled edits, historical timelines, character/observer perspectives, GM tools, author research tools, consistency inspection, counterfactual scenarios, visual observation, and possibly a future 3D client.

These are future clients of the canonical world, not reasons to create parallel representations of the world.

Do not build current core architecture around a UI technology or prematurely implement these interfaces. Instead, preserve the ability to query state at a time/place/entity scope, trace provenance, distinguish observer knowledge from canonical reality, and perform explicit world mutations or branch simulations.

### Existing systems first

Before implementing a substantial capability, check whether a suitable established/open-source system already exists. If so, investigate an adapter before proposing a new implementation. See `docs/REFERENCE_BACKLOG.md`.

### Keep experiments separate

Experiments are evidence about models and architecture. They are not automatically normative architecture. Keep experimental code/configuration/results separate from the stable framework.

## Development discipline

- Make the smallest change that satisfies the requirement.
- Prefer explicit interfaces over implicit coupling.
- Update documentation when architecture or contracts change.
- Avoid premature generalisation.
- Do not silently change the project's long-term direction to make a local implementation easier.
- If a requirement conflicts with the architecture, surface the conflict rather than inventing a workaround.
- Work on feature branches. Do not merge a pull request unless explicitly asked to do so.
- Before modifying a general data contract, explain the architectural options and trade-offs first.
- Keep validation and identifier-scheme decisions explicitly separate unless the current task requires them.
