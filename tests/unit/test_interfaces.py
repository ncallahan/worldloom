from worldloom import SimulationConfig, SimulationContext
from worldloom.interfaces import DataKind, InputSpec, ModuleSpec, OutputPolicy, OutputSpec
from worldloom.modules import HydrologyModule, TerrainModule


def test_context_defaults_are_deterministic():
    context = SimulationContext()
    assert context.step == 0
    assert context.time == 0.0
    assert context.seed is None
    assert context.delta == 0.0


def test_simulation_config_declares_numeric_time_unit():
    config = SimulationConfig(time_unit="days", start_time=10.0)
    assert config.time_unit == "days"
    assert config.start_time == 10.0


def test_module_spec_declares_identity_and_data_contract():
    spec = TerrainModule().spec

    assert isinstance(spec, ModuleSpec)
    assert spec.name == "prototype.terrain"
    assert spec.version == "0.1"
    assert spec.inputs == ()
    assert spec.outputs == (OutputSpec("field:terrain.elevation", DataKind.STATE),)


def test_module_spec_declares_dependencies_and_resolution():
    spec = HydrologyModule().spec

    assert spec.inputs == (InputSpec("field:terrain.elevation", DataKind.STATE),)
    assert spec.outputs == (OutputSpec("field:hydrology.water", DataKind.STATE),)
    assert spec.dependencies == ("prototype.terrain",)
    assert spec.spatial_resolution == "upstream terrain grid cells"
    assert spec.temporal_interval == 1.0
    assert spec.uncertainty == "deterministic"


def test_module_output_kind_distinguishes_state_observation_and_event():
    from worldloom.modules import SettlementResolutionModule, SettlementSuitabilityModule

    suitability = SettlementSuitabilityModule().spec.outputs[0]
    settlement, event = SettlementResolutionModule().spec.outputs

    assert suitability.kind is DataKind.OBSERVATION
    assert settlement.kind is DataKind.STATE
    assert event.kind is DataKind.EVENT


def test_module_input_kind_distinguishes_state_and_observation():
    from worldloom.modules import SettlementResolutionModule, SettlementSuitabilityModule

    suitability_inputs = SettlementSuitabilityModule().spec.inputs
    resolution_inputs = SettlementResolutionModule().spec.inputs

    assert suitability_inputs == (
        InputSpec("field:terrain.elevation", DataKind.STATE),
        InputSpec("field:hydrology.water", DataKind.STATE),
    )
    assert resolution_inputs == (
        InputSpec("observation:settlement.suitability", DataKind.OBSERVATION),
    )

def test_output_spec_ownership_defaults_are_backward_compatible():
    spec = OutputSpec("field:test.value", DataKind.STATE)

    assert spec.policy is OutputPolicy.EXCLUSIVE
    assert spec.refines is None
    assert spec.layer is None
    assert spec.priority is None

def test_output_spec_declares_provisional_refinement_and_overlay_metadata():
    refined = OutputSpec(
        "field:finer.value",
        DataKind.STATE,
        policy=OutputPolicy.REFINES,
        refines="field:coarser.value",
    )
    overlay = OutputSpec(
        "field:shared.value",
        DataKind.STATE,
        policy=OutputPolicy.OVERLAY,
        layer="resolved",
        priority=10,
    )

    assert refined.refines == "field:coarser.value"
    assert overlay.layer == "resolved"
    assert overlay.priority == 10
