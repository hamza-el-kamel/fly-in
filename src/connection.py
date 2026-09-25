from src.zone import Zone


class Connection:
    """
    Represents a connection between two zones.
    """

    def __init__(
        self,
        zone1: Zone,
        zone2: Zone,
        count_drones: int = 0,
        max_link_capacity: int = 1,
    ) -> None:
        self.zone1 = zone1
        self.zone2 = zone2
        self.count_drones = count_drones
        self.max_link_capacity = max_link_capacity
        self.name = f"{zone1.name}-{zone2.name}"
