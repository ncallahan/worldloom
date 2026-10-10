---
type: experiment
status: process
summary: Maintainability audit of the Markdown-vault exporter, using the source-complexity baseline and targeted review of implementation, tests, and interface documentation.
related: ["[[devwiki/experiments/src-function-complexity-audit]]", "[[devwiki/architecture/obsidian-markdown-interface]]", "[[devwiki/vision/fmg-import-vault-mvp]]"]
---

# Markdown-vault exporter maintainability audit

## Purpose

Assess the maintainability risks in the current Markdown-vault exporter before considering refactoring.

This is a review of the existing implementation, not a refactoring proposal or a rule-setting exercise. The audit is intended to identify responsibility boundaries, coupling, test-coverage risks, and plausible future refactoring seams while preserving the distinction between evidence and future decisions.

## Scope and evidence

The review covers:

- `src/worldloom/adapters/markdown_vault/exporter.py`
- `tests/unit/test_markdown_vault.py`
- the normative Markdown-interface boundary recorded in `devwiki/architecture/obsidian-markdown-interface.md`
- the source function-size and cyclomatic-complexity baseline produced by the companion audit

The companion complexity audit identified `export_markdown_vault` as the strongest source-level hotspot: 162 lines of source span and cyclomatic complexity 55 (Radon rank F). Other substantial functions include `_note` (97 lines, CC 23), `_import_note` (62 lines, CC 21), and `_display_map` (substantial branching and policy logic). These measurements are triage evidence, not quality thresholds.

The Markdown-vault test module currently reports approximately 46% coverage for the Markdown-vault implementation. The existing tests nevertheless exercise a number of important end-to-end behaviours, including determinism, filename sanitisation, duplicate-title disambiguation, link resolution, collision protection, hand-edit detection, rollback after write failures, malformed values, surrogate handling, and non-FMG worlds.

## Maintainability assessment

### 1. Responsibility density

`export_markdown_vault` is an orchestration point for several distinct responsibilities:

1. Build the projection model: derive titles, paths, display names, path collisions, and inverse relationships.
2. Validate source data: entity identifiers, strings, and JSON serialisability.
3. Render Markdown: entity notes, kind indexes, the root index, and the import report.
4. Construct projection metadata: world fingerprint, per-file hashes, and the vault marker.
5. Reconcile an existing vault: marker validation, hand-edit detection, protection of foreign files, and removal of obsolete generated files.
6. Perform transactional filesystem replacement: staging, backup, copying, and rollback.

The high complexity therefore reflects responsibility density at the orchestration boundary, rather than uniformly complicated helper functions.

### 2. Helper structure

Several lower-level helpers already have relatively narrow purposes, including:

- `_id_parts`
- `_title`
- `_filename`
- `_yaml_value`
- `_frontmatter`
- `_safe_text`
- `_display`
- `_link`
- `_items`
- `_mesh`

This is evidence that the implementation is not simply an undifferentiated monolith.

The larger helpers have broader semantic responsibilities. In particular:

- `_display_map` contains the policy for choosing human-readable disambiguation labels.
- `_note` combines frontmatter construction, imported-fact rendering, relationship rendering, inverse relationships, and provenance rendering.
- `_import_note` interprets import diagnostics and renders the import report.
- `export_markdown_vault` coordinates these operations with validation and filesystem lifecycle management.

These are plausible future seams, but the audit does not establish that they should be extracted.

### 3. Filesystem and transactional complexity

The latter portion of `export_markdown_vault` is materially different from the projection/rendering work.

It handles:

- refusing unsafe target paths;
- recognising Worldloom-managed vaults;
- detecting changes to previously generated files;
- refusing to overwrite unlisted files;
- staging generated output;
- backing up managed files;
- removing obsolete generated files;
- copying new files into place;
- restoring the previous state after a failure.

This logic represents a meaningful safety invariant: a failed export should not leave the existing vault partially replaced.

The existing tests explicitly exercise injected failures during both backup and write phases. Any future separation of filesystem responsibilities therefore needs to preserve these transactional semantics, rather than merely reduce function length.

