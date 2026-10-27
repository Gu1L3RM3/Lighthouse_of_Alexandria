from pygame import Rect


def grid_lift_positions(released, grid_rect: Rect, blocked_rects) -> list[tuple[int, int]]:
    """Finger lifts that act on the grid: inside it and not on any UI drawn over it."""
    return [
        pos for pos in released
        if grid_rect.collidepoint(pos) and not any(rect.collidepoint(pos) for rect in blocked_rects)
    ]


def aim_position(last_touch, blocked_rects, previous):
    """Where the held part should be: the last finger, unless that finger was pressing a button over the grid."""
    if last_touch is None or any(rect.collidepoint(last_touch) for rect in blocked_rects):
        return previous
    return last_touch
