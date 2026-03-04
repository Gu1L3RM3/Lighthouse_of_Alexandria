from pygame import Rect

from core.components.area_trigger import AreaTrigger
from core.components.position import Position
from core.components.sprite import Sprite
from core.components.always_on_top import AlwaysOnTop
from core.components.light_component import LightComponent
from core.managers.event_manager import EventManager
from core.managers.resource_manager import ResourceManager
from entities.itens.item import Item
from entities.player import Player


class AntiReaggroFlaskItem(Item):
    def __init__(self, x, y, active, props):
        super().__init__(x, y, active, props)
        self.em = EventManager.get()
        self.sprite = ResourceManager.get().load_image(
            "2D Pixel Dungeon Asset Pack v2.0/2D Pixel Dungeon Asset Pack/items and trap_animation/flasks/flasks_1_1.png"
        )
        self.area_trigger = Rect(0, 0, 16, 16)

        self.add(
            Position(x, y),
            AreaTrigger(self.area_trigger, active=active, on_entered=self.on_collect),
            Sprite(self.sprite),
            AlwaysOnTop(),
            LightComponent(radius=12),
        )

    def on_collect(self, entity):
        if not isinstance(entity, Player):
            return
        self.em.post({"type": "cancel_reaggro_after_invisibility"})
        self.em.post({"type": "kill_entity", "id": self.id})
