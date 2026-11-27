import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.managers.event_manager import EventManager


class PersistentSubscriptionTest(unittest.TestCase):
    def setUp(self):
        self.events = EventManager()
        self.received = []

    def test_persistent_listener_survives_clear(self):
        self.events.subscribe_persistent("panel_solved", self.received.append)

        self.events.clear()
        self.events.post({"type": "panel_solved"})

        self.assertEqual(self.received, [{"type": "panel_solved"}])

    def test_clear_still_removes_scene_listeners(self):
        self.events.subscribe("panel_solved", self.received.append)

        self.events.clear()
        self.events.post({"type": "panel_solved"})

        self.assertEqual(self.received, [])

    def test_persistent_and_scene_listeners_both_receive_the_event(self):
        scene_received = []
        self.events.subscribe("get_key", scene_received.append)
        self.events.subscribe_persistent("get_key", self.received.append)

        self.events.post({"type": "get_key"})

        self.assertEqual((len(scene_received), len(self.received)), (1, 1))

    def test_unsubscribe_persistent_stops_delivery(self):
        self.events.subscribe_persistent("get_key", self.received.append)

        self.events.unsubscribe_persistent("get_key", self.received.append)
        self.events.post({"type": "get_key"})

        self.assertEqual(self.received, [])


if __name__ == "__main__":
    unittest.main()
