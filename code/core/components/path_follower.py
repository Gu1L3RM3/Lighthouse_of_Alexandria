from core.ecs import Component

class PathFollower(Component):
    """
    Segue um caminho (lista de tiles) em velocidade constante.
    O caminho é em coordenadas de TILE (tx, ty). O sistema converte para pixel.
    """
    def __init__(self, path: list[tuple[int, int]], speed: float = 40):
        self.path_tiles = path or []
        self.current_index = 0
        self.speed = speed  
        self.done = len(self.path_tiles) == 0
