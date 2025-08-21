from pygame import Surface
from core.ecs import Entity
from core.components.position import Position
from core.components.collider import Collider
from core.components.sprite import Sprite
from core.components.dialogue import Dialogue
from core.components.freeze import Freeze
class ProfessorNPC(Entity):
    def __init__(self, x, y, props=None):
        super().__init__()
        image=Surface((16,16))
        image.fill((0,0,255))


     
        self.add(Position(x,y),
                Collider(16,16),
                Sprite(image),
                Freeze(active=False),
                Dialogue([
                "Olá estudante!",
                "Hoje vamos falar sobre resistores.",
                "Você sabe o que é a Lei de Ohm?",
                "É uma lei muito famosa e utilizada em diversas áreas da física e da engenharia elétrica.Mas exige bastante da sua inteligencia e disposição para aprendê-la!Está disposto a adiquirir esse conhecimento ?aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            ])
                )
        self.props = props or {}
    
