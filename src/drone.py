from src.zone import Zone
from src.connection import Connection


class Drone:
    """
    Represent a drone moving through the network.
    """

    def __init__(
        self,
        drone_id: str,
        current_zone: Zone,
        path: list[Zone] | None = None,
        delivered: bool = False,
    ) -> None:
        """
        Initialize a drone.
        """
        self.drone_id = drone_id
        self.current_zone = current_zone
        self.path = path if path is not None else []
        self.delivered = delivered
        self.available_paths: list[list[Zone]] = []
        self.current_path_index = 0
        self.in_transit = False
        self.transit_connection: Connection | None = None
        self.transit_destination: Zone | None = None
        self.transit_turns_remaining = 0
        self.acted_this_turn = False
