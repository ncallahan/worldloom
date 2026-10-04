---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

## Question-derived identity and address-keyed randomness integration experiment

### Question

When a resolution pipeline uses identity derived from its semantic resolution question and address-keyed randomness, are its resolved values independent of module execution order and candidate traversal order, while preserving deterministic state and provenance?

### Pass/fail criteria

The experiment passes only if all of the following hold:

- keyed draws made inside the resolver's traversal loop are identical under reversed traversal;
- a shared sequential stream used in the same loop is different under reversed traversal (the negative control);
- producer modules drawing from a shared stream produce different observations when producer order is reversed, while keyed producers do not (the engine-level control);
- the fields comparison asserts against at least one real field;
- the real SimulationEngine and WorldState are used for the engine-level tests.

**Falsification:** if either negative control fails to show order dependence, the experiment cannot distinguish keyed from unkeyed randomness and must be redesigned, not reported as a pass.

### Method

A small experiment harness uses the real SimulationEngine and WorldState contracts with two independent candidate-producing modules and one resolution module.

Each candidate value is generated with rng_for, keyed by the fixed experiment seed, generator identity and version, an Address, and a candidate-specific purpose.

The resolver draws a per-address resolution jitter inside its candidate traversal loop, keyed by the same experiment seed, generator identity/version, address, and purpose resolution.jitter. The jitter is added to each candidate score before selection, and the complete jitter mapping is written to the canonical resolution.jitter field.

The experiment varies two ordering dimensions:

- the order in which the two independent producer modules are supplied to the engine;
- the order in which the resolver traverses candidate addresses.

A permanent resolver control can replace the keyed draws with one random.Random(context.seed) stream created once per run. This is the reproducible order-dependent control that previously existed only as a temporary manual mutation.

The resolver derives the settlement entity ID from its semantic resolution question and slot. The selected address is stored as entity data rather than contributing to identity. Entity provenance records the identity kind and parts so that a future collision can be diagnosed rather than silently attributed to a matching digest.

The experiment also includes a producer-level shared-stream control. Two producer modules share one sequential stream; reversing producer order swaps their stream positions and therefore swaps the resulting candidate observations.

### Configuration

- Python: 3.12 in CI.
- Simulation seed: 314159 for the reproducibility/order tests.
- Generator ID: experiment.address_rng.integration.
- Generator version: 1.
- Candidate addresses: /region/a, /region/b, /region/c.
- Two independent candidate purposes.
- One persistent settlement resolution with slot 001.

### Measurements / results

The experiment verifies that:

- keyed jitter draws made inside the real resolver traversal loop are identical under forward and reverse traversal;
- the shared-stream traversal control produces different address-to-value mappings under reversal;
- keyed candidate producers remain identical when producer order is reversed;
- shared-stream candidate producers produce different observations when producer order is reversed, with the reversed candidate.a values exactly matching forward candidate.b values and vice versa;
- the resolver writes a real resolution.jitter field, so the engine-level fields comparison is non-vacuous;
- the engine-level keyed result is independent of producer and candidate traversal order;
- the permanent shared-stream resolver control produces different resolution.jitter fields under reversed traversal.

For seed 314159, the shared-stream resolver control does not change the selected location: both traversal orders select /region/b. It does change the jitter mapping, which is the decisive observable for this control.

The exact verification commands were:

    python -m pytest -q tests/experiments

    python -m pytest -q tests/unit

For implementation commit cba977e100cfc6bc6fd3a37170773c0540d46aef, GitHub Actions run 37061803055 completed successfully for both commands: the experiment suite reported 33 passed in 0.15s and the unit suite reported 100 passed, 2 warnings in 0.39s. This evidence applies to that commit; later documentation-only changes require their own verification.

The earlier deliberate mutation replaced the resolver's keyed rng_for(...).random() calls with the same shared-stream mechanism now represented permanently by ResolutionModule(shared_stream=True). That mutation failed at test_engine_result_is_independent_of_producer_and_candidate_order, establishing that the engine-level experiment detects the intended order dependence. The temporary mutation branch and draft PR were subsequently closed without merging.

The controls demonstrate detectability of order dependence, not general determinism. Passing them shows that this experiment can distinguish the keyed mechanism from the deliberately order-dependent shared-stream mechanisms under the tested traversal and producer-order perturbations.

The hashing golden values were independently reproduced from the pre-extraction WorldState.fingerprint implementation at commit a51d582b2c6a5746cdaa0942a2ea9f133c06d0a6; all three expected values matched. The requested git worktree add /tmp/main origin/main procedure could not be executed because no local repository was available and this environment cannot resolve github.com. The pre-extraction source was therefore fetched from that exact commit and the original hashing algorithm was executed independently.

### Interpretation

**Demonstrated**

For this controlled pipeline, semantic question-derived identity and address-keyed randomness remove two sources of incidental ordering dependence:

1. random values do not depend on the order in which other addresses are processed;
2. persistent entity identity does not depend on which candidate is selected.

The negative controls demonstrate that the experiment is capable of detecting the corresponding order dependence when a shared sequential stream is used instead.

This is stronger evidence than the earlier API-only keyed-randomness experiment because the values cross actual SimulationEngine and WorldState boundaries, a real canonical field is written, and the results are recorded in entity and provenance state.

The result supports keeping these mechanisms as viable provisional mechanisms for further experiments. It does not make them normative architecture.

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

The experiment uses deterministic toy producers and a single persistent resolution. It does not exercise parallel execution, event-triggered scheduling, retries, distributed execution, or a real specialist simulation engine. It therefore establishes feasibility and order-independence under the tested contracts rather than proving general determinism for all future Worldloom modules.

Only random() draw ordering was exercised. The experiment does not test other PRNG methods, distributions, stateful random objects beyond the deliberate shared-stream control, or stochastic algorithms that consume a variable number of draws.

Entity IDs currently use a 12-hex-character (48-bit) digest. Recording identity parts in provenance is the recommended collision-detection measure implemented here; lengthening the digest remains an open alternative.

WorldState.add_entity does not enforce alias uniqueness. Duplicate aliases are detected by find_entity_by_alias when looked up, not at insertion time; changing that enforcement is outside this PR.

Address canonicalisation currently preserves Unicode code-point sequences rather than normalising them. NFC versus NFD semantics remain undecided. A lone-surrogate segment currently raises UnicodeEncodeError during canonicalisation rather than ValueError; this is an open validation-behaviour decision for the human.

The existing SPECIFICATION.md section 12.5 still describes settlement:001 as the prototype's canonical entity identifier. It is intentionally unchanged here; if this experiment is promoted into normative architecture, that specification section will require a corresponding human-reviewed update.

Golden RNG values pin CPython 3.12 random.Random behaviour. A supported Python-version change requires deliberate review of those compatibility values.

### Scope

This is an experiment result, not a final identifier, address, randomness, validation, or entity-alias protocol.
