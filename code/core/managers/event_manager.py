import pygame
from collections import defaultdict

class EventManager:
    _instance = None

    def __init__(self):
        self._listeners = defaultdict(list)

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = EventManager()
        return cls._instance
    def clear(self):
        print("Limpou Liteners")
        self._listeners.clear()
    def subscribe(self, event_type: str, listener: callable):
        self._listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: callable):
        if listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)

    def post(self, events):
        """
        Distribui eventos:
        - Lista de pygame.event.Event: converte em nome e notifica listeners.
        - Dict custom com 'type' chave: notifica listeners deste type.
        """
        if isinstance(events, list):
            for e in events:
                name = pygame.event.event_name(e.type)
                for listener in self._listeners.get(name, []):
                    listener(e)
        elif isinstance(events, dict) and 'type' in events:
            for listener in self._listeners.get(events['type'], []):
                listener(events)
