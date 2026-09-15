from enum import Enum


class ZoneType(Enum):
    """
    Represents the possible statuses of type of Zone.
    """

    normal = 1
    blocked = 2
    restricted = 3
    priority = 4


class Zone:
    """
    Represents a zone with its position, appearance, type,
    and maximum number of drones.
    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        is_start: bool,
        is_end: bool,
        count_drones: int = 0,
        color: str = "none",
        max_drones: int = 1,
        zone_type: ZoneType = ZoneType.normal,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.is_start = is_start
        self.is_end = is_end
        self.count_drones = count_drones
        self.color = color
        self.max_drones = max_drones
        self.zone_type = zone_type
        # self.connections: list["Connection"] = []
        # self.neighbors: list["neighbors"] = []
