from heapq import heappop, heappush
from src.zone import Zone
from src.network import Network
from src.connection import Connection
from src.zone import ZoneType


class PathFinder:
    """
    Find valid paths between zones.
    """

    def __init__(self, network: Network) -> None:
        """Initialize the path finder with a network."""
        self.network = network

    def dijkstra(
        self,
        start_zone: Zone,
        end_zone: Zone,
    ) -> list[Zone]:
        """Find the shortest valid path between two zones."""
        distances: dict[Zone, float] = {
            zone: float("inf") for zone in self.network.zones.values()
        }

        previous: dict[Zone, Zone | None] = {
            zone: None for zone in self.network.zones.values()
        }

        visited: set[Zone] = set()

        distances[start_zone] = 0

        while len(visited) < len(self.network.zones):
            current_zone = self._get_closest_zone(
                distances,
                visited,
            )

            if current_zone is None:
                break

            if current_zone == end_zone:
                break

            visited.add(current_zone)

            for connection in self.network.connections:
                neighbor = self._get_neighbor(
                    connection,
                    current_zone,
                )

                if neighbor is None:
                    continue

                if neighbor in visited:
                    continue

                if neighbor.is_zone_blocked():
                    continue

                new_distance = (distances[current_zone]
                                + neighbor.movement_cost())

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current_zone

        return self._build_path(
            start_zone,
            end_zone,
            previous,
        )

    def find_multiple_paths(
        self,
        start_zone: Zone,
        end_zone: Zone,
        max_paths: int = 3,
    ) -> list[list[Zone]]:
        """
        Find several different paths ordered by movement cost.

        When paths have the same cost, prefer paths that go through
        priority zones.
        """
        if max_paths <= 0:
            return []

        paths: list[list[Zone]] = []
        counter = 0
        queue: list[tuple[int, int, tuple[Zone, ...]]] = (
            [(0, counter, (start_zone,))]
            )

        while queue and len(paths) < max_paths:
            cost, _, current_path = heappop(queue)
            current_zone = current_path[-1]

            if current_zone == end_zone:
                paths.append(list(current_path))
                continue

            neighbors = self._get_neighbors(current_zone)

            neighbors.sort(
                key=lambda zone: (
                    zone.movement_cost(),
                    0 if zone.zone_type == ZoneType.priority else 1,
                )
            )

            for neighbor in neighbors:
                if neighbor in current_path:
                    continue

                if neighbor.is_zone_blocked():
                    continue

                counter += 1
                new_path = current_path + (neighbor,)
                new_cost = cost + neighbor.movement_cost()

                heappush(
                    queue,
                    (new_cost, counter, new_path),
                )

        return paths

    def _get_neighbors(
        self,
        zone: Zone,
    ) -> list[Zone]:
        """Return valid neighboring zones."""
        neighbors: list[Zone] = []

        for connection in self.network.connections:
            neighbor = self._get_neighbor(
                connection,
                zone,
            )

            if neighbor is None:
                continue

            if neighbor.is_zone_blocked():
                continue

            neighbors.append(neighbor)

        return neighbors

    def _path_cost(
        self,
        path: list[Zone],
    ) -> int:
        """Calculate the movement cost of a path."""
        return sum(zone.movement_cost() for zone in path[1:])

    def _get_closest_zone(
        self,
        distances: dict[Zone, float],
        visited: set[Zone],
    ) -> Zone | None:
        """Return the closest unvisited zone."""
        closest_zone = None
        min_distance = float("inf")

        for zone, distance in distances.items():
            if zone in visited:
                continue

            if distance < min_distance:
                min_distance = distance
                closest_zone = zone

            elif (
                distance == min_distance
                and zone.zone_type == ZoneType.priority
                and (
                    closest_zone is None or
                    closest_zone.zone_type != ZoneType.priority
                )
            ):
                closest_zone = zone

        return closest_zone

    def _get_neighbor(
        self,
        connection: Connection,
        current_zone: Zone,
    ) -> Zone | None:
        """Return the other zone connected to current_zone."""
        if connection.zone1 == current_zone:
            return connection.zone2

        if connection.zone2 == current_zone:
            return connection.zone1

        return None

    def _build_path(
        self,
        start_zone: Zone,
        end_zone: Zone,
        previous: dict[Zone, Zone | None],
    ) -> list[Zone]:
        """Build a path from the previous-zone map."""
        path: list[Zone] = []
        current_zone: Zone | None = end_zone

        while current_zone is not None:
            path.append(current_zone)

            if current_zone == start_zone:
                break

            current_zone = previous[current_zone]

        if not path or path[-1] != start_zone:
            return []

        path.reverse()

        return path
