import os


FPS = 60

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


CODE_DIR = os.path.dirname(BASE_DIR)


PROJECT_ROOT = os.path.dirname(CODE_DIR)


ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')


def get_asset_path(subdir: str, filename: str) -> str:
    
    return os.path.join(ASSETS_DIR, subdir, filename)

