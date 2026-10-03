---
type: experiment
status: experiment
summary: Migrated documentation page; source material retained verbatim for Phase 3 traceability.
related: ["[[index]]"]
---

# Progressive Resolution Provenance

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
