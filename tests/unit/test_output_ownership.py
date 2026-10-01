"""Unit tests for the provisional canonical output ownership validation."""

from worldloom.core import WorldState
from worldloom.interfaces import (
    DataKind,
    ModuleSpec,
    OutputPolicy,
    OutputSpec,
    SimulationConfig,
)
from worldloom.simulation import SimulationEngine


class OwnershipModule:
    def __init__(self, name, outputs, log=None):
        self.log = log if log is not None else []
        self.spec = ModuleSpec(
            name=name,
            version="ownership-experiment",
            outputs=outputs,
        )

    def run(self, world, context):
        self.log.append(self.spec.name)


def output(name, policy=OutputPolicy.EXCLUSIVE, **kwargs):
    return OutputSpec(name, DataKind.STATE, policy=policy, **kwargs)


def engine(*modules):
    return SimulationEngine(modules, SimulationConfig(time_unit="days"))


def test_duplicate_exclusive_producers_are_rejected_before_execution():
    log = []
    first = OwnershipModule("producer.a", (output("field:shared.value"),), log)
    second = OwnershipModule("producer.b", (output("field:shared.value"),), log)

    try:
        engine(first, second).run(WorldState())
    except ValueError as exc:
        message = str(exc)
        assert "field:shared.value" in message
        assert "producer.a" in message
        assert "producer.b" in message
    else:
        raise AssertionError("Expected duplicate EXCLUSIVE producer error")

    assert log == []


def test_duplicate_exclusive_producers_are_also_rejected_for_scheduled_runs():
    first = OwnershipModule("producer.a", (output("field:shared.value"),))
    second = OwnershipModule("producer.b", (output("field:shared.value"),))

    try:
        engine(first, second).run(WorldState(), until=1.0)
    except ValueError as exc:
        assert "field:shared.value" in str(exc)
    else:
        raise AssertionError("Expected duplicate EXCLUSIVE producer error")


def test_single_exclusive_producer_is_accepted():
    log = []
    module = OwnershipModule("producer", (output("field:shared.value"),), log)

    engine(module).run(WorldState())

    assert log == ["producer"]


def test_refines_requires_parent_from_another_module_in_same_run():
    refiner = OwnershipModule(
        "refiner",
        (output("field:fine.value", OutputPolicy.REFINES, refines="field:coarse.value"),),
    )
    try:
        engine(refiner).run(WorldState())
    except ValueError as exc:
        assert "field:fine.value" in str(exc)
        assert "field:coarse.value" in str(exc)
    else:
        raise AssertionError("Expected missing REFINES parent error")

    self_refiner = OwnershipModule(
        "refiner",
        (output("field:coarse.value", OutputPolicy.REFINES, refines="field:coarse.value"),),
    )
    try:
        engine(self_refiner).run(WorldState())
    except ValueError as exc:
        assert "refiner" in str(exc)
        assert "field:coarse.value" in str(exc)
    else:
        raise AssertionError("Expected self-referential REFINES error")


def test_refines_cycles_are_rejected():
    first = OwnershipModule(
        "first",
        (output("field:a.value", OutputPolicy.REFINES, refines="field:b.value"),),
    )
    second = OwnershipModule(
        "second",
        (output("field:b.value", OutputPolicy.REFINES, refines="field:a.value"),),
    )

    try:
        engine(first, second).run(WorldState())
    except ValueError as exc:
        assert "Cyclic REFINES" in str(exc)
        assert "field:a.value" in str(exc)
        assert "field:b.value" in str(exc)
    else:
        raise AssertionError("Expected REFINES cycle error")


def test_valid_refines_declaration_is_accepted_without_value_check():
    parent = OwnershipModule("parent", (output("field:coarse.value"),))
    refiner = OwnershipModule(
        "refiner",
        (output("field:fine.value", OutputPolicy.REFINES, refines="field:coarse.value"),),
    )

    engine(refiner, parent).run(WorldState())


def test_overlay_producers_require_distinct_layers_and_integer_priorities():
    first = OwnershipModule(
        "first",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="first", priority=1),),
    )
    second = OwnershipModule(
        "second",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="second", priority=2),),
    )

    engine(first, second).run(WorldState())

    duplicate_priority = OwnershipModule(
        "third",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="third", priority=1),),
    )
    try:
        engine(first, duplicate_priority).run(WorldState())
    except ValueError as exc:
        assert "priority" in str(exc)
    else:
        raise AssertionError("Expected duplicate overlay priority error")

    duplicate_layer = OwnershipModule(
        "third",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="first", priority=3),),
    )
    try:
        engine(first, duplicate_layer).run(WorldState())
    except ValueError as exc:
        assert "layer" in str(exc)
    else:
        raise AssertionError("Expected duplicate overlay layer error")

    non_integer = OwnershipModule(
        "third",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="third", priority="3"),),
    )
    try:
        engine(first, non_integer).run(WorldState())
    except ValueError as exc:
        assert "priority" in str(exc)
    else:
        raise AssertionError("Expected non-integer overlay priority error")


def test_mixed_ownership_policies_are_rejected():
    exclusive = OwnershipModule("exclusive", (output("field:shared.value"),))
    overlay = OwnershipModule(
        "overlay",
        (output("field:shared.value", OutputPolicy.OVERLAY, layer="overlay", priority=1),),
    )

    try:
        engine(exclusive, overlay).run(WorldState())
    except ValueError as exc:
        message = str(exc)
        assert "mixed ownership policies" in message
        assert "exclusive" in message
        assert "overlay" in message
    else:
        raise AssertionError("Expected mixed ownership policy error")


def test_event_outputs_are_exempt_from_ownership_collisions():
    event = OutputSpec("event:shared", DataKind.EVENT)
    first = OwnershipModule("first", (event,))
    second = OwnershipModule("second", (event,))

    engine(first, second).run(WorldState())
