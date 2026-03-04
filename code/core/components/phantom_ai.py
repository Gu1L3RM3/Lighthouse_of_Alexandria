from core.ecs import Component


class PhantomAI(Component):
    STATE_PATROL = "patrol"
    STATE_CHASE = "chase"
    STATE_RETURN = "return"

    def __init__(
        self,
        detection_radius: float = 90.0,
        touch_radius: float = 10.0,
        chase_speed: float = 58.0,
        patrol_speed: float = 42.0,
        route: list[tuple[int, int]] | None = None,
    ):
        self.detection_radius = detection_radius
        self.touch_radius = touch_radius
        self.chase_speed = chase_speed
        self.patrol_speed = patrol_speed
        self.route = list(route or [])
        self.state = self.STATE_PATROL
        self.was_player_in_range = False
        self.wait_for_reenter = False

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "detection_radius": self.detection_radius,
            "touch_radius": self.touch_radius,
            "chase_speed": self.chase_speed,
            "patrol_speed": self.patrol_speed,
            "route": self.route,
            "state": self.state,
        }
