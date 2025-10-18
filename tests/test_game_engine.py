"""
Unit tests for the GameEngine module.
"""

import time

import numpy as np
import pytest

from game.game_engine import (
    DangerZone,
    GameEngine,
    GameState,
    SafeZone,
    Spirit,
)


class TestGameState:
    """Tests for GameState enum."""

    def test_game_states_exist(self):
        """Test that all expected game states exist."""
        assert GameState.READY
        assert GameState.COUNTDOWN
        assert GameState.PLAYING
        assert GameState.PAUSED
        assert GameState.WIN
        assert GameState.LOSE


class TestSpirit:
    """Tests for Spirit dataclass."""

    def test_spirit_creation(self):
        """Test creating a Spirit instance."""
        spirit = Spirit(position=(100.0, 200.0), velocity=(10.0, 5.0))

        assert spirit.position == (100.0, 200.0)
        assert spirit.velocity == (10.0, 5.0)
        assert spirit.radius == 40.0
        assert spirit.sprite_size == 80


class TestDangerZone:
    """Tests for DangerZone dataclass."""

    def test_danger_zone_creation(self):
        """Test creating a DangerZone instance."""
        zone = DangerZone(
            position=(300.0, 400.0), radius=50.0, velocity=(5.0, -5.0), damage=10
        )

        assert zone.position == (300.0, 400.0)
        assert zone.radius == 50.0
        assert zone.velocity == (5.0, -5.0)
        assert zone.damage == 10


class TestSafeZone:
    """Tests for SafeZone dataclass."""

    def test_safe_zone_creation(self):
        """Test creating a SafeZone instance."""
        zone = SafeZone(position=(150.0, 250.0), radius=40.0, points=20, lifetime=10.0)

        assert zone.position == (150.0, 250.0)
        assert zone.radius == 40.0
        assert zone.points == 20
        assert zone.lifetime == 10.0
        assert isinstance(zone.created_at, float)


