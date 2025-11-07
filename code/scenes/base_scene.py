from pygame import Event , Surface
from abc import ABC, abstractmethod
from core.managers.resource_manager import ResourceManager
from core.managers.event_manager import EventManager
from core.managers.entity_manager import EntityManager
from core.managers.time_manager import TimeManager
from core.managers.ui_manager import UIManager
from core.managers.day_night_manager import DayNightManager
from core.systems.physics_system import PhysicsSystem
from core.systems.dialogue_system import DialogueSystem
from core.systems.path_following_system import PathFollowingSystem
from core.systems.weapon_system import WeaponSystem
from core.systems.render_system import RenderSystem
from core.ecs import System
from core.camera import Camera

class BaseScene(ABC):
    def __init__(self,screen:Surface,world_width:int,world_height:int):
        self.screen=screen

        self.systems:set[System]=set()
        
        self.camera=Camera(
            self.screen,
            world_width,
            world_height
            )
        self.resources     = ResourceManager.get()
        self.event_manager = EventManager.get()
        self.entity_mn     = EntityManager()
        self.time_manager  = TimeManager()
        self.dn_manager    = DayNightManager(screen)
        self.ui_manager    = UIManager()
        self.time_manager  = TimeManager()

        self.render_system         = RenderSystem(self.screen,self.camera,self.entity_mn)
        self.physics_system        = PhysicsSystem()
        self.dialog_system         = DialogueSystem(self.ui_manager)
        self.path_following_system = PathFollowingSystem()
        


    
    def update_systems(self,dt):
        if not self.systems:
            return
        
        for sys in self.systems:
            sys.update(self.entity_mn,dt)



        

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
