---
type: experiment
status: experiment
summary: Experiment record migrated verbatim from docs/EXPERIMENTS.md.
related: ["[[index]]"]
---

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
