---
type: experiment
status: experiment
summary: Migrated documentation page; source material retained verbatim for Phase 3 traceability.
related: ["[[index]]"]
---

# Question Derived Identity Address Randomness

## Question-derived identity and address-keyed randomness integration experiment

### Question

Can a coarse observation inform a persistent fact while retaining enough information to investigate later invalidation and deterministic re-resolution?

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

### Method

The existing deterministic prototype terrain → hydrology → settlement suitability → settlement resolution pipeline is run on a 10×10 grid. The terrain field is given a minimal EPSG:4326 spatial grid using the spatial semantics established by the preceding experiment.

A thin Rasterio-backed export adapter projects three Worldloom outputs into a single GeoTIFF:

- terrain elevation;
- hydrology water mask;
- settlement suitability observation.

The suitability observation is rasterised only at the export boundary. It remains an observation in canonical Worldloom state and is not promoted to canonical spatial state merely because it is visualised.

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

Write-in-place observations are sufficient for this first feasibility experiment. A fingerprint is a useful minimal foundation: later code can compare the current observation payload with the payload that informed a resolved fact. The experiment does not establish whether invalidation should be query-based, event-based, or explicit, nor whether stale facts should be marked, removed, or reconciled.

### Retained as provisional for this experiment, with rationale

The following choices are retained only to keep this experiment concrete and reproducible; they are not settled architecture:

- **Address-keyed randomness and question-derived identity:** retained because the experiment needs a concrete mechanism to test order independence without making either mechanism normative.
- **12-hex-character (48-bit) entity-ID digest:** retained because changing it would confound this experiment with a separate collision-policy decision; identity parts are recorded in provenance so collisions can be diagnosed.
- **Address canonicalisation without Unicode NFC/NFD normalisation:** retained because the experiment tests canonical path encoding, while Unicode normalisation policy is a separate decision.
- **Lookup-time alias uniqueness rather than insertion-time enforcement:** retained because changing `WorldState.add_entity` is outside this experiment's scope.
- **No world/seed component in entity identity:** retained because the experiment isolates the semantic resolution question; world/seed identity scope remains a separate decision.
- **CPython 3.12 RNG golden compatibility:** retained because the golden values intentionally pin the tested PRNG behaviour for this experiment.

### Not decided

- whether address-keyed randomness and question-derived identity should be required mechanisms for modules that need order-independent reproducibility, or remain optional tools;
- the final address hierarchy or identifier representation;
- the final entity-ID derivation scheme;
- whether the 48-bit entity-ID digest should be lengthened; the current 12-hex-character digest remains unchanged in this PR;
- whether world/seed scope should contribute to entity identity;
- how seeds should be assigned, versioned, and recorded for real modules;
- whether all stochastic module behaviour must be keyed;
- how random streams should interact with temporal scheduling, retries, branching, or parallel execution;
- whether provenance must record the complete random-generation context;
- whether address segments should be NFC-normalised, or whether NFC and NFD should remain distinct canonical addresses;
- how changed upstream world state should trigger re-resolution of existing facts;
- final validation semantics.

### Limitations

The fixture is deliberately small and uses Rasterio directly rather than a full GIS application. The downstream prototype modules currently operate on simple nested Python values and do not themselves consume CRS or transform metadata. The experiment therefore proves the adapter boundary and causal exchange, not a complete geospatial interoperability model.

### Scope

This is deliberately an experiment, not a proposal for a general router or a final composition model. The harness and tests exist to expose current engine behaviour before those broader architectural decisions are made.
