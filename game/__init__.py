"""
Halloween-themed interactive projection game package.

This package provides modules for person detection, game logic,
rendering, and asset management for an interactive projection game.
"""

__version__ = "1.0.0"

from .person_detector import PersonDetector
from .game_engine import GameEngine, GameState
from .game_renderer import GameRenderer
from .halloween_game import HalloweenGame

__all__ = [
    "PersonDetector",
    "GameEngine",
    "GameState",
    "GameRenderer",
    "HalloweenGame",
]
