from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from game import Game


if __name__ == "__main__":
    Game().run()
