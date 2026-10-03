---
type: architecture
status: normative
summary: Migrated documentation page; source material retained with Phase 3 traceability.
related: ["[[index]]"]
---

# Time And Scheduling

## 6. Time and orchestration

Modules operate at different natural temporal resolutions. For example:

- weather: minutes
- rivers and hydrology: hours/days
- economy: days/months
- population: months/years
- politics: days/years
- culture: decades
- geography: centuries/millennia

Simulation time is a numeric coordinate whose unit is supplied by simulation configuration. A module may declare a positive numeric temporal interval in those simulation-time units. The scheduler invokes each module when its interval is due rather than forcing every module through one universal timestep.

The scheduler is deterministic: when multiple modules are due at the same simulation time, declared dependency order is respected and the original module input order remains the tie-breaker for otherwise independent modules.

Each invocation receives the current simulation time and the elapsed time since that module's previous invocation. A module without a temporal interval is treated as a one-time/static module during a scheduled run.

Event-triggered scheduling is intentionally outside the current scheduler contract and remains future work.

## 4. Time

The simulation engine SHALL permit modules with different temporal resolutions. It SHALL NOT require every module to execute at every smallest timestep.

### 4.1 Simulation time

Simulation time SHALL be represented as a numeric coordinate. The simulation configuration SHALL identify the unit associated with that coordinate; the unit is configuration rather than encoded into the numeric value.

A module MAY declare a positive numeric temporal interval in the configured simulation-time unit. A module with no temporal interval SHALL be treated as static/one-time for a scheduled run.

### 4.2 Scheduling

When running a bounded scheduled period, the engine SHALL invoke each module when its declared interval is due.

The scheduler SHALL:

- be deterministic;
- preserve declared dependency ordering when multiple modules are due at the same simulation time;
- use the modules' input order as the tie-breaker for otherwise independent modules;
- invoke a module without a temporal interval once at the start of the scheduled period;
- reject non-positive temporal intervals;
- NOT require event-triggered scheduling.

### 4.3 Execution context

Each module invocation SHALL receive:

- the current simulation time;
- the elapsed simulation time since that module's previous invocation;
- the simulation step associated with the scheduler;
- the configured random seed and execution metadata where supplied.

The first invocation of a module in a scheduled run SHALL receive zero elapsed time.

The existing single-cycle execution form remains available: when no scheduling end time is supplied, the engine invokes the modules once in dependency order at the supplied context time.

### Time and events

Do not assume one universal simulation timestep. Different domains naturally operate at different temporal resolutions, and the orchestrator should schedule work accordingly.

Events are first-class records and may change state, trigger dependent work, resolve uncertainty, or record external/endogenous occurrences.
