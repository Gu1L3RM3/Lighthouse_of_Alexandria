import os
from pygame.locals import *

FPS = 60

TILE_SIZE=16

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(CODE_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')

DAWN_COLOR   = (255, 120, 50, 100)
DAY_COLOR    = (135, 206, 250, 0)  
DUSK_COLOR   = (255, 120, 50, 100) 
NIGHT_COLOR  = (10, 5, 40, 160)
WHITE        = (255,255,255)
BLACK        = (0,0,0)
GREEN        = (0,255,0)
BLUE         = (0,0,255)
RED          = (255,0,0)
YELLOW       = (255,255,0)
TRANSPARENT  = (0,0,0,0)

FONT = "PressStart2P-Regular.ttf"

KEY_DIALOG = K_e
KEY_NEXT_SCENE = K_SPACE

PLAYER_RIGHT = K_d           
PLAYER_LEFT  = K_a
PLAYER_UP    = K_w
PLAYER_DOWN  = K_s
PLAYER_ATTACK = K_l
        









