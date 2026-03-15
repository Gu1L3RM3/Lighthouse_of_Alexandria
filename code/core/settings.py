import os
from pathlib import Path
from pygame.locals import *

FPS = 60

TILE_SIZE=16

BASE_DIR = Path(__file__).resolve().parent
CODE_DIR = BASE_DIR.parent
PROJECT_ROOT = CODE_DIR.parent
ASSETS_DIR = str(PROJECT_ROOT / 'assets')
CIRCUITOS_DIR = CODE_DIR / 'circuitos'
LTSPICE_DIR = CODE_DIR / 'ltspice'


def path_in_circuitos(*parts: str) -> Path:
    return CIRCUITOS_DIR.joinpath(*parts)


def path_in_ltspice(*parts: str) -> Path:
    return LTSPICE_DIR.joinpath(*parts)

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

COMERCIAL_RESISTORS = {
    '1.0': 1.0, '1.2': 1.2, '1.5': 1.5, '1.8': 1.8, '2.2': 2.2, '2.7': 2.7, 
    '3.3': 3.3, '3.9': 3.9, '4.7': 4.7, '5.6': 5.6, '6.8': 6.8, '8.2': 8.2, 
    '10': 10.0, '12': 12.0, '15': 15.0, '18': 18.0, '22': 22.0, '27': 27.0, 
    '33': 33.0, '39': 39.0, '47': 47.0, '56': 56.0, '68': 68.0, '82': 82.0, 
    '100': 100.0, '120': 120.0, '150': 150.0, '180': 180.0, '220': 220.0, '270': 270.0, 
    '330': 330.0, '390': 390.0, '470': 470.0, '560': 560.0, '680': 680.0, '820': 820.0, 
    '1.0k': 1000.0, '1.2k': 1200.0, '1.5k': 1500.0, '1.8k': 1800.0, '2.2k': 2200.0, '2.7k': 2700.0, 
    '3.3k': 3300.0, '3.9k': 3900.0, '4.7k': 4700.0, '5.6k': 5600.0, '6.8k': 6800.0, '8.2k': 8200.0, 
    '10k': 10000.0, '12k': 12000.0, '15k': 15000.0, '18k': 18000.0, '22k': 22000.0, '27k': 27000.0, 
    '33k': 33000.0, '39k': 39000.0, '47k': 47000.0, '56k': 56000.0, '68k': 68000.0, '82k': 82000.0, 
    '100k': 100000.0, '120k': 120000.0, '150k': 150000.0, '180k': 180000.0, '220k': 220000.0, '270k': 270000.0, 
    '330k': 330000.0, '390k': 390000.0, '470k': 470000.0, '560k': 560000.0, '680k': 680000.0, '820k': 820000.0, 
    '1.0M': 1000000.0
}

# Pools de fontes usados no mapa (fase 6 e validadores associados).
MAP_VOLTAGE_SOURCE_POOL = [
    "0.5", "1", "1.5", "2", "3.3", "4.5", "5", "6", "7.5",
    "9", "10", "12", "15", "18", "20", "24", "30", "36"
]

MAP_CURRENT_SOURCE_POOL = [
    "0.0001", "0.0002", "0.0005", "0.001", "0.002", "0.003", "0.005", "0.0075",
    "0.01", "0.015", "0.02", "0.03", "0.05", "0.1", "0.15", "0.2"
]

PREFIXES = [
            (1e12, 'T'), (1e9, 'G'), (1e6, 'M'), (1e3, 'k'),
            (1, ''),
            (1e-3, 'm'), (1e-6, 'µ'), (1e-9, 'n'), (1e-12, 'p')
        ]




