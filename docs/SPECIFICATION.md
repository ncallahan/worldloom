# Worldloom Specification

## Status

This is the initial normative outline. Details remain provisional until exercised by the prototype.

## 1. World state

The canonical world state SHALL support, directly or through extensible representations:

1. entities
2. fields
3. events
4. relationships
5. constraints
6. uncertain/statistical states
7. provenance

State must have stable identity so that facts can persist across simulation steps.

## 2. Module contract

A module SHALL expose enough metadata to identify:

- module name and version
- inputs
- outputs
- spatial resolution
- temporal resolution
- dependencies
- uncertainty behaviour

A module SHOULD expose lifecycle operations equivalent to initialise, advance/step, and validate.

## 3. State exchange

Modules SHALL exchange information through canonical world state or explicitly defined adapter contracts rather than hidden direct dependencies.

## 4. Time

The simulation engine SHALL permit modules with different temporal resolutions. It SHALL NOT require every module to execute at every smallest timestep.

## 5. Events

Events SHALL be representable as persistent records with enough information to identify their time, effects, and provenance.

## 6. Resolution

The system SHALL distinguish:

- uncertainty about a possible future or unresolved world state
- concrete facts already established in simulated history

Resolution SHALL produce persistent state rather than silently resampling an already-resolved fact.

## 7. Provenance

Derived state SHOULD retain provenance sufficient to identify its producer, inputs, configuration, simulation time, and uncertainty/confidence where available.

## 8. Reproducibility

Experiments SHOULD record configuration, software versions, random seeds, execution parameters, measurements, and outputs.

## 9. External systems

The architecture SHOULD favour adapters to established specialist software over reimplementation when an appropriate system already exists.

## 10. Validation

Architectural changes SHALL be accompanied by tests where behaviour is testable and by corresponding documentation updates.
