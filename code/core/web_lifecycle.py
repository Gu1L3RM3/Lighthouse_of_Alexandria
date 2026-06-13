import pygame


class WebLifecycle:
    def __init__(self):
        self.is_paused = False

    def consume(self, event: pygame.event.Event) -> None:
        if event.type == pygame.WINDOWFOCUSLOST:
            self.is_paused = True
        elif event.type == pygame.WINDOWFOCUSGAINED:
            self.is_paused = False

