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

    def is_zone_blocked(self) -> bool:
        """
        check if the zone is blocked and return true
        """
        return self.zone_type == ZoneType.blocked

    def movement_cost(self) -> int:
        """
        check if the zone is normal or restricted or priority and return.
        """
        if self.zone_type == ZoneType.normal:
            return 1
        elif self.zone_type == ZoneType.restricted:
            return 2
        elif self.zone_type == ZoneType.priority:
            return 1
        else:
            raise ValueError("cannot get movement cost of a blocked zone")
