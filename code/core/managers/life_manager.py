class LifeManager:
    _instance = None

    def __init__(self, max_lives: int = 10):
        self.max_lives = max_lives
        self.current_lives = max_lives

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = LifeManager()
        return cls._instance

    def set_max_lives(self, lives: int):
        if lives < 1:
            raise ValueError("max_lives must be >= 1")
        self.max_lives = lives
        if self.current_lives > self.max_lives:
            self.current_lives = self.max_lives

    def reset_lives(self):
        self.current_lives = self.max_lives

    def lose_life(self) -> int:
        if self.current_lives > 0:
            self.current_lives -= 1
        return self.current_lives

    def has_lives(self) -> bool:
        return self.current_lives > 0

    def is_game_over(self) -> bool:
        return self.current_lives <= 0
