---
type: experiment
status: experiment
summary: Measurement-only comparison of FMG population layers and candidate reference fields.
related: ["[[devwiki/current]]", "[[devwiki/process/wiki-conventions]]"]
---

# FMG population layering and candidate-reference measurement

## Question

What do direct, deterministic measurements of the canonical FMG JSON exports show about population fields, state and religion aggregates, burg/cell relationships, and candidate reference-field target spaces?

## Scope

**Measurement only.** This experiment does not change `src/worldloom`, does not use the importer, makes no claims about FMG semantics, and promotes nothing to architecture. All interpretations remain hypotheses until the measured evidence is reviewed. Counts, sums, differences, type distributions, and target-space match fractions are observations, not semantic conclusions.

## Hypotheses (not conclusions)

- **H-A:** For each state, `states[i].urban` may be close to the sum of `burgs[b].population` grouped by `burgs[b].state == i`, and may also be close to the sum grouped by the state of the referenced burg cell, `cells[burgs[b].cell].state == i`.
- **H-B:** `states[i].rural` may be close to the sum of `cells[c].pop` for cells with `cells[c].state == i`.
- **H-C:** `burgs[b].state` may equal `cells[burgs[b].cell].state`, and `cells[burgs[b].cell].burg` may equal `burgs[b].i`.
- **H-D:** Cells that hold a burg may include zero-population cells; the experiment counts them and measures the share of total cell population on burg cells.
- **H-E:** The sum of all states' rural and urban values may be close to the sum of all cell populations and all burg populations, respectively.
- **Religion aggregates:** Where religion rural/urban fields exist, they may agree with sums of cell populations and burg populations grouped by cell religion.
- **Candidate references:** `states.capital` may refer to a burg; `burgs.culture` to a culture; `provinces.burg` to a burg; `religions.culture` to a culture; `rivers.parent` and `rivers.basin` to rivers; and `rivers.mouth` and `rivers.source` to cells. These are candidate mappings only.

## Method

The measurement code reads exports directly with `json.load`; it does not invoke Worldloom's importer. For each export it records the three settings fields and type/value, numeric population-field summaries, per-state and per-religion claimed values versus grouped sums, exact and relative differences, burg/cell agreement counts, aggregate totals, and candidate-reference type distributions and target-space fractions. The relative tolerance reported is (10^{-9}). Integer booleans are excluded from integer/numeric classification. Missing collections and malformed records are tolerated and counted where applicable. Output is deterministic JSON and Markdown; no timing or wall-clock measurements are used.

## Results

**None recorded here yet.** Results are to be copied from the CI job summary in a follow-up after the measurement tests run successfully. No measured values or conclusions are claimed by this page.