### 4. Test coverage and refactoring risk

The approximately 46% coverage makes internal refactoring comparatively risky.

The current test suite has strong end-to-end coverage of several externally visible invariants, but coverage alone does not establish that every branch in the exporter is protected. In particular, the complexity audit indicates substantial branching in code responsible for:

- disambiguation;
- diagnostic interpretation;
- validation;
- existing-vault reconciliation;
- rollback.

Before a structural refactor, targeted characterization tests would provide more useful protection than relying on the existing aggregate coverage figure alone.

This is a risk assessment, not a recommendation to increase coverage to a particular threshold. No threshold is established by this audit.

### 5. Architectural boundary

The exporter is consistent with the documented semantic boundary in which Markdown is a human-facing representation of Worldloom state rather than an independent authority for world facts.

Consequently, maintainability work should preserve the distinction between:

- canonical Worldloom state;
- derived projection data;
- human-readable presentation;
- and filesystem management of generated projection artifacts.

The audit does not propose changing that boundary.

## Candidate future seams

The following areas appear to be plausible candidates for future investigation:

| Area | Why it is a possible seam | Main risk to preserve |
| --- | --- | --- |
| Projection-model preparation | Separates derived paths, titles, displays, and inverse relationships from I/O | Deterministic ordering and cross-reference consistency |
| Markdown rendering | Separates representation construction from filesystem lifecycle | Exact filenames, frontmatter, links, and projection vocabulary |
| Import-report rendering | Has its own diagnostic interpretation and output structure | Correct treatment of heterogeneous diagnostic shapes |
| Vault reconciliation | Separates managed-file safety checks from generation | Never overwrite hand-edited or foreign files unexpectedly |
| Transactional write/rollback | Is conceptually independent of Markdown semantics | Atomic-enough replacement and restoration after failure |
| Display/disambiguation policy | Encapsulates human-readable naming decisions | Stable, unique displays without changing entity-ID-based paths |

These are hypotheses for future design work, not prescribed decomposition.

## Invariants identified for future work

Any future refactoring should preserve, at minimum, the behaviours currently represented by the implementation and tests:

- entity-ID-based projected filenames;
- deterministic output;
- unique and stable display labels within a kind;
- resolvable generated wikilinks;
- safe filename sanitisation and reserved-name handling;
- protection against path collisions;
- protection against Markdown/code-fence injection in rendered values;
- rejection of unsafe string values before writing;
- rejection of non-JSON-serialisable values with useful source paths;
- preservation of foreign files;
- detection of hand-edited managed files;
- safe handling of deleted managed files;
- marker integrity and file hashes;
- rollback when filesystem writes fail;
- provenance and import-report representation;
- projection-only semantics rather than Markdown becoming canonical state.

This list records observed/required behaviours for later characterization; it is not a new normative architecture specification.

## Interpretation

The exporter is maintainable enough to continue serving the MVP, but it has a clear concentration of orchestration complexity and several responsibilities that could eventually be separated.

The principal concern is not function length by itself. The more important issue is that projection construction, rendering, validation, vault reconciliation, and transactional filesystem management are coordinated within the same top-level operation.

At the same time, the existing helper structure and end-to-end tests provide a reasonable starting point. The approximately 46% coverage means that structural refactoring should not be undertaken merely because the complexity metrics are high.

The safest future sequence would be to improve characterization of the behaviours that matter most, then evaluate individual seams against those tests. No such refactoring is proposed or authorised by this audit.

## Question | Evidence | Tentative conclusion

