class SpatialHash:
    def __init__(self, cell_size=64):
        self.cell_size = cell_size
        self.cells = {}

    def _cell_id(self, x, y):
        cid = (x // self.cell_size, y // self.cell_size)
        return cid

    def clear(self):
        self.cells.clear()

    def insert(self, entity, rect):
        cid = self._cell_id(rect.centerx, rect.centery)
        if cid not in self.cells:
            self.cells[cid] = []
        self.cells[cid].append((entity, rect))

    def query(self, rect):
        cx, cy = self._cell_id(rect.centerx, rect.centery)
        found = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                cell = self.cells.get((cx + dx, cy + dy))
                if cell:
                    found.extend(cell)
        return found
