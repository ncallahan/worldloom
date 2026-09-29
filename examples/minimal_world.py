"""Run the smallest complete Worldloom vertical slice."""

from worldloom.core import WorldState
from worldloom.modules import (
    HydrologyModule,
    SettlementResolutionModule,
    SettlementSuitabilityModule,
    TerrainModule,
)
from worldloom.simulation import SimulationEngine


def main() -> None:
    world = WorldState()
    engine = SimulationEngine(
        (
            TerrainModule(),
            HydrologyModule(),
            SettlementSuitabilityModule(),
            SettlementResolutionModule(),
        )
    )
    engine.run(world)

    settlement = world.entities["settlement:001"]
    print("Worldloom prototype")
    print(f"settlement location: {settlement['location']}")
    print(f"population: {settlement['population']}")
    print(f"events: {len(world.events)}")


if __name__ == "__main__":
    main()
