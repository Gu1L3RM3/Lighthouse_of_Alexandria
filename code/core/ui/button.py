from pygame import Surface

class Button:
    def __init__(self,
                 action:callable|None,
                 image:Surface,
                 image_pressed:Surface|None,
                 pos:tuple[int,int],
                 offset_rect:tuple[int,int]=(0,0),
                 show_rect:bool=False
                 ):
        self.action=action
        self.image=image
        self.image_pressed=image_pressed
        self.pos=pos
        self.offset_rect=offset_rect
        self.show_rect=show_rect
    def draw(self):
        pass
    def update(self):
        pass
