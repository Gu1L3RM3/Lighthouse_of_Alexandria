def player_tile(scene) -> tuple[int | None, int | None]:
    """Tile under the player in the active level, or (None, None) outside levels."""
    try:
        from core.components.position import Position

        position = scene.player.get(Position)
        tile_map = scene.tile_map
        return int(position.x // tile_map.tile_width), int(position.y // tile_map.tile_height)
    except Exception:
        return None, None
