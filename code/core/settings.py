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
        



CELL_SIZE = 64
NODE_OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
NODE_DEFAULT = "eletric_components/node/node_all.png"
NODE_SPRITE_MAP = {
    frozenset({"up", "down", "left", "right"}): "eletric_components/node/node_all.png",
    frozenset({"left", "right"}): "eletric_components/node/node_horizontal.png",
    frozenset({"up", "down"}): "eletric_components/node/node_vertical.png",
    frozenset({"right", "down"}): "eletric_components/node/node_right_bottom.png",
    frozenset({"right", "up"}): "eletric_components/node/node_right_top.png",
    frozenset({"left", "up"}): "eletric_components/node/node_left_top.png",
    frozenset({"left", "down"}): "eletric_components/node/node_left_bottom.png",
    frozenset({"left", "right", "up"}): "eletric_components/node/node_t_top.png",
    frozenset({"left", "right", "down"}): "eletric_components/node/node_t_bottom.png",
    frozenset({"up", "down", "left"}): "eletric_components/node/node_t_left.png",
    frozenset({"up", "down", "right"}): "eletric_components/node/node_t_right.png",
    frozenset({"up"}): "eletric_components/node/node_top.png",
    frozenset({"down"}): "eletric_components/node/node_bottom.png",
    frozenset({"left"}): "eletric_components/node/node_left.png",
    frozenset({"right"}): "eletric_components/node/node_right.png",
    frozenset(): "eletric_components/node/node_single.png",
}

LABEL_OFFSET=45




