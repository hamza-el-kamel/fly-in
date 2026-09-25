from src.zone import Zone
from src.connection import Connection


class Network:
    """
    Represent the drone network and its connected zones.
    """

    def __init__(self, nb_drones: int = 0) -> None:
        """
        Initialize a network with zones, connections, and drones.
        """
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.nb_drones = nb_drones
        self.start_hub: Zone | None = None
        self.end_hub: Zone | None = None
        self.graph: dict[str, list[str]] = {}

    def get_start_zone(self) -> Zone:
        """
        Return the starting zone of the network.
        """
        if self.start_hub is None:
            raise ValueError("Start zone has not been defined")
        return self.start_hub

    def get_end_zone(self) -> Zone:
        """
        Return the ending zone of the network.
        """
        if self.end_hub is None:
            raise ValueError("end zone has not been defined")
        return self.end_hub

    def zone_to_network(self, zone: Zone) -> None:
        """
        Add a zone to the network graph.
        """
        if zone.name in self.zones:
            raise ValueError(f"duplicate zone name '{zone.name}'")
        self.graph[zone.name] = []
        self.zones[zone.name] = zone
        if zone.is_start:
            self.start_hub = zone
        if zone.is_end:
            self.end_hub = zone

    def connection_to_network(self, connection: Connection) -> None:
        """Add a connection to the network."""

        zone1 = connection.zone1
        zone2 = connection.zone2

        if zone1.name not in self.graph:
            self.zone_to_network(zone1)

        if zone2.name not in self.graph:
            self.zone_to_network(zone2)

        if zone2.name in self.graph[zone1.name]:
            raise ValueError(
                f"duplicate connection '{zone1.name}-{zone2.name}'"
                )

        self.graph[zone1.name].append(zone2.name)
        self.graph[zone2.name].append(zone1.name)

        self.connections.append(connection)

    def get_neighbors(self, zone_node: Zone) -> list[str]:
        """
        Return the neighbors zones of a given zone.
        """
        return self.graph[zone_node.name]
