# Experiment Conventions

Experiments are evidence about the architecture or a model, not architecture by themselves.

Each substantial experiment should record:

- purpose and question
- model implementation/version
- configuration
- random seed(s)
- software/environment versions
- execution parameters
- measurements
- output locations
- interpretation, kept distinct from raw results

A suggested layout is:

    experiments/<id>/
      README.md
      config.yaml
      run.py
      results/

Experiments should be reproducible where practical and should not overwrite raw outputs without recording the change.

## Progressive-resolution provenance experiment

### Question

Can a coarse observation inform a persistent fact while retaining enough information to investigate later invalidation and deterministic re-resolution?

### Method and result

The prototype creates a coarse `settlement.candidates` observation, resolves one candidate into a persistent entity, then replaces the observation with changed data. The entity remains unchanged, its provenance retains the observation dependency, and both values receive deterministic payload fingerprints. Worldloom copies values at write time, so the recorded fingerprint describes the stored payload even if the caller later mutates its original object.

Fingerprints intentionally support a limited world-data domain: JSON-like scalars, lists/tuples, sets, and dictionaries containing those values. Unsupported Python objects raise `TypeError`; this experiment does not claim universal serialization stability.

### Interpretation

Write-in-place observations are sufficient for this first feasibility experiment. A fingerprint is a useful minimal foundation: later code can compare the current observation payload with the payload that informed a resolved fact. The experiment does not establish whether invalidation should be query-based, event-based, or explicit, nor whether stale facts should be marked, removed, or reconciled.

### Follow-up paths

- Decide how to retain provenance history when observation versioning is introduced.
- Investigate invalidation and reconciliation semantics after an explicit world change.
- Test whether fingerprints plus stored module configuration and per-module seeds are sufficient for deterministic regeneration.
- Compare storing derived outputs with recomputing them from snapshots and module inputs.


## Raster terrain adapter causal integration experiment

### Question

Can an established external terrain/GIS representation enter Worldloom through a thin adapter, become canonical Worldloom terrain state, and drive the existing hydrology → settlement suitability → settlement resolution pipeline without downstream modules knowing about the external system?

### Implementation

The existing Rasterio-backed terrain adapter is exercised with a small deterministic GeoTIFF fixture. Rasterio handles the external raster representation and its geospatial metadata; the adapter writes the first band to the existing `terrain.elevation` canonical field and records source identity, shape, CRS, transform, and simulation time in existing provenance.

The test wraps the adapter as the terrain provider for the existing `prototype.terrain` module contract. No changes are made to the hydrology, settlement-suitability, or settlement-resolution implementations.

Two otherwise identical 10×10 fixtures place the low-elevation/water cell at different locations. Each fixture is run through the real downstream modules and settlement resolution.

### Configuration

- External representation: single-band GeoTIFF.
- Raster dimensions: 10×10.
- CRS: EPSG:4326.
- Cell size: 0.5 degrees.
- Elevation: 9.0 everywhere except one 4.0 cell.
- Simulation time: 12 for causal and determinism tests.
- No external GUI GIS application is required.

### Measurements / results

The experiment verifies that:

- the adapter imports representative terrain values and spatial metadata;
- provenance identifies the adapter and external source;
- the existing hydrology module consumes the canonical terrain field;
- settlement suitability consumes Worldloom state rather than Rasterio objects;
- changing only the external terrain fixture changes hydrology;
- the hydrology change propagates to settlement suitability;
- the suitability change propagates to the resolved settlement location and founding event;
- repeating the same fixture and configuration produces the same canonical state, observations, entities, events, and provenance;
- the existing production vertical slice remains covered separately in `tests/test_prototype.py`.

### Interpretation

**Demonstrated**

An established raster representation can participate in the existing Worldloom module pipeline through a replaceable adapter boundary. The external representation does not need to become part of downstream module contracts, and the adapter is demonstrably in the causal path rather than merely loading unused data.

