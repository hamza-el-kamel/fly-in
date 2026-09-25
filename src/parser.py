from src.zone import ZoneType, Zone
from src.connection import Connection
from src.network import Network
from src.pathfinding import PathFinder


class Parser:
    """
    Read and clean map data from a file.
    """

    def __init__(self, path: str) -> None:
        """
        Initialize the parser with the file path.
        """
        self.path = path

    def read_file(self) -> list[tuple[int, str]]:
        """
        Read the file and return non-empty, non-comment lines.
        """
        lines: list[tuple[int, str]] = []

        with open(self.path, "r") as file:
            for i, line in enumerate(file, start=1):
                line = line.strip()

                if line.startswith("#"):
                    continue

                if not line:
                    continue

                lines.append((i, line))

        return lines

    def parse_zone_line(
        self,
        line: str,
        line_number: int,
    ) -> Zone:
        """
        Parse a zone line and return a Zone object.
        """
        line = line.replace("[", " ")
        line = line.replace("]", " ")
        line = line.replace("=", " ")

        parts = line.split()

        if len(parts) < 4:
            raise ValueError(f"Line {line_number}: invalid zone definition")

        is_start = parts[0] == "start_hub:"
        is_end = parts[0] == "end_hub:"

        name = parts[1]

        if "-" in name or " " in name:
            raise ValueError(f"Line {line_number}: invalid zone name '{name}'")

        try:
            x = int(parts[2])
            y = int(parts[3])
        except ValueError:
            raise ValueError(
                f"Line {line_number}: coordinates must be integers"
                )

        color = "none"
        zone_type = ZoneType.normal
        max_drones = 1

        for i in range(4, len(parts), 2):
            if i + 1 >= len(parts):
                raise ValueError(f"Line {line_number}: invalid zone attribute")

            key = parts[i]
            value = parts[i + 1]

            if key == "color":
                color = value

            elif key == "zone":
                try:
                    zone_type = ZoneType[value]
                except KeyError:
                    raise ValueError(
                        f"Line {line_number}: " f"invalid zone type '{value}'"
                    )

            elif key == "max_drones":
                try:
                    max_drones = int(value)
                except ValueError:
                    raise ValueError(
                        f"Line {line_number}: max_drones must be an integer"
                    )

                if not is_start and not is_end and max_drones <= 0:
                    raise ValueError(
                        f"Line {line_number}: "
                        f"max_drones must be greater than 0"
                    )

            else:
                raise ValueError(
                    f"Line {line_number}: " f"unknown zone attribute '{key}'"
                )

        return Zone(
            name,
            x,
            y,
            is_start,
            is_end,
            color=color,
            max_drones=max_drones,
            zone_type=zone_type,
        )

    def parse_connection_line(
        self,
        line: str,
        line_number: int,
        network: Network,
    ) -> Connection:
        """
        Parse a connection line and return a Connection object.
        """
        line = line.replace("[", " ")
        line = line.replace("]", " ")
        line = line.replace("=", " ")
        line = line.replace("-", " ")

        parts = line.split()

        if len(parts) < 3:
            raise ValueError(
                f"Line {line_number}: invalid connection definition"
                )

        zone_name_1 = parts[1]
        zone_name_2 = parts[2]

        if zone_name_1 not in network.zones:
            raise ValueError(
                f"Line {line_number}: " f"unknown zone '{zone_name_1}'"
                )

        if zone_name_2 not in network.zones:
            raise ValueError(
                f"Line {line_number}: " f"unknown zone '{zone_name_2}'"
                )

        zone_1 = network.zones[zone_name_1]
        zone_2 = network.zones[zone_name_2]

        max_link_capacity = 1

        if len(parts) > 4:
            try:
                max_link_capacity = int(parts[4])
            except ValueError:
                raise ValueError(
                    f"Line {line_number}: max_link_capacity must be an integer"
                )

            if max_link_capacity <= 0:
                raise ValueError(
                    f"Line {line_number}: "
                    f"max_link_capacity must be greater than 0"
                )

        return Connection(
            zone_1,
            zone_2,
            max_link_capacity=max_link_capacity,
        )

    def validate(self, network: Network) -> None:
        """
        Validate the complete network.
        """
        start = 0
        end = 0

        for zone in network.zones.values():
            if zone.is_start:
                start += 1

            if zone.is_end:
                end += 1

        if start != 1:
            raise ValueError(f"Expected exactly 1 start zone, found {start}")

        if end != 1:
            raise ValueError(f"Expected exactly 1 end zone, found {end}")

    def parse(self) -> Network:
        """
        Parse the complete map and return the network.
        """
        lines = self.read_file()
        network = Network()

        nb_drones_count = 0

        for line_number, text in lines:
            if text.startswith("nb_drones:"):
                nb_drones_count += 1

                if nb_drones_count > 1:
                    raise ValueError(
                        f"Line {line_number}: duplicate nb_drones definition"
                    )

                parts = text.split()

                if len(parts) != 2:
                    raise ValueError(
                        f"Line {line_number}: invalid nb_drones definition"
                    )

                try:
                    nb_drones = int(parts[1])
                except ValueError:
                    raise ValueError(
                        f"Line {line_number}: nb_drones must be an integer"
                    )

                if nb_drones <= 0:
                    raise ValueError(
                        f"Line {line_number}: nb_drones must be greater than 0"
                    )

                network.nb_drones = nb_drones

        if nb_drones_count == 0:
            raise ValueError("missing required nb_drones definition")

        for line_number, text in lines:
            if text.startswith(("hub:", "start_hub:", "end_hub:")):
                zone = self.parse_zone_line(
                    text,
                    line_number,
                )
                network.zone_to_network(zone)

        for line_number, text in lines:
            if text.startswith("connection:"):
                connection = self.parse_connection_line(
                    text,
                    line_number,
                    network,
                )
                network.connection_to_network(connection)

        self.validate(network)
        path_finder = PathFinder(network)

        start = network.get_start_zone()
        end = network.get_end_zone()

        if not path_finder.dijkstra(start, end):
            raise ValueError(
                "no valid path exists from start to end"
            )
        return network