| Question | Evidence | Tentative conclusion |
| --- | --- | --- |
| Is the exporter unusually complex? | `export_markdown_vault` has 162 source lines and CC 55; several helpers are also substantial. | Yes; it merits maintainability attention. |
| Is the complexity solely caused by poor factoring? | The implementation already has several narrow helpers, while the top-level function coordinates multiple genuinely distinct responsibilities. | No; some complexity is inherent orchestration and safety logic. |
| Is immediate refactoring justified? | The exporter has approximately 46% test coverage despite meaningful end-to-end tests. | No; refactoring should wait for stronger characterization of critical behaviours. |
| Are there plausible refactoring seams? | Projection preparation, rendering, report generation, reconciliation, transactional writing, and display policy have distinguishable responsibilities. | Yes, but the correct decomposition remains an open design question. |
| Does the audit establish complexity or coverage thresholds? | The companion complexity audit is explicitly diagnostic and proposes no hard limits. | No. |
| Does this audit change the Markdown architectural boundary? | The current implementation and architecture documentation treat Markdown as a projection of canonical Worldloom state. | No. |

## Unresolved questions

- Which of the candidate seams, if any, produces a materially clearer design without obscuring projection invariants?
- Which behaviours need additional characterization before a structural refactor can be considered low risk?
- Should filesystem transaction handling eventually be represented as a separately testable component?
- How much of the current rendering policy should remain together because its output semantics are tightly coupled?
- Whether the current end-to-end tests sufficiently characterize deterministic output across larger FMG worlds remains to be established.

## Status

**Process / audit.** This page records the maintainability findings, implementation progress, and known follow-ups. It does not establish a coverage threshold, complexity threshold, or new architectural rule.

## Invariant coverage matrix

The matrix below records the invariants identified by this audit and the direct tests that characterize them. The source complexity audit scans only `src/**/*.py`; test modules are outside its source scan.

| Invariant | Coverage |
| --- | --- |
| entity-ID-based projected filenames | `test_markdown_vault_filenames_remain_entity_id_based` |
| deterministic output | `test_marker_safety_determinism_and_roundtrip`, `test_canonical_indexes_are_deterministic_and_marker_burg_counts_sum` |
| unique and stable display labels within a kind | `test_link_display_disambiguation_rules`, `test_display_text_is_unique_within_kind_for_canonical_exports_and_slices` |
| resolvable generated wikilinks | `test_all_wikilinks_resolve_and_report_duplicate_titles`, `test_group_by_indexes_are_categorical_by_name_and_safe` |
| safe filename sanitisation and reserved-name handling | `test_filename_sanitisation_and_reserved_names` |
| protection against path collisions | `test_duplicate_titles_are_unique_and_forced_collision_aborts` |
| protection against Markdown/code-fence injection in rendered values | `test_frontmatter_order_and_markdown_injection`, `test_long_and_multiline_text_fields_are_fenced_and_not_markdown`, `test_group_by_code_spans_pad_edge_backticks_and_empty_values`, `test_attribute_and_relationship_field_names_are_code_spans` |
| rejection of unsafe string values before writing | `test_surrogate_and_non_fmg_world`, `test_surrogate_in_written_world_sources` |
| rejection of non-JSON-serialisable values with useful source paths | `test_non_json_serialisable_attribute_reports_entity_path` |
| preservation of foreign files | `test_marker_safety_determinism_and_roundtrip` |
| detection of hand-edited managed files | `test_marker_safety_determinism_and_roundtrip` |
| safe handling of deleted managed files | `test_marker_safety_determinism_and_roundtrip` |
| marker integrity and file hashes | `test_marker_safety_determinism_and_roundtrip` |
| rollback when filesystem writes fail | `test_injected_write_failure_leaves_existing_vault_unchanged`, `test_injected_write_failure_during_write_restores_marker_and_vault` |
| provenance and import-report representation | `test_thimaland_import_note_diagnostics_are_integer_totals`, `test_surrogate_in_written_world_sources`, `test_surrogate_and_non_fmg_world` |
| projection-only semantics rather than Markdown becoming canonical state | `test_markdown_vault_export_does_not_mutate_world_state` |

## Exporter coverage-gap matrix

The pre-refactor exporter coverage snapshot recorded 413 statements, 11 missed statements, 224 branches, 16 partial branches, and 96% coverage.

The post-characterization exporter coverage snapshot recorded 413 statements, 0 missed statements, 224 branches, 1 partial branch, and 99% coverage.

