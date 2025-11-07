from core.ecs import Entity
from core.components.position import Position
from core.components.sprite import Sprite
from core.managers.resource_manager import ResourceManager

class Delete(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/delete.png"
        surf=rm.load_image(img_path)


        self.add(
            Sprite(surf,image_path=img_path),
            Position(x,y)
        )

class Rotate(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/rotate.png"
        surf=rm.load_image(img_path)
        self.add(
            Sprite(surf,image_path=img_path),
            Position(x,y)
        )



class Select(Entity):
    def __init__(self,x,y):
        super().__init__()
        rm=ResourceManager.get()
        img_path="eletric_components/select.png"
        surf=rm.load_image(img_path)

        self.add(
            Sprite(surf,image_path=img_path),
            Position(x,y)
        )
