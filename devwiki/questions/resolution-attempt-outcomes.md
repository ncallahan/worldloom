---
type: question
status: open
summary: Design question for recording attempted resolution outcomes, including skipped calculations.
related: ["[[devwiki/process/wiki-conventions]]", "[[devwiki/questions/identifier-address-model]]", "[[devwiki/architecture/events-and-history]]", "[[devwiki/architecture/provenance]]", "[[devwiki/glossary]]", "[[devwiki/experiments/burg-ward-local-detail]]", "[[src/worldloom/detail/burg_wards.py]]", "[[src/worldloom/why.py]]", "[[src/worldloom/core/persistence.py]]", "[[devwiki/current]]"]
---

# Resolution-attempt outcomes

## Problem

- **FACT** — When a calculation is attempted but yields no value, absence alone is ambiguous: it can mean not yet attempted, attempted and failed, or attempted before any record existed.
- **OPEN** — This is a null-value problem involving distinct possibilities: unknown, unknowable, not yet calculated, or undefined because of an error. Their eventual representation is not decided here.

## Current burg-ward behaviour

- **FACT** — In `src/worldloom/detail/burg_wards.py`, a successful resolution adds ward entities, records a `local_detail.resolved` event, and attaches entity provenance to the generated wards. The event includes the burg entity ID and `question_id` (`burg.wards`).
- **FACT** — A skip is returned in the resolver summary's `skipped` list and printed by the CLI as a warning; the skip itself is not persisted as an outcome record.
- **FACT** — A burg with an existing `local_detail.resolved` event matching its entity ID and `question_id` is counted as `already_resolved` and is a no-op.
- **FACT** — The skip-reason strings in the resolver are `unknown-burg`, `not-a-burg`, `missing-population`, `non-numeric-population`, `non-finite-population`, `non-positive-population`, and `invalid-population-claim`. The last is a defensive fallback after claim validation.
- **FACT** — The `why` query reads recorded provenance, observations, and events without rerunning resolution or RNG. Its current trace cannot explain why a burg has no wards when neither a resolution event nor a persisted skip reason exists; it reports that no resolution is recorded and the reason is not recorded.

## What an attempt can establish

- **FACT** — The resolver can observe which check failed and return its corresponding reason code.
- **OPEN** — The resolver cannot, from that failed check alone, distinguish whether a value is unknown, unknowable, or undefined because of an error.
- **PROPOSED (pending owner confirmation)** — Record the observable cause and the attempt now; treat “unknown”, “unknowable”, and “undefined” as later classifications layered on top. This must not settle the broader open question of how uncertainty should be represented.

## Owner decisions

- **OWNER DECISION** — Whenever a calculation is attempted, something is recorded.
- **OWNER DECISION** — The preferred direction is an event, a sibling of `local_detail.resolved`, keyed by `question_id`; an attached observation is a possibility, but its meaning is not yet specified.
- **OWNER DECISION** — Request errors such as `unknown-burg` and `not-a-burg` are not persisted, because they are not facts about the world.
- **OWNER DECISION** — Whether a non-positive population claim should remain a skip or become “resolved to no wards” is deferred. The current leaning is “resolved to no wards”, but the reason the model treats non-positive claims as skips must first be understood.

## Proposed record and reading model

- **PROPOSED (pending owner confirmation)** — Record the entity ID, `question_id`, reason code (reusing the existing strings), producer, version, and burg input fingerprint at attempt time. This would let the `why` query report when a skip has become stale and prevent a later resolver version from being confused with an old skip.
- **PROPOSED (pending owner confirmation)** — Idempotence: do not append an identical repeat with the same reason, fingerprint, and version.
- **PROPOSED (pending owner confirmation)** — Retention: append-only. Readers use the latest outcome per entity and question according to event-list order; no deletion or compaction.
- **PROPOSED (pending owner confirmation)** — Key outcomes by `question_id`, so later questions such as hamlets or rural population can reuse the mechanism. The first implementation would cover `burg.wards` only.
- **PROPOSED (pending owner confirmation)** — With recorded outcomes, the `why` query's “reason not recorded” wording would instead report the recorded reason (and, where available, whether its input fingerprint is stale).

## Open questions and caveats

- **OPEN** — What does the “attached observation” mean? It might be unnecessary initially; a lookup index should be considered only if scanning events becomes awkward.
- **FACT** — `src/worldloom/core/persistence.py` serializes events as a list and decodes that list in sequence into the snapshot's event list.
- **OPEN** — Event time fields used by the burg-ward resolver are currently placeholder `0.0`, so “latest outcome” cannot be inferred from those timestamps. Persistence code preserves list sequence in its encode/decode structure, but a round-trip test or check of the repository's persistence tests is still needed to verify that order is preserved end-to-end before relying on it.
- **FACT` — The project uses “events” for both simulation/process events (such as `local_detail.resolved`) and occurrences within the world. `devwiki/architecture/events-and-history.md` uses “events” in both senses.
- **OPEN** — This terminology overlaps. The owner's provisional term for in-world occurrences is “historical events”; whether and how to distinguish these from simulation/process events remains open.
- **OPEN** — Possible later coarse outcome categories have not been decided.
- **OPEN** — Re-attempt behaviour after an input is corrected has not been decided beyond the proposed append-only/latest-outcome approach above.
- **PROPOSED (pending owner confirmation)** — A later, small measurement experiment could count burg population claim values classified as missing, non-numeric, non-finite, zero, or negative across the three canonical FMG exports, to help understand the non-positive case. This experiment has not been performed and is not part of this documentation change.

## Existing experiment note

- **FACT** — `devwiki/experiments/burg-ward-local-detail.md` currently says a future run-result/report artifact could retain the skip summary.
- **OWNER DECISION** — The current direction is to record an event instead. The experiment page is intentionally not edited by this change.
