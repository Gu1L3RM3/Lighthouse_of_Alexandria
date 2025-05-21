from pygame import Surface
from scenes.base_scene import BaseScene
from core.components.sprite import Sprite
from core.components.position import Position
from core.components.collider import Collider
from core.components.velocity import Velocity
from core.ecs import Entity
from entities.player import Player
from core.config import TEST_MAP


class TestScene(BaseScene):
    def __init__(self,screen:Surface):
        cols = len(TEST_MAP[0])
        rows = len(TEST_MAP)

       
        tile_w = screen.get_width()  / cols
        tile_h = screen.get_height() / rows

        self.tile_size = int(min(tile_w, tile_h))

        world_w=cols*self.tile_size
        world_h=rows*self.tile_size

        super().__init__(screen,world_w,world_h)

        self.entities=[]
        self.set_map()
        self.camera.follow=self.player
        self.event_manager.subscribe('collision',self.on_collision)
    
    def set_map(self):#para teste
        for row_idx,row in enumerate(TEST_MAP):
            for col_idx, cell in enumerate(row):
                x=col_idx*self.tile_size+3
                y=row_idx*self.tile_size

                if cell=='X':
                    wall = Entity()
                    wall.add(Position(x, y))
                    wall.add(Collider(self.tile_size, self.tile_size))
                    # sprite cinza para a parede
                    surf = Surface((self.tile_size, self.tile_size))
                    surf.fill((100, 100, 100))
                    wall.add(Sprite(surf))
                    self.entities.append(wall)
                elif cell == "P":
                    
                    self.player = Player(x + self.tile_size/2, y + self.tile_size/2)
                    
                    self.entities.append(self.player)               


    def on_collision(self, evt):
        #TODO: Melhorar essa função
        
        e1, e2       = evt['entities']
        r1, r2       = evt['rects']

        
        if e1 is self.player:
            player, wall = e1, e2
            pr, wr       = r1, r2
        elif e2 is self.player:
            player, wall = e2, e1
            pr, wr       = r2, r1
        else:
            return  

        # Calcula a região de interseção
        inter = pr.clip(wr)

       
        pos = player.get(Position)   
        col = player.get(Collider)     
        vel = player.get(Velocity)    

        # Decide em qual eixo “resolver” a colisão:
        if inter.width < inter.height:
            # Colisão mais profunda no eixo X → empurra no X
            if pr.centerx < wr.centerx:
                # player veio da esquerda → encosta à esquerda da parede
                pos.x = wr.left  - col.width  - col.offset_x
            else:
                # player veio da direita → encosta à direita da parede
                pos.x = wr.right - col.offset_x
        else:
            # Colisão mais profunda no eixo Y → empurra no Y
            if pr.centery < wr.centery:
                # player veio de cima → encosta em cima da parede
                pos.y = wr.top    - col.height - col.offset_y
            else:
                # player veio de baixo → encosta embaixo da parede
                pos.y = wr.bottom - col.offset_y

        
        vel.xy = (0, 0)

    def process_input(self, events):
        self.player.input(events)

    def update(self, dt):
        self.movement_system.update(self.entities,dt)
        self.collision_system.update(self.entities,dt)

    def render(self):
        self.screen.fill((0, 0, 50))
        self.render_system.update(self.entities)