The experiment therefore strengthens the existing adapter-first architectural conclusion: specialist raster/GIS functionality can remain outside Worldloom while Worldloom owns the canonical state and orchestration boundary.

**Still open**

This experiment does not settle:

- the final spatial data model;
- whether spatial/grid metadata should remain provenance or become part of field semantics when spatial meaning is required downstream;
- final GIS interchange formats;
- coordinate reference system policy;
- spatial indexing;
- raster/vector interoperability;
- large-data handling or streaming/chunking;
- external-tool versioning and reproducible source identity;
- identifier semantics;
- validation semantics;
- whether adapted data should always become canonical state or sometimes remain derived/provisional.

### Limitations

The fixture is deliberately small and uses Rasterio directly rather than a full GIS application. The downstream prototype modules currently operate on simple nested Python values and do not themselves consume CRS or transform metadata. The experiment therefore proves the adapter boundary and causal exchange, not a complete geospatial interoperability model.



## Spatial field semantics experiment

### Question

When spatial metadata is part of the meaning of a Worldloom value, rather than merely provenance about where it came from, can a downstream Worldloom module use that meaning without knowing the specialist system that produced the value?

### Candidate representation

This experiment deliberately tests one small representation rather than selecting the final spatial model:

- ordinary non-spatial fields remain plain values;
- a spatial field may have an associated typed SpatialGrid semantic object;
- the grid records shape, CRS, and a six-coefficient affine transform;
- Worldloom exposes cell-centre coordinate lookup through its own state API;
- the specialist adapter remains responsible for translating native GIS metadata into this representation.

The spatial semantic object is stored with canonical world state and is included in snapshots. It is not stored only in provenance.

### Causal test

The Rasterio terrain adapter imports the existing 10×10 GeoTIFF fixture and attaches its grid semantics to terrain.elevation. A downstream test module asks Worldloom for the world coordinate of a selected terrain cell using only the Worldloom field API. The downstream module does not import Rasterio or inspect provenance.

The experiment also verifies that:

- the grid shape, CRS, and derived bounds are available from canonical state;
- cell-centre coordinates are deterministically derived from the grid transform;
- ordinary scalar fields do not acquire spatial wrappers;
- spatial semantics survive snapshot/restore;
- the existing raster → hydrology → suitability → settlement causal path remains intact.

### Interpretation

**Demonstrated**

A small, typed spatial-semantic sidecar can carry enough meaning for a downstream Worldloom module to interpret a grid-backed field without coupling that module to Rasterio or provenance structure.

This is evidence that spatial meaning need not be encoded solely as provenance. It also preserves a simple representation for ordinary scalar/entity values.

**Not decided**

This experiment does not establish the final Worldloom spatial model. In particular, it does not decide:

- whether all spatial data should use this representation;
- how vector geometries should be represented;
- whether fields should eventually be wrapped directly rather than associated with spatial semantics;
- CRS policy and transformation services;
- spatial indexing/query semantics;
- temporal/spatial reference systems beyond this minimal grid case;
- interoperability with external GIS data structures;
- identifier or validation semantics.

The result should therefore inform the eventual spatial-data contract without prematurely fixing it.


## End-to-end GIS export experiment

### Question

Can the existing small Worldloom simulation pipeline produce a tangible, georeferenced map artifact that can be opened directly by an established GIS application?

### Method

The existing deterministic prototype terrain → hydrology → settlement suitability → settlement resolution pipeline is run on a 10×10 grid. The terrain field is given a minimal EPSG:4326 spatial grid using the spatial semantics established by the preceding experiment.

A thin Rasterio-backed export adapter projects three Worldloom outputs into a single GeoTIFF:

- terrain elevation;
- hydrology water mask;
- settlement suitability observation.

The suitability observation is rasterised only at the export boundary. It remains an observation in canonical Worldloom state and is not promoted to canonical spatial state merely because it is visualised.

