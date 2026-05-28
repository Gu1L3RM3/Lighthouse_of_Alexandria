import os
import shutil
import sys
from pathlib import Path
from pygame.locals import *

FPS = 60

TILE_SIZE=16

BASE_DIR = Path(__file__).resolve().parent
CODE_DIR = BASE_DIR.parent
PROJECT_ROOT = CODE_DIR.parent
IS_FROZEN = bool(getattr(sys, "frozen", False))
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
DEFAULT_CIRCUITOS_DIR = BUNDLE_ROOT / "code" / "circuitos"
DEFAULT_LTSPICE_DIR = BUNDLE_ROOT / "code" / "ltspice"


def _copy_missing_tree(source_dir: Path, target_dir: Path) -> None:
    if not source_dir.exists():
        return
    for src in source_dir.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(source_dir)
        dst = target_dir / rel
        if dst.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _resolve_runtime_data_dirs() -> tuple[Path, Path]:
    if not IS_FROZEN:
        return CODE_DIR / "circuitos", CODE_DIR / "ltspice"

    base_local = os.getenv("LOCALAPPDATA")
    runtime_root = Path(base_local) if base_local else (Path.home() / "AppData" / "Local")
    runtime_root = runtime_root / "Alexandria"
    circuitos_runtime = runtime_root / "code" / "circuitos"
    ltspice_runtime = runtime_root / "code" / "ltspice"
    circuitos_runtime.mkdir(parents=True, exist_ok=True)
    ltspice_runtime.mkdir(parents=True, exist_ok=True)

    # Copia apenas arquivos que ainda nao existem no perfil do usuario.
    _copy_missing_tree(DEFAULT_CIRCUITOS_DIR, circuitos_runtime)
    _copy_missing_tree(DEFAULT_LTSPICE_DIR, ltspice_runtime)
    return circuitos_runtime, ltspice_runtime


CIRCUITOS_DIR, LTSPICE_DIR = _resolve_runtime_data_dirs()
ASSETS_DIR = str(BUNDLE_ROOT / "assets")
SAVE_DIR = CIRCUITOS_DIR.parent / "save"
SAVE_FILE = SAVE_DIR / "savegame.json"
PREFERENCES_FILE = SAVE_DIR / "preferences.json"
DEFAULT_LANGUAGE = "en"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


def path_in_circuitos(*parts: str) -> Path:
    return CIRCUITOS_DIR.joinpath(*parts)


def path_in_ltspice(*parts: str) -> Path:
    return LTSPICE_DIR.joinpath(*parts)


def path_in_save(*parts: str) -> Path:
    return SAVE_DIR.joinpath(*parts)

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
KEY_PLACE_BOMB = K_b

PLAYER_RIGHT = K_d           
PLAYER_LEFT  = K_a
PLAYER_UP    = K_w
PLAYER_DOWN  = K_s
        



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





# UI / cenas
HELP_SCROLL_STEP = 34
ELETRIC_LIST_DIALOG_MAX_SCREEN_RATIO = 0.75
ELETRIC_LIST_DIALOG_MIN_HEIGHT = 150
ELETRIC_LIST_DIALOG_SIDE_PADDING = 30
ELETRIC_LIST_DIALOG_TOP_PADDING = 52
ELETRIC_LIST_DIALOG_BOTTOM_PADDING = 24
ELETRIC_LIST_SCROLL_STEP = 36

# Gameplay de fases
GENERIC_LEVEL_TEMPORARY_LIGHT_DURATION_SECONDS = 6.0
GENERIC_LEVEL_TEMPORARY_LIGHT_FADE_OUT_SECONDS = 1.0
GENERIC_LEVEL_BOMB_ENEMY_HIT_MARGIN = 10.0
GENERIC_LEVEL_BOMB_COUNT_PER_LEVEL = 8
GENERIC_LEVEL_BOMB_EDITOR_FILE = "bombs/bomb_editor"
GENERIC_LEVEL_BOMB_TARGET_RESISTOR = "R1"
GENERIC_LEVEL_BOMB_DEFAULT_NETLIST = "bombs/default_bomb.net"
GENERIC_LEVEL_BOMB_VISUAL_SCALE = 0.34
GENERIC_LEVEL_GHOST_RESPAWN_SECONDS = 10.0
GENERIC_LEVEL_GHOST_REBIRTH_ANIM_SECONDS = 1.2

