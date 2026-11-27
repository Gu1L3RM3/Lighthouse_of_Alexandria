import pygame
from collections import defaultdict

class EventManager:
    _instance = None

    def __init__(self):
        self._listeners = defaultdict(list)
        # Survive clear(), which runs on every scene change (e.g. telemetry observers).
        self._persistent_listeners = defaultdict(list)

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = EventManager()
        return cls._instance
    def clear(self):
        self._listeners.clear()
    def subscribe(self, event_type: str, listener: callable):
        self._listeners[event_type].append(listener)

    def unsubscribe(self, event_type: str, listener: callable):
        if listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)

    def subscribe_persistent(self, event_type: str, listener: callable):
        self._persistent_listeners[event_type].append(listener)

    def unsubscribe_persistent(self, event_type: str, listener: callable):
        if listener in self._persistent_listeners[event_type]:
            self._persistent_listeners[event_type].remove(listener)

    def _listeners_for(self, event_type: str) -> tuple:
        return tuple(self._listeners.get(event_type, ())) + tuple(self._persistent_listeners.get(event_type, ()))

    def post(self, events):
        """
        Distribui eventos:
        - Lista de pygame.event.Event: converte em nome e notifica listeners.
        - Dict custom com 'type' chave: notifica listeners deste type.
        """
        if isinstance(events, list):
            for e in events:
                name = pygame.event.event_name(e.type)
                listeners = self._listeners_for(name)
                for listener in listeners:
                    listener(e)
        elif isinstance(events, dict) and 'type' in events:
            listeners = self._listeners_for(events['type'])
            for listener in listeners:
                listener(events)