class TestGameEngine:
    """Tests for GameEngine class."""

    def test_initialization(self):
        """Test GameEngine initialization with default parameters."""
        engine = GameEngine(field_width=1920, field_height=1080)

        assert engine.field_width == 1920
        assert engine.field_height == 1080
        assert engine.level == 1
        assert engine.time_limit == 60.0
        assert engine.state == GameState.READY
        assert engine.score == 0
        assert engine.health == 100
        assert engine.player_position is None

    def test_initialization_custom_params(self):
        """Test GameEngine initialization with custom parameters."""
        engine = GameEngine(
            field_width=800, field_height=600, level=3, time_limit=120.0
        )

        assert engine.field_width == 800
        assert engine.field_height == 600
        assert engine.level == 3
        assert engine.time_limit == 120.0

    def test_level_configuration_spawns_entities(self):
        """Test that level configuration spawns spirits and danger zones."""
        engine = GameEngine(field_width=1920, field_height=1080, level=2)

        # Level 2 should spawn 2 + 2 = 4 spirits and 1 + 2 = 3 danger zones
        assert len(engine.spirits) == 4
        assert len(engine.danger_zones) == 3

    def test_start_countdown(self):
        """Test starting the countdown sequence."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_countdown()

        assert engine.state == GameState.COUNTDOWN
        assert engine._countdown_start_time > 0

    def test_start_game(self):
        """Test starting active gameplay."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_game()

        assert engine.state == GameState.PLAYING
        assert engine._game_start_time > 0

    def test_get_countdown_number(self):
        """Test getting countdown number."""
        engine = GameEngine(field_width=1920, field_height=1080)

        # Not in countdown, should return None
        assert engine.get_countdown_number() is None

        # Start countdown
        engine.start_countdown()
        number = engine.get_countdown_number()

        # Should return 3, 2, or 1
        assert number is None or number in [0, 1, 2, 3]

    def test_reset(self):
        """Test resetting the game state."""
        engine = GameEngine(field_width=1920, field_height=1080, level=2)

        # Modify state
        engine.state = GameState.PLAYING
        engine.score = 100
        engine.health = 50
        engine.time_remaining = 30.0

        # Reset
        engine.reset()

        # Check state is reset
        assert engine.state == GameState.READY
        assert engine.score == 0
        assert engine.health == 100
        assert engine.time_remaining == engine.time_limit
        assert engine.player_position is None

    def test_update_without_player_position(self):
        """Test update with no player detected."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_game()

        initial_time = engine.time_remaining
        time.sleep(0.1)
        engine.update(player_position=None)

        # Time should decrease
        assert engine.time_remaining < initial_time

    def test_update_player_reaches_goal(self):
        """Test that player reaching goal zone triggers win state."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_game()

        # Position player in goal zone (top 10%)
        player_pos = (960.0, 50.0)  # Near top
        engine.update(player_position=player_pos)

        assert engine.state == GameState.WIN
        # Score should include time bonus
        assert engine.score > 0

    def test_time_runs_out(self):
        """Test that running out of time triggers lose state."""
        engine = GameEngine(field_width=1920, field_height=1080, time_limit=0.1)
        engine.start_game()

        time.sleep(0.2)
        engine.update(player_position=(960.0, 540.0))

        assert engine.state == GameState.LOSE

    def test_health_depletes_triggers_lose(self):
        """Test that zero health triggers lose state."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_game()
        engine.health = 0

        engine.update(player_position=(960.0, 540.0))

        assert engine.state == GameState.LOSE


class TestGameEngineCollisions:
    """Tests for collision detection in GameEngine."""

    def test_spirit_collision_damages_player(self):
        """Test that colliding with a spirit reduces health."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_game()

        # Clear spirits and add one at known position
        engine.spirits.clear()
        engine.spirits.append(Spirit(position=(500.0, 500.0), velocity=(0.0, 0.0)))

        initial_health = engine.health

        # Update with player at same position
        engine.update(player_position=(500.0, 500.0))

        # Health should decrease
        assert engine.health < initial_health

    def test_danger_zone_collision_damages_player(self):
        """Test that standing in danger zone reduces health."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_game()

        # Clear danger zones and add one at known position
        engine.danger_zones.clear()
        engine.danger_zones.append(
            DangerZone(position=(600.0, 600.0), radius=50.0, damage=10)
        )

        initial_health = engine.health

        # Update with player in danger zone
        engine.update(player_position=(600.0, 600.0))

        # Health should decrease
        assert engine.health < initial_health

    def test_safe_zone_collection_awards_points(self):
        """Test that standing in safe zone awards points."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_game()

        # Disable auto-spawning for this test
        engine._last_safe_zone_spawn = time.time()
        engine._safe_zone_spawn_interval = 1000.0  # Very long interval

        # Clear any existing safe zones
        engine.safe_zones.clear()

        # Add safe zone at known position
        engine.safe_zones.append(SafeZone(position=(700.0, 700.0), points=50))

        initial_score = engine.score

        # Update with player on safe zone
        engine.update(player_position=(700.0, 700.0))

        # Score should increase
        assert engine.score > initial_score
        # Safe zone should be removed after collection
        assert len(engine.safe_zones) == 0


class TestGameEngineEdgeCases:
    """Edge case tests for GameEngine."""

    def test_update_during_countdown(self):
        """Test that update during countdown progresses to playing state."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.start_countdown()

        # Wait for countdown to finish
        time.sleep(3.1)
        engine.update(player_position=None)

        assert engine.state == GameState.PLAYING

    def test_update_after_game_ends(self):
        """Test that update after game ends doesn't change state."""
        engine = GameEngine(field_width=1920, field_height=1080)
        engine.state = GameState.WIN

        engine.update(player_position=(960.0, 540.0))

        # State should remain WIN
        assert engine.state == GameState.WIN
