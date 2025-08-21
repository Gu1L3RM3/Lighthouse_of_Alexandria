import heapq

class NavGrid:
    """
    Grid de navegação derivado da layer 'ground2' (somente ela é caminhável).
    """
    def __init__(self, tmx_data, tile_width: int, tile_height: int, walk_layer_name="ground2"):
        self.tile_width  = tile_width
        self.tile_height = tile_height
        self.width  = tmx_data.width
        self.height = tmx_data.height

        self.walkable = [[False for _ in range(self.height)] for _ in range(self.width)]

        # Marca tiles da ground2 como caminháveis
        for layer in tmx_data.layers:
            if hasattr(layer, "name") and isinstance(getattr(layer, "name", ""), str):
                if layer.name.lower() == walk_layer_name:
                    for x, y, gid in layer:
                        if isinstance(gid, int) and gid != 0:
                            self.walkable[x][y] = True

    def is_walkable(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height and self.walkable[tx][ty]

    def pixel_center(self, tx: int, ty: int) -> tuple[int, int]:
        px = tx * self.tile_width  + self.tile_width  // 2
        py = ty * self.tile_height + self.tile_height // 2
        return px, py


class Pathfinder:
    """A* 4-direções sobre o NavGrid."""
    def __init__(self, navgrid: NavGrid):
        self.g = navgrid

    def _h(self, a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])
    def _smooth_path(self, path: list) -> list:
        """Remove nós intermediários desnecessários de um caminho."""
        if not path or len(path) < 3:
            return path

        smoothed_path = [path[0]]
        current_idx = 0

        while current_idx < len(path) - 1:
            lookahead_idx = current_idx + 2
            while lookahead_idx < len(path):
                # Verifica se há uma linha de visão direta do nó atual para o nó lookahead
                if not self._has_line_of_sight(path[current_idx], path[lookahead_idx]):
                    # Não há linha de visão, então o nó anterior era o mais longe que podíamos ir
                    break
                lookahead_idx += 1
            
            # Adiciona o último nó visível e continua a partir dele
            current_idx = lookahead_idx - 1
            smoothed_path.append(path[current_idx])

        return smoothed_path

    def _has_line_of_sight(self, start_tile, end_tile) -> bool:
        """Verifica se há um caminho reto e andável entre dois tiles (algoritmo de Bresenham)."""
        x0, y0 = start_tile
        x1, y1 = end_tile
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            if not self.g.is_walkable(x0, y0):
                return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return True
    def find_path(self, start: tuple[int,int], goal: tuple[int,int]) -> list[tuple[int,int]] | None:
        if not self.g.is_walkable(*goal) or not self.g.is_walkable(*start):
            return None

        frontier = []
        heapq.heappush(frontier, (0, start))
        came = {start: None}
        cost = {start: 0}

        while frontier:
            _, cur = heapq.heappop(frontier)
            if cur == goal:
                break

            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx = cur[0]+dx; ny = cur[1]+dy
                if not self.g.is_walkable(nx, ny):
                    continue
                new_cost = cost[cur] + 1
                nxt = (nx, ny)
                if nxt not in cost or new_cost < cost[nxt]:
                    cost[nxt] = new_cost
                    priority = new_cost + self._h(nxt, goal)
                    heapq.heappush(frontier, (priority, nxt))
                    came[nxt] = cur

        if goal not in came:
            return None

        # reconstrói
        path = []
        p = goal
        while p is not None:
            path.append(p)
            p = came[p]
        path.reverse()
        return self._smooth_path(path)
    