### Measurements / results

The export test verifies that the resulting file is a readable GeoTIFF with:

- 10×10 dimensions;
- EPSG:4326 CRS;
- the expected affine transform;
- three named bands;
- values matching the Worldloom terrain and water fields;
- suitability values mapped to their corresponding grid cells.

The exporter does not mutate the Worldloom state, and the example can generate the artifact from the command line.

### Interpretation

**Demonstrated**

Worldloom now has a small complete path from procedural world generation through causal simulation to a concrete GIS-ready file. GIS-specific encoding remains behind an adapter boundary, while the simulation modules continue to exchange ordinary Worldloom state.

This is deliberately an integration proof rather than a decision that GeoTIFF is Worldloom's universal interchange format.

**Still open**

This experiment does not settle:

- the final GIS exchange formats;
- vector export;
- packaging of entities and events alongside raster fields;
- whether derived raster observations should eventually carry their own spatial semantics;
- CRS transformation policy;
- large-data or streaming behaviour;
- round-trip editing from GIS back into Worldloom.


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


## Canonical-state data routing and propagation experiment

### Question

Can the current dependency-aware engine exchange data between modules through canonical Worldloom state across direct chains, fan-out, state → observation → resolution boundaries, and differing temporal cadences without introducing an explicit routing layer?

### Method

A small Python-only experiment harness defines deterministic toy modules with explicit semantic input/output contracts. The modules exchange values only through `WorldState`; no module calls another module directly and no general router is added.

The harness tests four shapes:

- A → B state propagation;
- A → B + C fan-out from one state output;
- A → B → C chained propagation;
- state → observation → resolution into a persistent entity and event.

A fifth test runs producer/consumer modules at different fixed temporal intervals to observe which previously-produced value a slower consumer receives.

### Measurements / results

The experiment records whether:

- dependency ordering is sufficient to make upstream outputs available to downstream modules;
- one canonical state value can be consumed by multiple downstream modules;
- state can cross multiple dependency edges without direct module-to-module calls;
- the state/observation boundary remains explicit before resolution creates persistent state;
- a slower module consumes the latest available canonical output rather than requiring a same-timestep message.

### Interpretation

**Demonstrated**

The current Worldloom execution model is sufficient for these small routing shapes without a general data-routing mechanism. Module dependencies determine execution order, while canonical field/observation names provide the data exchange surface.

Fan-out requires no special mechanism: multiple modules can independently consume the same canonical output. Chaining likewise requires no intermediate router.

The cadence test demonstrates a useful current semantic: with fixed intervals, a slower consumer reads the value currently present in canonical state. It therefore can consume an upstream result produced at an earlier simulation time.

**Still open**

This experiment does not settle:

- whether canonical field names are sufficient when multiple module instances provide competing values;
- how explicit routing should work when several producers or consumers share related semantic names;
- whether dependencies and data contracts should be validated against the actual world state;
- whether consumers should be allowed to read stale upstream values across temporal cadences;
- how event-triggered propagation should interact with fixed-interval scheduling;
- how invalidation and recomputation should operate when an upstream value changes;
- identifier semantics;
- a general validation architecture.

### Scope

This is deliberately an experiment, not a proposal for a general router or a final composition model. The harness and tests exist to expose current engine behaviour before those broader architectural decisions are made.


## Competing canonical-state producers experiment

### Question

What happens when multiple independent modules write the same canonical field, and does the current model provide an ownership or arbitration rule for that shared output?

### Method

Two deterministic toy producer modules both declare `field:shared.value` as an output, but write distinguishable values. A consumer declares the same field as its input. The experiment runs the same three modules twice, reversing the producer order between runs.

No routing, validation, ownership, or identifier mechanism is added.

### Measurements / results

The final canonical value is the value written by the producer that executes last. Reversing the producer order therefore reverses the final value seen by the consumer.

