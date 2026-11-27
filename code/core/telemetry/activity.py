import pygame

# Stick axes are left out: analog drift would keep an absent player "active" forever.
PLAYER_INPUT_EVENTS = frozenset({
    pygame.KEYDOWN,
    pygame.KEYUP,
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP,
    pygame.MOUSEMOTION,
    pygame.MOUSEWHEEL,
    pygame.FINGERDOWN,
    pygame.FINGERUP,
    pygame.FINGERMOTION,
    pygame.JOYBUTTONDOWN,
    pygame.JOYHATMOTION,
    pygame.CONTROLLERBUTTONDOWN,
    pygame.TEXTINPUT,
})


def has_player_input(events) -> bool:
    return any(event.type in PLAYER_INPUT_EVENTS for event in events)
