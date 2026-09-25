from src.simulation import Simulation
from src.parser import Parser
from src.drone import Drone


def test_real_maps() -> None:
    """Run the simulation on all medium and hard maps."""

    maps = [
        "maps/easy/01_linear_path.txt",
        "maps/easy/02_simple_fork.txt",
        "maps/easy/03_basic_capacity.txt",
        "maps/medium/01_dead_end_trap.txt",
        "maps/medium/02_circular_loop.txt",
        "maps/medium/03_priority_puzzle.txt",
        "maps/hard/01_maze_nightmare.txt",
        "maps/hard/02_capacity_hell.txt",
        "maps/hard/03_ultimate_challenge.txt",
        "maps/challenger/01_the_impossible_dream.txt",
    ]

    for map_path in maps:
        print()
        print("=" * 60)
        print(f"TESTING: {map_path}")
        print("=" * 60)

        try:
            parser = Parser(map_path)
            network = parser.parse()

            drones = []
            start = network.get_start_zone()

            for i in range(1, network.nb_drones + 1):
                drones.append(
                    Drone(
                        f"D{i}",
                        start,
                    )
                )

            simulation = Simulation(
                network,
                drones,
            )

            simulation.run()

            print()
            print(f"PASS: {map_path}")

        except Exception as error:
            print()
            print(f"FAIL: {map_path}")
            print(f"Error: {error}")


def main() -> None:
    """Run the simulation on all provided test maps."""
    test_real_maps()


if __name__ == "__main__":
    main()