The experiment demonstrates that the earlier model permitted multiple writers to the same field without detecting the collision.

### Interpretation

**Demonstrated**

The pre-ownership model had no intrinsic single-producer rule for canonical field names. When competing producers wrote the same field, ordinary execution order determined which value remained in `WorldState`.

This result is superseded for the ownership experiment by the provisional EXCLUSIVE rule documented below: canonical outputs now default to EXCLUSIVE, so two producers declaring the same non-event output are rejected during declaration-time validation rather than arbitrated by execution order.

This supersession is intentionally limited. It does not establish a general validation framework, and it does not retroactively change the historical result recorded by this experiment.

**Still open**

This earlier experiment does not decide:

- whether a canonical output should have exactly one producer;
- whether multiple producers should coexist under distinct semantic identities;
- whether arbitration or composition belongs in module contracts, scheduling, or another layer;
- whether competing outputs should be represented as separate values and combined explicitly;
- what provenance should mean when several producers contribute to one resulting value.

The ownership experiment addresses only a provisional subset of these questions.

### Scope

This section records the historical last-writer-wins behaviour observed before ownership declarations were introduced. It is not a proposal that last-writer-wins should become Worldloom architecture.

## Invalidation and reconciliation experiment

### Question

When a resolved canonical fact depends on a derived observation, can Worldloom detect that the upstream observation has changed without automatically changing the resolved fact?

### Method

A deterministic toy resolution path creates a `settlement.candidates` observation, resolves the highest-scoring candidate into persistent `settlement:001` state, then replaces the observation with changed scores that would select a different candidate.

The experiment records the observation fingerprint before and after the change and inspects the resolved entity's provenance. A separate snapshot preserves the earlier observation provenance so the two versions can be compared explicitly.

No invalidation, stale-state marker, reconciliation mechanism, or production API is added.

### Measurements / results

The experiment verifies that:

- replacing an observation changes its stored provenance fingerprint;
- the resolved entity remains unchanged when its source observation changes;
- the entity provenance identifies the observation by semantic name;
- the entity provenance does not currently retain the fingerprint or version of the particular observation value that informed the resolution;
- a snapshot can preserve the earlier observation provenance, allowing an external process to compare the old and current fingerprints.

### Interpretation

**Demonstrated**

Worldloom can detect that an observation's current value differs from a previously captured version when the earlier provenance is retained. The existing provenance link also identifies that a resolved fact depends on the observation.

However, the live resolved fact does not itself contain enough information to determine, from current state alone, whether the observation version that informed it has changed. Its provenance records the observation name and the fact's own fingerprint, but not the source observation's historical fingerprint.

The current behaviour therefore preserves canonical stability but does not provide automatic invalidation or reconciliation semantics.

**Still open**

This experiment does not decide:

- whether provenance should retain source-version fingerprints;
- whether observations should have explicit versions or immutable history;
- whether invalidation should be explicit, provenance-driven, event-driven, or on-demand;
- whether a changed observation should mark a resolved fact stale;
- whether stale facts should be removed, replaced, retained with a status, or reconciled by a new resolution process;
- how changes should propagate through multiple layers of derived observations;
- whether snapshots, provenance history, or another mechanism should provide the comparison baseline.

### Scope

This is a feasibility and information-availability experiment. It deliberately does not introduce an invalidation mechanism or make a policy decision about what Worldloom should do when an upstream dependency changes.


## Canonical output ownership experiment

### Question

Can provisional producer-ownership declarations make competing canonical outputs explicit and deterministic without changing the scheduler contract, while permitting refinement and opt-in priority-based overlays?

### Pass/fail criteria

The original criteria were written before implementation. During review, four criteria were clarified or reworded to reflect the chosen experimental policy and implementation: compatibility is scoped to non-colliding existing outputs; the provenance criterion distinguishes required losing-layer metadata from additional losing-producer metadata; the runtime guard includes declared overlay-layer ownership; and entity matching is explicitly provisional. The experiment therefore tests that existing modules remain unchanged when they do not collide and that declared EXCLUSIVE collisions are rejected before execution.

