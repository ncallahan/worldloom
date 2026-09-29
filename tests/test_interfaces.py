from worldloom import SimulationContext


def test_context_defaults_are_deterministic():
    context = SimulationContext()
    assert context.step == 0
    assert context.time == 0.0
    assert context.seed is None