| Function | Baseline gap | Final classification |
| --- | --- | --- |
| `_yaml_value` | line 53 | now covered |
| `_mesh` | line 111 | now covered |
| `_reference_links` | 128→121 | now covered |
| `_display_map` | 148→154 | now covered |
| `_note` | 204→203, 207→212, 218→221, 244, 255, 284→289 | all now covered except 207→212, which remains a defensive branch left untested |
| `_import_note` | 318, 339 | now covered |
| `_validate_strings` | 393 | now covered |
| `export_markdown_vault` | 524, 535-536, 548, 572→569 | now covered |

The remaining `_note` branch 207→212 is defensive: it requires an `attributes` value that is not a `dict` but still provides the `.get()` interface required earlier by title derivation, which is outside the normal JSON-shaped WorldState data exercised here. No exporter gap is classified as suspected dead code.

This matrix records the actual baseline gaps and the actual final Coverage result; it does not establish a coverage threshold.



## Progress

**R1 done (implementation).** The transactional managed-tree writer and manifest construction have moved to `src/worldloom/adapters/markdown_vault/writer.py`; rendering, naming, and escaping remain in `exporter.py`. The source-only Radon ratchet measured `export_markdown_vault` at CC 66 before extraction and CC 36 after extraction. The `complexity-baseline-candidate` artifact supported changing only that baseline entry from 66 to 36. No behavior fix is included in R1.

## R1b safety fixes

Both R1 known issues are fixed by R1b.

1. **Fresh-vault rollback directory cleanup — fixed.** A failed first export now removes the empty directories created by that call, deepest first, including the vault root and any missing ancestors. The test `test_failed_fresh_write_removes_created_tree_and_retry_succeeds` compares the full tree, including directories and root existence, and verifies that retry succeeds. The parameterised `test_copy_failure_rolls_back_file_set_and_bytes` covers first, middle, and last write-phase failures on fresh and existing vaults, and verifies existing directory state is restored.
2. **Stale empty-directory cleanup — additional behaviour change.** After a successful write, directories made empty by deleting stale managed files are pruned up to, but not including, the vault root. Directories containing foreign files are retained. Covered by `test_stale_empty_directories_are_pruned_but_foreign_content_and_root_remain`.
3. **Manifest path validation — fixed.** Manifest file keys and hashes are validated before hand-edit checks or manifest-derived file access. Unsafe new-file paths and manifest names are rejected before writes. Coverage includes `test_manifest_path_outside_root_is_rejected_without_changes`, `test_unsafe_manifest_paths_are_rejected_before_filesystem_changes`, `test_non_string_manifest_key_is_rejected`, `test_non_string_manifest_hash_is_rejected`, `test_unsafe_new_file_paths_are_rejected`, `test_manifest_name_must_be_plain_filename`, and `test_manifest_symlink_escape_is_rejected_when_symlinks_available`.
4. **BaseException rollback — additional behaviour change.** Rollback now also runs for `BaseException` subclasses such as `KeyboardInterrupt`, then re-raises. Covered by `test_keyboard_interrupt_during_write_rolls_back_and_propagates`.

The first issue concerned leftover directories created for generated files' nested paths, not directories created by the output path itself. Created directories are tracked explicitly and removed only when empty; pre-existing directories are never removed by rollback. No rendering, naming, importer, core, exporter, projection-version, or complexity-baseline changes are part of R1b.

## Planned next steps

- **R1b:** merged in PR #60.
- **R2:** complete in PR #61 — naming and markup helpers extracted and direct helper tests added.
- **R3a:** extract note and import-report rendering while preserving output behaviour.
- **R3b:** extract the plan builder, index rendering, and orchestration, targeting `export_markdown_vault`.
- **Report-shape unification:** follow R3b; it will change `render_import_note` input handling.
- **Step 7:** return to the planned on-demand local-detail design after the exporter work.

R2 does not change the architecture boundary, projection version, or complexity baseline.


