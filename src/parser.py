from src.zone import ZoneType, Zone
from src.connection import Connection
from src.network import Network


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

    def parse_zone_line(self, line: str) -> Zone:
        """
        Parse a zone line and return a Zone object.
        """
        line = line.replace("[", " ")
        line = line.replace("]", " ")
        line = line.replace("=", " ")
        parts = line.split()

        is_start = parts[0] == "start_hub:"
        is_end = parts[0] == "end_hub:"

        name = parts[1]
        x = int(parts[2])
        y = int(parts[3])
        color = "none"
        zone_type = ZoneType.normal
        max_drones = 1

        for i in range(4, len(parts), 2):
            key = parts[i]
            value = parts[i + 1]
            if key == "color":
                color = value
            elif key == "zone":
                zone_type = ZoneType[value]
            elif key == "max_drones":
                max_drones = int(value)

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
            raise ValueError("invalid connection definition")

        zone_name_1 = parts[1]
        zone_name_2 = parts[2]

        if zone_name_1 not in network.zones:
            raise ValueError(f"unknown zone '{zone_name_1}'")

        if zone_name_2 not in network.zones:
            raise ValueError(f"unknown zone '{zone_name_2}'")

        zone_1 = network.zones[zone_name_1]
        zone_2 = network.zones[zone_name_2]

        max_link_capacity = 1

        if len(parts) > 4:
            try:
                max_link_capacity = int(parts[4])
            except ValueError:
                raise ValueError("max_link_capacity must be an integer")

        return Connection(
            zone_1,
            zone_2,
            max_link_capacity=max_link_capacity,
        )

    # def parse(self) -> Network:
    #     pass


if __name__ == "__main__":
    par = Parser("./maps/easy/02_simple_fork.txt")
    lines = par.read_file()

    network = Network()

    for line_number, text in lines:
        if text.startswith("nb_drones:"):
            continue
        if text.startswith(("hub:", "start_hub:", "end_hub:")):
            zone = par.parse_zone_line(text)
            network.zone_to_network(zone)

    print("Zones added:", list(network.zones.keys()))

    for line_number, text in lines:
        if text.startswith("connection:"):
            conn = par.parse_connection_line(text, network)
            print(
                conn.zone1.name,
                "-",
                conn.zone2.name,
                "| capacity:",
                conn.max_link_capacity,
            )
