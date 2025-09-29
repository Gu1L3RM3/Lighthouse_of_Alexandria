from pygame import Surface
from core.ecs import Component
from typing import Dict, List, Callable, Optional

class AnimateSprite(Component):
    def __init__(self, animations: Dict[str, List[Surface]], fps: int = 8, loop: bool = True):
        
        self.animations = animations
        self.fps = fps
        self.loop = loop

        self.current_animation: str | None = None
        self.current_frame: int = 0
        self.time_acc: float = 0.0
        self.image: Surface | None = None
        self.done: bool = False
        self.on_finish: Optional[Callable[[], None]] = None  # callback quando terminar a animação

    def play(self, name: str, reset: bool = False, loop: bool | None = None, on_finish: Callable[[], None] | None = None):
        """
        Inicia ou troca a animação atual.
        reset=True -> reinicia do frame 0
        loop -> sobrescreve o loop padrão
        on_finish -> função chamada quando animação terminar (se loop=False)
        """
        if self.current_animation == name and not reset:
            return
        
        self.current_animation = name
        self.current_frame = 0
        self.time_acc = 0.0
        self.done = False
        self.loop = loop if loop is not None else self.loop
        self.on_finish = on_finish

        if name in self.animations:
            self.image = self.animations[name][0]

    def stop(self):
        """Para a animação atual (mantém o frame atual)."""
        self.done = True

    def is_playing(self) -> bool:
        """Retorna True se a animação ainda não terminou."""
        return not self.done
    def to_dict(self):
        pass