## R2 complete — naming and markup helpers

**R2 is complete in PR #61.** The behaviour-preserving extraction moves the strict entity-ID parser, title sanitisation, entity filename construction, and display-map policy into `naming.py`; YAML/frontmatter serialisation, safe text, display escaping, code spans, text fields, and wikilink formatting into `markup.py`. The exporter remains the orchestration and rendering boundary. Strict ID validation remains strict; generated output bytes and projection version are unchanged. No complexity-baseline entries were added. Direct tests cover the moved helpers, alongside end-to-end characterization tests.

## R3a complete in PR #62

R3a moves `_items` to `notes.as_items`, keeps `_mesh` and `_reference_links` private in `notes.py`, exposes `render_note` and `render_import_note`, and moves `PROJECTION_VERSION` to `version.py` without changing its value. Rendering is split into section helpers. The existing per-entity `_validate_strings(entity, ...)` call remains in its original position even though `world.entities` was validated earlier; removing it is a follow-up, not part of this refactor. Direct characterization tests cover the moved note and import-report rendering outcomes.

## R3b complete in PR #63

R3b moves projection preparation into `plan.py`: entity-copy/title/path assignment, projected-path collision checking, display-map construction, inverse-reference construction, and duplicate-title counting. `ProjectionPlan` carries the derived entities, paths, displays, disambiguation counts, inverse references, and duplicate counts. Index rendering moves into `indexes.py`, with a shared member-sort-key factory and separate group-by, kind, and root index helpers. `export_markdown_vault` now orchestrates planning, the unchanged validation sequence, note rendering, index insertion, import-report rendering, fingerprinting, and managed-tree writing.

The required ordering is retained: planning steps 1–5 run in the original order; source validation and per-entity validation remain in their original positions; note files are inserted in entity order; sorted-kind group indexes are inserted in `type`, then `group` order before each kind index; `index.md` precedes `_worldloom/import.md`. The hidden `_title` and `_path` keys remain on entity copies as before. The projection version and intended generated bytes are unchanged.

The tolerant-projection hardening follow-up is complete: extra entity fields and malformed FMG metadata are prepared before fingerprinting, provenance attributes are handled independently, and surrogate checks use ASCII fast paths plus a compiled expression. Next is importer cleanup of `build_entities`, then step 7.

## U0 — frozen reference retired

U0 removes the frozen pre-R1 exporter and its differential test after the R1–R3 extraction series. The five former differential scenario groups were inventoried in PR #64: edge cases, canonical FMG worlds/slices, errors, vault lifecycle, and failure injection. The scenario inventory is now represented by direct tests that assert observable outcomes rather than equality against a second implementation. Existing output assertions were retained; direct checks were added for slice-export determinism and save/load round trips, target-file and malformed-marker failures, unlisted projected-path collisions, changed-world overwrite, and stale-note removal after an entity is deleted. The generated-file-order test now lives in tests/unit/test_markdown_vault_exporter.py.

This is a test-maintenance and helper-tidying change, not a change to the projection contract. Later PRs that intentionally change generated output must update or add direct tests for the intended bytes and failure properties. The frozen reference is not to be reintroduced as the oracle for later output changes.

## Known follow-ups (not fixed)

- `writer.py`: a non-bytes value in the files mapping raises an error prefixed “Unsafe path:”, which misdescribes the problem.
- `writer.py`: `root.resolve()` is recomputed for every validated path.
- The frozen pre-R1 reference exporter was retired in U0 after the R1–R3 extraction series. Later output-changing PRs rely on direct tests asserting intended bytes, ordering, exception properties, and lifecycle outcomes; see `devwiki/process/development-workflow.md`.
- The copied entities retain hidden `_title` and `_path` keys injected by projection planning; removing or replacing these is deferred.
- The world fingerprint hashes the entire fields mapping (including the mesh) on every export and is likely a large share of export time. Measure it once rendering and writing are separate.
- Importer cleanup of `build_entities` remains the next implementation task; preserve current import behaviour and report shapes, then return to step 7.
