# Worldloom Experiments

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

### Purpose

Test whether a coarse observation can be used to create a resolved fact while preserving enough provenance to explain the dependency and to detect when that dependency has changed.

### Question

Can a world fact be resolved from a broad observation without losing the link to that observation, and can a stable fingerprint of the observation support later investigation of invalidation and re-resolution without committing to a full invalidation engine?

### Method

1. Create a coarse observation such as `settlement.candidates`.
2. Resolve a persistent entity from that observation and record the observation as an explicit `Provenance.inputs` dependency.
3. Record a deterministic fingerprint derived from the observation payload and from the selected entity payload.
4. Replace the coarse observation with a changed version.
5. Verify that the already-resolved entity remains stable and that the provenance still identifies the dependency it was originally derived from.

### Evidence from the prototype

The current implementation exercises this pattern through the `test_progressive_resolution_exposes_invalidation_boundary` and `test_observation_provenance_records_a_deterministic_fingerprint` tests. The experiment demonstrates that:

- the canonical entity remains stable when a broad observation changes;
- the dependency link is retained in provenance;
- a deterministic fingerprint can be attached to the observation or entity provenance without requiring a full invalidation model.

This is intentionally narrower than a complete invalidation framework. It establishes the foundational requirement: a resolved fact should carry enough provenance to later support an invalidation or re-resolution policy without locking in the full semantics today.

### Interpretation

The current prototype shows that the general idea works at this stage: a coarse observation can inform a resolved entity while the entity's provenance preserves both the dependency chain and a stable fingerprint. That is enough to test the architecture without building a complete progressive-world invalidation system.

### Remaining open questions

- what precise invalidation semantics should be used when a broad observation is superseded;
- whether invalidation should be query-based, event-based, or explicit;
- whether-store-versus-compute should be the default for deferred re-resolution;
- how module-level random seeds should be captured for deterministic regeneration of derived outputs.

Those questions remain explicitly future work, and the prototype keeps them separate from the current observation/provenance contract.
