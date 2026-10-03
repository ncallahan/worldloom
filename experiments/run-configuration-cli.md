---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## Declarative run configuration and CLI experiment

### Question

Can the existing end-to-end terrain → hydrology → settlement suitability → settlement resolution → GeoTIFF pipeline be completely described and reproduced by a human-editable JSON run configuration and executed from the command line, without putting inter-module wiring into that configuration?

### Method

The run configuration declares:

- simulation time unit and start/end time;
- the participating modules;
- configuration for each module instance;
- requested output adapters and their configuration;
- an optional execution seed.

The module names correspond to Worldloom module contracts. The scheduler continues to use module dependencies and semantic contracts to determine execution order and data exchange.

The prototype terrain module demonstrates module-owned configuration decoding by translating its JSON spatial-grid configuration into Worldloom's SpatialGrid object.

The command-line entry point is:

    worldloom run examples/prototype_run.json

### Measurements / results

Automated tests verify that the JSON configuration:

- instantiates the same prototype module set;
- reproduces the resolved settlement and its deterministic output;
- generates the requested GeoTIFF relative to the configuration file;
- preserves the existing module-contract-based exchange between terrain and hydrology;
- does not require explicit input/output wiring in the configuration.

### Interpretation

**Demonstrated**

A small declarative run configuration is sufficient to turn the existing prototype into a runnable experiment that does not require writing Python. The configuration can select modules and their parameters while leaving module interoperability to the existing contracts and scheduler.

This creates a useful user-facing execution boundary without requiring a general composition language.

**Still open**

This experiment does not settle:

- a final configuration schema or validation system;
- plugin/discovery mechanisms for external modules;
- reusable multi-module compositions;
- explicit wiring for multiple instances or competing providers;
- configuration inheritance or composition;
- provenance requirements for complete run configurations;
- packaging and versioning of configurations independently of Worldloom releases.
