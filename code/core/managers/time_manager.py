import pygame

class TimeManager:
    def __init__(self):
        self.timers = {}

    def set(self, name, interval):
        self.timers[name] = pygame.time.get_ticks() + int(interval * 1000)

    def ready(self, name)->bool:
        return pygame.time.get_ticks() >= self.timers.get(name, 0)

    def reset(self, name, interval):
        self.set(name, interval)

    def clear(self, name):
        if name in self.timers:
            del self.timers[name]

    def remaining(self, name):
        return max(0, (self.timers.get(name, 0) - pygame.time.get_ticks()) / 1000)
