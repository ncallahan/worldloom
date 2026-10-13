---
type: question
status: open
summary: Open questions about representing in-world time, dates, and calendars.
related: ["[[index]]", "[[devwiki/architecture/time-and-scheduling]]", "[[devwiki/architecture/events-and-history]]", "[[devwiki/questions/resolution-attempt-outcomes]]"]
---

# In-world time and dating

## Current implementation

**FACT** — `SimulationConfig` has numeric `time_unit` and `start_time` settings, `SimulationContext.time` is numeric, `Event.time` is a float, and modules may declare a numeric `temporal_interval`. The engine schedules modules according to those intervals. These are numeric simulation-time coordinates, not calendar dates. See `src/worldloom/interfaces/protocols.py` (`SimulationConfig` and `SimulationContext`), `src/worldloom/core/events.py`, `src/worldloom/simulation/engine.py`, and [[devwiki/architecture/time-and-scheduling]].

**FACT** — The burg-to-ward resolver writes its resolution event with `time=0.0` and generated ward provenance with `time=0.0`. This is placeholder time in that resolver, not an implemented historical dating scheme. See `src/worldloom/detail/burg_wards.py`.

**FACT** — The current `Event` record stores a numeric `time` and has no calendar or date type. `SimulationConfig` defines `time_unit` and numeric `start_time`; `SimulationContext.time` is numeric. These interfaces provide no calendar abstraction.

## Open questions

**OWNER DECISION** — Table or session time is out of scope; no real-time adaptation of the world during play is expected.


**OPEN** — Date type and calendar systems: whether to support one calendar, multiple calendars, conversion between calendars, or a neutral internal date representation.

**OPEN** — Process time versus in-world time: how to distinguish when a simulation process ran from when an event or fact is said to apply in the fictional world.

**OPEN** — Uncertain or approximate dates: how to represent ranges, precision, and confidence. Soft anchors in anchored-history reconciliation may need date ranges rather than a single point.

**OPEN** — Tolerance and precision for approximate dates relate to resolution and scale as approximate locations do on coarse maps; no representation is decided.

**OPEN** — Granularity: whether dates can be expressed at year, season, month, day, or finer scales, and how mixed precision is compared.

**OPEN** — Ordering events with equal times: whether equal timestamps imply no known order, require a secondary ordering, or allow explicit causal ordering.

**OPEN** — Terminology and semantics for “historical events” versus simulation/process events. The relationship to resolution-attempt outcomes is open; see [[devwiki/questions/resolution-attempt-outcomes]]. Do not infer a terminology decision from this question page.

## Toy experiment

**OWNER DECISION** — The first toy experiment will use plain integer years. This is explicitly a convenience for the experiment, not a decision about Worldloom's eventual date model.