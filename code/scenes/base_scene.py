from pygame import Event , Surface
from abc import ABC, abstractmethod
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from core.ecs import Entity

from core.camera import Camera
class BaseScene(ABC):
   

    def __init__(self,screen:Surface,world_width:int,world_height:int):
        self.screen=screen

        self.camera=Camera(
            self.screen,
            world_width,
            world_height
            )
        self.resources = ResourceManager.get()
        self.event_manager:EventManager= EventManager.get()
        self.entities:list[Entity]
        

    @abstractmethod
    def process_input(self, events: list[Event]) -> None:
        """
        Recebe a lista de eventos do Pygame.
        Deve processar entradas de teclado, mouse, etc.
        """
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Atualiza a lógica da cena.
        dt é o delta time em segundos desde a última chamada.
        """
        pass

    @abstractmethod
    def render(self) -> None:
        """
        Desenha tudo que pertence à cena na superfície `screen`.
        """
        pass

    def start(self) -> None:
        """
        Chamado pelo SceneManager imediatamente após a cena se tornar ativa.
        Útil para inicializar ou resetar variáveis.
        """
        pass

    def end(self) -> None:
        """
        Chamado pelo SceneManager imediatamente antes de trocar para outra cena.
        Útil para limpeza ou salvar estado.
        """
        pass
