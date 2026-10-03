---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Run Configuration And Cli

## 16. Declarative run configuration and CLI

Worldloom should be usable for basic simulation experiments without requiring a user to write Python. The first implementation therefore provides a small JSON run configuration and a command-line entry point:

    worldloom run <configuration.json>

A run configuration describes:

- simulation time settings;
- the modules participating in the run;
- configuration for each module instance;
- requested output projections;
- execution options such as a run seed.

It deliberately does **not** describe inter-module wiring. Module contracts, semantic input/output names, and declared dependencies remain responsible for determining how participating modules interact.

This establishes three distinct configuration concerns:

    module contract
        how a module communicates

    run configuration
        which modules participate and how each instance is configured

    future composition/integration configuration
        explicit wiring or reusable multi-module compositions when the
        simpler run configuration is no longer sufficient

The third category is intentionally deferred. The current run configuration should remain a thin orchestration layer rather than becoming a second simulation architecture.

Module-specific configuration is allowed to have module-specific structure. A module may provide its own configuration decoding rather than requiring Worldloom to define a universal parameter schema.

Output adapters are similarly selected by a small adapter name and supplied with adapter-specific configuration. This is an initial mechanism for experimentation, not a commitment to a final plugin/discovery architecture.

The run configuration is execution metadata, not canonical world state. The resulting WorldState remains the authoritative simulation state, while requested outputs are projections of that state.

This separation should make it possible to save and reproduce an experiment as a small human-editable file while preserving the architectural boundary between orchestration, module semantics, canonical state, and external representations.
