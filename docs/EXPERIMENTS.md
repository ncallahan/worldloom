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

The prototype creates a coarse `settlement.candidates` observation, resolves one candidate into a persistent entity, then replaces the observation with changed data. The entity remains unchanged, its provenance retains the observation dependency, and both values receive deterministic payload fingerprints. This verifies the general idea without introducing observation version history or an invalidation policy.

### Interpretation

Write-in-place observations are sufficient for this first feasibility experiment. A fingerprint is a useful minimal foundation: later code can compare the current observation payload with the payload that informed a resolved fact. The experiment does not establish whether invalidation should be query-based, event-based, or explicit, nor whether stale facts should be marked, removed, or reconciled.

### Follow-up paths

- Decide how to retain provenance history when observation versioning is introduced.
- Investigate invalidation and reconciliation semantics after an explicit world change.
- Test whether fingerprints plus stored module configuration and per-module seeds are sufficient for deterministic regeneration.
- Compare storing derived outputs with recomputing them from snapshots and module inputs.