# Component overload / player weight
COMPONENT_OVERLOAD_ENABLED = True
COMPONENT_OVERLOAD_BASE_WEIGHT = {
    "resistor": 1.0,
    "current_source": 2.5,
    "voltage_source": 2.5,
}
COMPONENT_OVERLOAD_OFF_CONTEXT_BONUS = 1.35
COMPONENT_OVERLOAD_REPEAT_STEP = 0.08
COMPONENT_OVERLOAD_REPEAT_MAX_BONUS = 0.40
COMPONENT_OVERLOAD_IRRELEVANT_THRESHOLDS = (0.0, 8.0, 16.0, 28.0)
COMPONENT_OVERLOAD_SPEED_MULTIPLIERS = (1.0, 0.95, 0.90, 0.82, 0.74)
# Quantidade de componentes de referencia usada para escalar os limiares
# de sobrecarga por mapa/fase.
COMPONENT_OVERLOAD_REFERENCE_COMPONENT_COUNT = 12

# Spider webs (global tuning, shared across all phases)
SPIDER_WEB_ENABLED_DEFAULT = True
SPIDER_WEB_SPAWN_INTERVAL_SECONDS = 2.6
SPIDER_WEB_LIFETIME_SECONDS = 16.0
SPIDER_WEB_RADIUS = 15.0
SPIDER_WEB_MAX_PER_SPIDER = 4
SPIDER_WEB_GLOBAL_MAX_ACTIVE = 14
SPIDER_WEB_MIN_SPAWN_DISTANCE = 30.0
SPIDER_WEB_SLOW_MULTIPLIER = 0.38
SPIDER_WEB_SLOW_DURATION_SECONDS = 1.6
SPIDER_WEB_ARM_DELAY_SECONDS = 0.2
SPIDER_WEB_PLAYER_GRACE_SECONDS = 0.85
SPIDER_WEB_AMBUSH_SPEED = 150.0
SPIDER_WEB_AMBUSH_DURATION_SECONDS = 0.62
SPIDER_WEB_AMBUSH_COOLDOWN_SECONDS = 2.4
SPIDER_WEB_AMBUSH_PREDICTION_SECONDS = 0.45
SPIDER_WEB_CHASE_MIN_SECONDS = 1.2
SPIDER_WEB_CHASE_MAX_SECONDS = 3.8
SPIDER_WEB_CHASE_TIME_MARGIN_SECONDS = 0.55
SPIDER_WEB_ALERT_RADIUS = 120.0
SPIDER_WEB_ALERT_MAX_HELPERS = 1
# Velocidade padrao das aranhas em todas as fases
# (alinhada ao ritmo base das fases 3/4).
SPIDER_STANDARD_SPEED = 80.0

MAX_POWER_LEVEL_VOLTAGE_POOL = ["1", "2", "3.3", "5", "9", "12", "15", "20"]
MAX_POWER_LEVEL_CURRENT_POOL = ["0.001", "0.002", "0.005", "0.01", "0.05", "0.10"]

FINAL_LEVEL_DEFAULT_PANEL_HOLD_SECONDS = 90.0
FINAL_LEVEL_FINAL_FADE_SECONDS = 0.8
FINAL_LEVEL_STORAGE_TYPE_BY_KIND = {
    "resistor": "Resistor",
    "current_source": "CurrentSource",
    "voltage_source": "VoutageSource",
}

# Sistemas
DAY_NIGHT_KEY_FRAMES = [
    (0, NIGHT_COLOR),
    (4, NIGHT_COLOR),
    (6, DAWN_COLOR),
    (8, DAY_COLOR),
    (17, DAY_COLOR),
    (18, DUSK_COLOR),
    (21, NIGHT_COLOR),
    (24, NIGHT_COLOR),
]
DAY_NIGHT_GAME_HOUR_DURATION = 48.0
PHANTOM_AI_STEALTH_TIMER_NAME = "phantom_stealth_timer"
FALL_GROUND_REQUIRED_PERCENT_INSIDE = 25
FALL_GROUND_ARM_DELAY_MS = 100
FALL_GROUND_WARNING_SFX = "sfx/ui_hover.wav"
FALL_GROUND_WARNING_VOLUME = 0.8
THEVENIN_NORTON_TARGET_RESISTOR = "R1"
