from worldloom.core import WorldState
from worldloom.interfaces import ModuleSpec, SimulationConfig, SimulationContext
from worldloom.simulation import SimulationEngine


class RecordingModule:
    def __init__(self, name, interval, log, dependencies=()):
        self.log = log
        self.spec = ModuleSpec(
            name=name,
            version="test",
            temporal_interval=interval,
            dependencies=dependencies,
        )

    def run(self, world, context):
        self.log.append((self.spec.name, context.time, context.delta, context.step))


def test_scheduler_runs_modules_at_declared_intervals():
    log = []
    engine = SimulationEngine(
        (
            RecordingModule("slow", 2.0, log),
            RecordingModule("fast", 1.0, log),
        ),
        SimulationConfig(time_unit="days"),
    )

    engine.run(WorldState(), until=4.0)

    assert [entry[:2] for entry in log] == [
        ("slow", 0.0),
        ("fast", 0.0),
        ("fast", 1.0),
        ("slow", 2.0),
        ("fast", 2.0),
        ("fast", 3.0),
        ("slow", 4.0),
        ("fast", 4.0),
    ]


def test_scheduler_reports_elapsed_time_since_each_module_run():
    log = []
    engine = SimulationEngine(
        (RecordingModule("module", 2.0, log),),
        SimulationConfig(time_unit="days"),
    )

    engine.run(WorldState(), until=4.0)

    assert [(time, delta) for _, time, delta, _ in log] == [
        (0.0, 0.0),
        (2.0, 2.0),
        (4.0, 2.0),
    ]


def test_scheduler_preserves_dependency_order_at_each_time():
    log = []
    engine = SimulationEngine(
        (
            RecordingModule("dependent", 1.0, log, dependencies=("source",)),
            RecordingModule("source", 1.0, log),
        ),
        SimulationConfig(time_unit="days"),
    )

    engine.run(WorldState(), until=2.0)

    assert log == [
        ("source", 0.0, 0.0, 0),
        ("dependent", 0.0, 0.0, 0),
        ("source", 1.0, 1.0, 1),
        ("dependent", 1.0, 1.0, 1),
        ("source", 2.0, 1.0, 2),
        ("dependent", 2.0, 1.0, 2),
    ]


def test_module_without_interval_runs_once_in_scheduled_run():
    log = []
    engine = SimulationEngine(
        (
            RecordingModule("static", None, log),
            RecordingModule("dynamic", 1.0, log),
        ),
        SimulationConfig(time_unit="days"),
    )

    engine.run(WorldState(), until=3.0)

    assert [name for name, *_ in log].count("static") == 1
    assert [time for name, time, *_ in log if name == "static"] == [0.0]


def test_scheduler_rejects_non_positive_intervals():
    log = []
    engine = SimulationEngine(
        (RecordingModule("invalid", 0.0, log),),
        SimulationConfig(time_unit="days"),
    )

    try:
        engine.run(WorldState(), until=1.0)
    except ValueError as exc:
        assert "temporal interval must be positive" in str(exc)
    else:
        raise AssertionError("Expected invalid temporal interval error")


def test_single_cycle_run_preserves_original_execution_mode():
    log = []
    engine = SimulationEngine(
        (RecordingModule("module", 2.0, log),),
        SimulationConfig(time_unit="days"),
    )

    engine.run(WorldState(), SimulationContext(time=5.0))

    assert log == [("module", 5.0, 0.0, 0)]
