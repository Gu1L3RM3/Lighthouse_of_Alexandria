from core.ecs import System
from core.components.position import Position
from core.components.collider import Collider
from core.components.team import Team
from core.components.freeze import Freeze
from core.managers.entity_manager import EntityManager
from core.managers.event_manager import EventManager
from entities.player import Player


class EnemyTouchGameOverSystem(System):
    def __init__(self):
        self.triggered = False

    def update(self, entity_mn: EntityManager, dt: float):
        _ = dt
        if self.triggered:
            return

        player: Player = entity_mn.get_player()
        if not player or not player.has(Position) or not player.has(Collider):
            return
        if player.has(Freeze) and player.get(Freeze).active:
            return

        player_pos: Position = player.get(Position)
        player_col: Collider = player.get(Collider)
        player_rect = player_col.get_rect(player_pos.x, player_pos.y).inflate(2, 2)

        for enemy in entity_mn.get_entities_with(Position, Collider, Team):
            team: Team = enemy.get(Team)
            if team.name != "enemy":
                continue

            enemy_pos: Position = enemy.get(Position)
            enemy_col: Collider = enemy.get(Collider)
            enemy_rect = enemy_col.get_rect(enemy_pos.x, enemy_pos.y)
            if not player_rect.colliderect(enemy_rect):
                continue

            self.triggered = True
            EventManager.get().post({"type": "player_touched_enemy"})
            return
