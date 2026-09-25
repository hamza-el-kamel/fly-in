from src.connection import Connection
from src.drone import Drone
from src.network import Network
from src.pathfinding import PathFinder
from src.zone import Zone, ZoneType


class Simulation:
    """
    Simulate multiple drones moving through the network.
    """

    ANSI_COLORS = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "black": "\033[30m",
        "none": "",
    }

    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(
        self,
        network: Network,
        drones: list[Drone],
        max_paths_per_drone: int = 10,
    ) -> None:
        """Initialize the simulation."""
        self.network = network
        self.drones = drones
        self.turn = 0
        self.max_paths_per_drone = max_paths_per_drone

        self.reserved_zone_counts: dict[Zone, int] = {}

        self.path_finder = PathFinder(network)

        self._initialize_zone_counts()
        self._initialize_drone_paths()

    def _initialize_zone_counts(self) -> None:
        """Set the number of drones currently in each zone."""
        for zone in self.network.zones.values():
            zone.count_drones = 0

        for drone in self.drones:
            drone.current_zone.count_drones += 1

    def _initialize_drone_paths(self) -> None:
        """Give drones multiple possible paths."""
        start_zone = self.network.get_start_zone()
        end_zone = self.network.get_end_zone()

        paths = self.path_finder.find_multiple_paths(
            start_zone,
            end_zone,
            self.max_paths_per_drone,
        )

        for drone in self.drones:
            if not drone.available_paths:
                drone.available_paths = [path.copy() for path in paths]

            if not drone.path and drone.available_paths:
                drone.path = drone.available_paths[0].copy()

    def run(
        self,
        max_turns: int = 10000,
    ) -> None:
        """
        Run the simulation and display each turn.
        """
        self._print_header()

        while not self._all_drones_delivered():
            self.turn += 1

            if self.turn > max_turns:
                raise RuntimeError(
                    f"Simulation did not finish after "
                    f"{max_turns} turns. "
                    "At least one drone may be permanently stuck."
                )

            for drone in self.drones:
                drone.acted_this_turn = False

            movements = self._process_transit_drones()

            if self._all_drones_delivered():
                self._print_state()

                if movements:
                    print(" ".join(movements))

                break

            moves = self._calculate_moves()

            normal_movements = self._apply_moves(moves)

            movements.extend(normal_movements)

            self._print_state()

            if movements:
                print(" ".join(movements))

            if self._all_drones_delivered():
                print()
                print(f"TOTAL TURNS: {self.turn}")

    def _print_header(self) -> None:
        """Print the simulation header."""
        print()
        print(
            f"{self.BOLD}" "========== DRONE SIMULATION =========="
            f"{self.RESET}"
            )

    def _print_state(self) -> None:
        """Display the current simulation state."""
        print()

        print(f"{self.BOLD}" f"--- Turn {self.turn} ---" f"{self.RESET}")

        self._print_zones()
        self._print_drones()

    def _print_zones(self) -> None:
        """Display zones that currently contain drones."""
        print("Zones:")

        has_drones = False

        for zone in self.network.zones.values():
            if zone.count_drones <= 0:
                continue

            has_drones = True

            color = self._get_zone_color(zone)

            print(
                f"  {color}"
                f"{zone.name}"
                f"{self.RESET}"
                f" ({zone.count_drones} drone(s))"
            )

        if not has_drones:
            print("  No drones in zones.")

    def _print_drones(self) -> None:
        """Display the current position of every drone."""
        print("Drones:")

        end_zone = self.network.get_end_zone()
        end_color = self._get_zone_color(end_zone)

        for drone in self.drones:
            if drone.delivered:
                print(
                    f"  {drone.drone_id}: " f"{end_color}"
                    f"DELIVERED" f"{self.RESET}"
                )
                continue

            if drone.in_transit:
                connection = drone.transit_connection

                if connection is not None:
                    print(
                        f"  {drone.drone_id}: "
                        f"{self.BOLD}"
                        f"IN TRANSIT"
                        f"{self.RESET} "
                        f"({connection.name})"
                    )
                continue

            zone = drone.current_zone
            color = self._get_zone_color(zone)

            print(
                f"  {drone.drone_id}: " f"{color}"
                f"{zone.name}" f"{self.RESET}"
                )

    def _get_zone_color(self, zone: Zone) -> str:
        """
        Return the ANSI color associated with a zone.
        """
        return self.ANSI_COLORS.get(
            zone.color.lower(),
            "",
        )

    def _all_drones_delivered(self) -> bool:
        """Return True when every drone reached the goal."""
        return all(drone.delivered for drone in self.drones)

    def _process_transit_drones(self) -> list[str]:
        """
        Complete restricted-zone movements.

        Return movements that happened this turn.
        """
        movements: list[str] = []

        for drone in self.drones:
            if not drone.in_transit:
                continue

            destination = drone.transit_destination
            connection = drone.transit_connection

            if destination is None or connection is None:
                continue

            drone.transit_turns_remaining -= 1

            if drone.transit_turns_remaining > 0:
                continue

            reserved = self.reserved_zone_counts.get(
                destination,
                0,
            )

            if reserved > 0:
                self.reserved_zone_counts[destination] -= 1

                if self.reserved_zone_counts[destination] == 0:
                    del self.reserved_zone_counts[destination]

            destination.count_drones += 1
            drone.current_zone = destination

            drone.in_transit = False
            drone.transit_connection = None
            drone.transit_destination = None
            drone.transit_turns_remaining = 0

            connection.count_drones -= 1

            drone.acted_this_turn = True

            if destination.is_end:
                drone.delivered = True

            movements.append(f"{drone.drone_id}-{destination.name}")

        return movements

    def _calculate_moves(
        self,
    ) -> list[tuple[Drone, Zone, Connection]]:
        """Calculate valid moves for the current turn."""
        moves: list[tuple[Drone, Zone, Connection]] = []

        leaving_counts: dict[Zone, int] = {}
        entering_counts: dict[Zone, int] = {}
        connection_counts: dict[Connection, int] = {}

        for drone in self._get_ordered_drones():
            if drone.delivered or drone.in_transit or drone.acted_this_turn:
                continue

            self._select_best_available_path(drone)

            next_zone = self._get_next_zone(drone)

            if next_zone is None:
                continue

            connection = self._get_connection(
                drone.current_zone,
                next_zone,
            )

            if connection is None:
                continue

            if self._can_move_to(
                next_zone,
                connection,
                leaving_counts,
                entering_counts,
                connection_counts,
            ):
                moves.append(
                    (
                        drone,
                        next_zone,
                        connection,
                    )
                )

                self._reserve_move(
                    drone,
                    next_zone,
                    connection,
                    leaving_counts,
                    entering_counts,
                    connection_counts,
                )

                continue

            alternative = self._try_alternative_path(
                drone,
                leaving_counts,
                entering_counts,
                connection_counts,
            )

            if alternative is None:
                continue

            next_zone, connection = alternative

            moves.append(
                (
                    drone,
                    next_zone,
                    connection,
                )
            )

            self._reserve_move(
                drone,
                next_zone,
                connection,
                leaving_counts,
                entering_counts,
                connection_counts,
            )

        return moves

    def _can_move_to(
        self,
        next_zone: Zone,
        connection: Connection,
        leaving_counts: dict[Zone, int],
        entering_counts: dict[Zone, int],
        connection_counts: dict[Connection, int],
    ) -> bool:
        """Check whether a move is possible."""
        if next_zone.is_zone_blocked():
            return False

        if not self._has_zone_capacity(
            next_zone,
            leaving_counts,
            entering_counts,
        ):
            return False

        if not self._has_connection_capacity(
            connection,
            connection_counts,
        ):
            return False

        return True

    def _reserve_move(
        self,
        drone: Drone,
        next_zone: Zone,
        connection: Connection,
        leaving_counts: dict[Zone, int],
        entering_counts: dict[Zone, int],
        connection_counts: dict[Connection, int],
    ) -> None:
        """Reserve a move during move calculation."""
        current_zone = drone.current_zone

        leaving_counts[current_zone] = leaving_counts.get(current_zone, 0) + 1

        entering_counts[next_zone] = entering_counts.get(next_zone, 0) + 1

        connection_counts[connection] = (
            connection_counts.get(connection, 0) + 1
            )

    def _get_ordered_drones(self) -> list[Drone]:
        """Order drones by remaining path length."""

        def priority(
            drone: Drone,
        ) -> tuple[int, int]:
            remaining = self._remaining_path_length(drone)
            return remaining, int(drone.drone_id[1:])

        return sorted(
            self.drones,
            key=priority,
        )

    def _remaining_path_length(
        self,
        drone: Drone,
    ) -> int:
        """Return the remaining travel cost of the current path."""
        if not drone.path:
            return 999999

        try:
            current_index = drone.path.index(drone.current_zone)
        except ValueError:
            return 999999

        remaining_cost = 0

        for zone in drone.path[current_index + 1:]:
            remaining_cost += zone.movement_cost()

        return remaining_cost

    def _select_best_available_path(
        self,
        drone: Drone,
    ) -> None:
        """Select the best path considering congestion."""
        if not drone.available_paths:
            return

        candidates: list[tuple[int, int, int, list[Zone]]] = []

        for index, path in enumerate(drone.available_paths):
            try:
                current_index = path.index(drone.current_zone)
            except ValueError:
                continue

            remaining = sum(
                zone.movement_cost() for zone in path[current_index + 1:]
                )

            congestion = self._path_congestion(
                path,
                current_index,
            )

            candidates.append(
                (
                    remaining,
                    congestion,
                    index,
                    path,
                )
            )

        if not candidates:
            return

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            )
        )

        _, _, index, selected_path = candidates[0]

        drone.current_path_index = index
        drone.path = selected_path.copy()

    def _path_congestion(
        self,
        path: list[Zone],
        current_index: int,
    ) -> int:
        """Calculate congestion on a path."""
        congestion = 0

        for zone in path[current_index + 1:]:
            if zone.is_start or zone.is_end:
                continue

            congestion += zone.count_drones

            congestion += self.reserved_zone_counts.get(
                zone,
                0,
            )

        return congestion

    def _try_alternative_path(
        self,
        drone: Drone,
        leaving_counts: dict[Zone, int],
        entering_counts: dict[Zone, int],
        connection_counts: dict[Connection, int],
    ) -> tuple[Zone, Connection] | None:
        """Find an alternative path whose next move is possible."""
        candidates: list[
            tuple[
                int,
                int,
                int,
                list[Zone],
                Zone,
                Connection,
            ]
        ] = []

        for index, path in enumerate(drone.available_paths):
            if path == drone.path:
                continue

            try:
                current_index = path.index(drone.current_zone)
            except ValueError:
                continue

            if current_index + 1 >= len(path):
                continue

            next_zone = path[current_index + 1]

            if next_zone.is_zone_blocked():
                continue

            connection = self._get_connection(
                drone.current_zone,
                next_zone,
            )

            if connection is None:
                continue

            if not self._can_move_to(
                next_zone,
                connection,
                leaving_counts,
                entering_counts,
                connection_counts,
            ):
                continue

            remaining = sum(
                zone.movement_cost() for zone in path[current_index + 1:]
                )

            congestion = self._path_congestion(
                path,
                current_index,
            )

            candidates.append(
                (
                    remaining,
                    congestion,
                    index,
                    path,
                    next_zone,
                    connection,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            )
        )

        (
            _,
            _,
            path_index,
            selected_path,
            next_zone,
            connection,
        ) = candidates[0]

        drone.current_path_index = path_index
        drone.path = selected_path.copy()

        return next_zone, connection

    def _get_next_zone(
        self,
        drone: Drone,
    ) -> Zone | None:
        """Return the next zone in the drone's path."""
        try:
            current_index = drone.path.index(drone.current_zone)
        except ValueError:
            return None

        next_index = current_index + 1

        if next_index >= len(drone.path):
            return None

        return drone.path[next_index]

    def _get_connection(
        self,
        zone1: Zone,
        zone2: Zone,
    ) -> Connection | None:
        """Return the connection between two zones."""
        for connection in self.network.connections:
            if connection.zone1 == zone1 and connection.zone2 == zone2:
                return connection

            if connection.zone1 == zone2 and connection.zone2 == zone1:
                return connection

        return None

    def _has_zone_capacity(
        self,
        zone: Zone,
        leaving_counts: dict[Zone, int],
        entering_counts: dict[Zone, int],
    ) -> bool:
        """Check whether a zone has available capacity."""
        if zone.is_start or zone.is_end:
            return True

        drones_leaving = leaving_counts.get(zone, 0)
        drones_entering = entering_counts.get(zone, 0)

        drones_reserved = self.reserved_zone_counts.get(
            zone,
            0,
        )

        available_capacity = (
            zone.max_drones
            - zone.count_drones
            - drones_reserved
            + drones_leaving
            - drones_entering
        )

        return available_capacity > 0

    def _has_connection_capacity(
        self,
        connection: Connection,
        connection_counts: dict[Connection, int],
    ) -> bool:
        """Check whether a connection has free capacity."""
        used_this_turn = connection_counts.get(
            connection,
            0,
        )

        return (connection.count_drones + used_this_turn
                < connection.max_link_capacity)

    def _apply_moves(
        self,
        moves: list[tuple[Drone, Zone, Connection]],
    ) -> list[str]:
        """Apply calculated moves."""
        movements: list[str] = []

        for drone, next_zone, connection in moves:
            if next_zone.zone_type == ZoneType.restricted:
                self._start_restricted_move(
                    drone,
                    next_zone,
                    connection,
                )

                movements.append(f"{drone.drone_id}-" f"{connection.name}")

                continue

            current_zone = drone.current_zone

            current_zone.count_drones -= 1
            next_zone.count_drones += 1

            drone.current_zone = next_zone
            drone.acted_this_turn = True

            if next_zone.is_end:
                drone.delivered = True

            movements.append(f"{drone.drone_id}-{next_zone.name}")

        self._refresh_connection_counts()
        self._check_zone_capacities()

        return movements

    def _start_restricted_move(
        self,
        drone: Drone,
        destination: Zone,
        connection: Connection,
    ) -> None:
        """Start a two-turn restricted movement."""
        current_zone = drone.current_zone

        current_zone.count_drones -= 1

        drone.in_transit = True
        drone.transit_connection = connection
        drone.transit_destination = destination
        drone.transit_turns_remaining = 1
        drone.acted_this_turn = True

        self.reserved_zone_counts[destination] = (
            self.reserved_zone_counts.get(
                destination,
                0,
            )
            + 1
        )

        connection.count_drones += 1

    def _refresh_connection_counts(self) -> None:
        """Keep restricted transit on connections."""
        for connection in self.network.connections:
            restricted_usage = 0

            for drone in self.drones:
                if drone.in_transit and drone.transit_connection == connection:
                    restricted_usage += 1

            connection.count_drones = restricted_usage

    def _check_zone_capacities(self) -> None:
        """Verify that no zone exceeds its capacity."""
        for zone in self.network.zones.values():
            if zone.is_start or zone.is_end:
                continue

            if zone.count_drones > zone.max_drones:
                raise RuntimeError(
                    f"Zone capacity exceeded: "
                    f"{zone.name} has "
                    f"{zone.count_drones}/"
                    f"{zone.max_drones} drones."
                )

            if zone.count_drones < 0:
                raise RuntimeError(
                    f"Invalid negative drone count "
                    f"in zone {zone.name}: "
                    f"{zone.count_drones}"
                )