The experiment passes if all of the following are demonstrated:

- existing modules with no ownership declarations retain their current behaviour when their outputs do not collide;
- two EXCLUSIVE producers of the same non-event output are rejected before execution;
- a single producer of an EXCLUSIVE output is accepted;
- a REFINES producer must name an output declared by another module in the same run;
- missing, self-referential, and cyclic REFINES declarations are rejected;
- a valid REFINES declaration is accepted without requiring a value-consistency check;
- two OVERLAY producers of one output may coexist when their layer names and integer priorities are distinct;
- mixed ownership policies for one output are rejected;
- equal overlay priorities and duplicate layer names for one output are rejected;
- reversing overlay producer execution order produces the same effective value;
- losing overlay values remain queryable;
- overlay provenance identifies the winning layer and the losing layers;
- overlay state survives snapshot/restore without sharing mutable state;
- event outputs remain append-only and permit multiple producers;
- with the runtime declaration guard enabled, undeclared writes from an active module are rejected while declared writes succeed, including enforcement of the module's declared overlay layer;
- entity declarations such as entity:settlement permit IDs such as settlement:001 under the experiment's provisional entity-name matching rule;
- writes made outside module execution, including adapter loading, remain unrestricted;
- with the guard disabled, existing write behaviour remains unchanged;
- the existing prototype, CLI, GeoTIFF export, unit suite, and experiment suite continue to pass.

### Falsification condition

The ownership design is considered falsified for this experiment if any required ownership distinction cannot be enforced without depending on execution order or modifying the scheduler contract, or if overlay effective values vary with producer execution order despite fixed layer priorities.

A guard-related falsification is also recorded if declared-name matching cannot distinguish the prototype's declared entity type from an individual entity ID without either exact-ID declarations or unrestricted writes.

### Results

The implementation differs from the original criteria in four documented ways:

- compatibility is narrowed from all existing undeclared outputs to **existing non-colliding outputs**, because the provisional default EXCLUSIVE policy intentionally rejects competing canonical producers;
- the provenance criterion is clarified to retain the **winning layer and losing layers**, with losing producers additionally recorded when provenance exists;
- the optional runtime guard is strengthened to enforce declared overlay-layer ownership, so an active module cannot write another module's declared layer;
- entity matching is explicitly treated as the experiment's **provisional entity-prefix rule**, rather than a final identifier semantics decision.

The implementation demonstrates the ownership-specific behaviours covered by the experiment tests. The full-suite status is deliberately **not** claimed here until the exact local unit and experiment commands and the GitHub Actions checks have been independently verified.

The ownership-specific results are:

