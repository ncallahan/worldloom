from worldloom import SimulationContext


def test_context_defaults_are_deterministic():
    context = SimulationContext()
    assert context.step == 0
    assert context.time == 0.0
    assert context.seed is None


from worldloom.interfaces import ModuleSpec, OutputKind, OutputSpec
from worldloom.modules import HydrologyModule, TerrainModule


def test_module_spec_declares_identity_and_data_contract():
    spec = TerrainModule().spec

    assert isinstance(spec, ModuleSpec)
    assert spec.name == "prototype.terrain"
    assert spec.version == "0.1"
    assert spec.inputs == ()
    assert spec.outputs == (OutputSpec("field:terrain.elevation", OutputKind.STATE),)


def test_module_spec_declares_dependencies_and_resolution():
    spec = HydrologyModule().spec

    assert spec.inputs == ("field:terrain.elevation",)
    assert spec.outputs == (OutputSpec("field:hydrology.water", OutputKind.STATE),)
    assert spec.dependencies == ("prototype.terrain",)
    assert spec.spatial_resolution == "10x10 cells"
    assert spec.temporal_resolution == "per simulation step"
    assert spec.uncertainty == "deterministic"


def test_module_output_kind_distinguishes_state_observation_and_event():
    from worldloom.modules import SettlementResolutionModule, SettlementSuitabilityModule

    suitability = SettlementSuitabilityModule().spec.outputs[0]
    settlement, event = SettlementResolutionModule().spec.outputs

    assert suitability.kind is OutputKind.OBSERVATION
    assert settlement.kind is OutputKind.STATE
    assert event.kind is OutputKind.EVENT
