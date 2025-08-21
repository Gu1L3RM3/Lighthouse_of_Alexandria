import pygame

class NavDebugOverlay:
    def __init__(self, map_system):
        self.map = map_system
        self.surf = pygame.Surface((self.map.map_width, self.map.map_height), pygame.SRCALPHA)
        self.dirty = True

    def rebuild(self):
        self.surf.fill((0,0,0,0))
        tw, th = self.map.tile_width, self.map.tile_height

        # ground2 walkables
        for x in range(self.map.navgrid.width):
            for y in range(self.map.navgrid.height):
                if self.map.navgrid.walkable[x][y]:
                    pygame.draw.rect(self.surf, (0,255,0,60), (x*tw, y*th, tw, th))

        # waypoints
        for name, (tx, ty) in self.map.waypoints.items():
            cx = tx*tw + tw//2; cy = ty*th + th//2
            pygame.draw.circle(self.surf, (255,255,0,160), (cx,cy), 4)

        self.dirty = False

    def draw(self, screen, camera):
        if self.dirty:
            self.rebuild()
        view = camera.viewport  # Rect do mundo visível
        screen.blit(self.surf, (-view.left, -view.top))