- EXCLUSIVE collisions are rejected before module execution.
- A single EXCLUSIVE producer remains valid.
- REFINES requires a distinct same-run parent and rejects missing, self-referential, and cyclic declarations.
- Valid REFINES declarations are accepted without imposing value-consistency semantics.
- REFINES is purely declarative in this experiment: it does not impose execution ordering or a dependency edge. A refiner supplied before its parent remains before its parent, demonstrating that declaration alone does not schedule the parent first. The single-module parent+child case is rejected as a self-reference.
- OVERLAY accepts distinct layers with distinct integer priorities, rejects mixed policies, duplicate layers, and duplicate priorities, and selects the highest-priority available layer independently of producer execution order.
- The runtime guard enforces declared overlay layer ownership in addition to output-name ownership.
- Losing overlay values remain queryable. Provenance records the effective winning layer plus losing layers and, where available, losing producers; losing layers are ordered by priority. The original criterion specifically requires the winning layer and losing layers, while the implementation records losing producers as additional metadata. The two losing lists are not positional pairs: a losing layer without provenance is still present in `losing_layers` but contributes no entry to `losing_producers`.
- Overlay provenance removes stale metadata when the effective winner is later written without provenance and keeps overlay metadata namespaced separately from producer configuration.
- Overlay state is included in snapshot/restore with independent mutable copies.
- Event outputs remain append-only and may have multiple producers; the strengthened test has both producers actually record an event and asserts that both events are present.
- The optional runtime declaration guard rejects undeclared field, observation, event, and entity writes while permitting declared writes under the tested entity-type prefix rule. The guard state is reset after an exception, including its declared outputs, declared overlay layers, and active module name.
- Writes outside module execution, including adapter writes, remain unrestricted, and disabling the guard preserves existing behaviour.
- Reusing a WorldState with the same overlay registration is accepted when the layer declaration is identical and rejected when the same overlay name is registered with different layers.
- The provisional entity matching rule treats declarations such as entity:settlement as permitting individual IDs such as settlement:001 while rejecting unrelated entity prefixes. This is evidence for the experiment's guard target only; it is not a final identifier or entity-address rule.
- Overlay provenance currently uses `repr(address)` in its provenance namespace. This is a deliberately provisional choice on the experiment branch and should not be treated as the final address/identifier representation.
- Overlay storage is a sidecar to canonical state rather than materialising the effective value into `world.fields`. Consequently, downstream `InputSpec` consumption of overlay outputs remains an open interface question.

### Interpretation

**Demonstrated**

Provisional ownership declarations are sufficient to make competing canonical outputs explicit and reject ambiguous EXCLUSIVE ownership before execution without changing the scheduler contract.

The experiment also demonstrates that arbitration can be separated from scheduling for the OVERLAY case: fixed layer priorities determine the effective value, so producer execution order does not determine the result. Keeping all overlay layers queryable preserves information that would otherwise be lost under a single canonical storage slot.

The optional runtime guard provides a second, distinct enforcement boundary. Declaration validation establishes what a module says it may produce; the guard checks writes made while that module is executing. Keeping the guard opt-in preserves compatibility with existing code and allows direct adapter/state preparation outside module execution.

REFINES remains intentionally declarative. This experiment demonstrates declaration validation, not refinement computation, value merging, or scheduling semantics.

**Architectural implications**

This is evidence for a provisional ownership protocol around canonical outputs, not a final general validation or composition architecture. In particular, the experiment supports:

- explicit ownership metadata in module output declarations;
- declaration-time rejection of ambiguous EXCLUSIVE ownership;
- deterministic, sidecar overlay state rather than materialising an arbitrated value into ordinary canonical fields;
- provenance that can expose both the effective layer and losing contributions;
- a runtime write guard as an optional enforcement mechanism.

The implementation intentionally uses a generic hashable address key for overlay storage because this experiment branch is independent of the address-derived identity work in PR #19. It does not select the final identifier scheme.

When the winning overlay layer has no provenance, the current implementation removes the effective overlay provenance entry, even if losing layers retain layer-level provenance. This is an explicit experiment behaviour.

### Limitations and open questions

The experiment does not establish:

- semantics for actually combining or transforming REFINES values;
- any ordering or dependency semantics for REFINES;
- a general validation framework;
- a final identifier/address model;
- whether overlay effective values should ever be materialised into ordinary fields;
- whether overlay layer identity should eventually use stronger module/output identifiers;
- whether overlay values need deletion or masking operations;
- how a downstream InputSpec should declare and consume an overlay output stored in the sidecar;
- how ownership interacts with more complex module composition or dynamic module discovery;
- whether runtime enforcement should eventually become mandatory;
- whether WorldState reuse should be validated through full engine reruns rather than the current overlay-registration tests;
- how ownership and overlays should interact with invalidation, versioned state, or event-triggered scheduling;
- whether the provisional entity-prefix matching rule is sufficiently precise for a final identifier model;
- whether `repr(address)` is an adequate long-term provenance namespace.

