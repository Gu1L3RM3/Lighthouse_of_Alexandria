from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class DisplayConfig:
    width: int
    height: int
    flags: int


class DisplayConfigResolver:
    WEB_DEFAULT_WIDTH = 1280
    WEB_DEFAULT_HEIGHT = 720

    @classmethod
    def resolve(cls) -> DisplayConfig:
        return DisplayConfig(
            width=cls.WEB_DEFAULT_WIDTH,
            height=cls.WEB_DEFAULT_HEIGHT,
            flags=0,
        )