### Scope

This is an architectural feasibility result, not a claim that the ownership protocol is the final Worldloom composition model.



## Address-derived identity and keyed-randomness integration experiment

### Question

When a resolution pipeline uses address-derived entity identity and keyed randomness, are its resolved values independent of module execution order and candidate traversal order, while preserving deterministic state and provenance?

### Pass/fail criteria

The experiment passes only if all of the following hold:

- keyed draws made inside the resolver's traversal loop are identical under reversed traversal;
- a shared sequential stream used in the same loop is different under reversed traversal (the negative control);
- producer modules drawing from a shared stream produce different observations when producer order is reversed, while keyed producers do not (the engine-level control);
- the fields comparison asserts against at least one real field;
- the real `SimulationEngine` and `WorldState` are used for the engine-level tests.

**Falsification:** if either negative control fails to show order dependence, the experiment cannot distinguish keyed from unkeyed randomness and must be redesigned, not reported as a pass.

### Method

A small experiment harness uses the real `SimulationEngine` and `WorldState` contracts with two independent candidate-producing modules and one resolution module.

Each candidate value is generated with `rng_for`, keyed by:

- the fixed experiment seed;
- generator identity and version;
- an `Address`;
- a candidate-specific purpose.

The experiment varies two ordering dimensions:

- the order in which the two independent producer modules are supplied to the engine;
- the order in which the resolver traverses candidate addresses.

The resolver derives the settlement entity ID from the resolution question and slot. The selected address is stored as entity data rather than contributing to identity.

The experiment also runs the same configuration twice with the same seed and runs the resolution with a changed upstream seed to verify that a changed resolved value retains the same entity identity rather than creating a second entity.

### Configuration

- Python: 3.12 in CI.
- Simulation seed: 314159 for the reproducibility/order tests.
- Generator ID: `experiment.address_rng.integration`.
- Generator version: `1`.
- Candidate addresses: `/region/a`, `/region/b`, `/region/c`.
- Two independent candidate purposes.
- One persistent settlement resolution with slot `001`.

### Measurements / results

The experiment verifies that:

- reversing the independent producer order does not change canonical fields or observations;
- reversing candidate traversal does not change the selected settlement;
- the resolved entity ID is unchanged by the selected address;
- entity, event, and provenance values are identical between the ordering variants;
- canonical data fingerprints for fields, observations, and entities are identical between the ordering variants;
- repeating the same seed reproduces canonical data and provenance;
- changing the upstream random values changes the resolved entity's contents without creating a second entity.

All tests pass in CI.

### Interpretation

**Demonstrated**

For this controlled pipeline, address-keyed randomness and identity derived from the resolution question remove two sources of incidental ordering dependence:

1. random values do not depend on the order in which other addresses are processed;
2. persistent entity identity does not depend on which candidate is selected.

This is stronger evidence than the earlier API-only keyed-randomness experiment because the values cross actual `SimulationEngine` and `WorldState` boundaries and are recorded in entity and provenance state.

The result supports keeping address-derived identity and keyed randomness as viable provisional mechanisms for further experiments.

**Not decided**

This experiment does not establish that these mechanisms should become normative Worldloom architecture. In particular, it does not decide:

- the final address hierarchy or identifier representation;
- the final entity-ID derivation scheme;
- how seeds should be assigned, versioned, and recorded for real modules;
- whether all stochastic module behaviour must be keyed;
- how random streams should interact with temporal scheduling, retries, branching, or parallel execution;
- whether provenance must record the complete random-generation context;
- how changed upstream world state should trigger re-resolution of existing facts;
- final validation semantics.

### Limitations

The experiment uses deterministic toy producers and a single persistent resolution. It does not exercise parallel execution, event-triggered scheduling, retries, distributed execution, or a real specialist simulation engine. It therefore establishes feasibility and order-independence under the tested contracts rather than proving general determinism for all future Worldloom modules.
