"""
Game engine module for Halloween projection game.

This module handles game logic, state management, scoring,
and collision detection for the Spirit Crossing game.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional

import numpy as np


class GameState(Enum):
    """Game state enumeration."""

    READY = "ready"  # Waiting to start
    COUNTDOWN = "countdown"  # Countdown before game starts
    PLAYING = "playing"  # Active gameplay
    PAUSED = "paused"  # Game paused
    WIN = "win"  # Player won
    LOSE = "lose"  # Player lost


@dataclass
class Spirit:
    """
    Represents a floating spirit/ghost in the game.

    Attributes:
        position (tuple[float, float]): Current (x, y) position.
        velocity (tuple[float, float]): Movement velocity (vx, vy).
        radius (float): Collision radius in pixels.
        sprite_size (int): Display size of the spirit sprite.
    """

    position: Tuple[float, float]
    velocity: Tuple[float, float]
    radius: float = 40.0
    sprite_size: int = 80


@dataclass
class DangerZone:
    """
    Represents a danger zone (haunted area) in the game.

    Attributes:
        position (tuple[float, float]): Center (x, y) position.
        radius (float): Radius of the zone in pixels.
        velocity (tuple[float, float]): Movement velocity (vx, vy).
        damage (int): Damage/time penalty for touching this zone.
    """

    position: Tuple[float, float]
    radius: float
    velocity: Tuple[float, float] = (0.0, 0.0)
    damage: int = 5


@dataclass
class SafeZone:
    """
    Represents a safe zone (magic circle) in the game.

    Attributes:
        position (tuple[float, float]): Center (x, y) position.
        radius (float): Radius of the zone in pixels.
        points (int): Points awarded for standing in this zone.
        lifetime (float): How long this zone exists (seconds).
        created_at (float): Timestamp when zone was created.
    """

    position: Tuple[float, float]
    radius: float = 50.0
    points: int = 10
    lifetime: float = 5.0
    created_at: float = field(default_factory=time.time)


class GameEngine:
    """
    Core game engine for Spirit Crossing Halloween game.

    Manages game state, entities, collision detection, and scoring.
    """

    def __init__(
        self,
        field_width: int,
        field_height: int,
        level: int = 1,
        time_limit: float = 60.0,
    ):
        """
        Initialize the game engine.

        Args:
            field_width (int): Width of the game field in pixels.
            field_height (int): Height of the game field in pixels.
            level (int): Starting difficulty level (1-5).
            time_limit (float): Time limit in seconds to complete the level.
        """
        self.field_width = field_width
        self.field_height = field_height
        self.level = level
        self.time_limit = time_limit

        # Game state
        self.state = GameState.READY
        self.score = 0
        self.time_remaining = time_limit
        self.health = 100

        # Player tracking
        self.player_position: Optional[Tuple[float, float]] = None
        self.start_zone_height = field_height // 10  # Bottom 10% is start
        self.goal_zone_height = field_height // 10  # Top 10% is goal

        # Game entities
        self.spirits: List[Spirit] = []
        self.danger_zones: List[DangerZone] = []
        self.safe_zones: List[SafeZone] = []

        # Timing
        self._last_update_time = time.time()
        self._countdown_start_time = 0.0
        self._game_start_time = 0.0
        self._last_safe_zone_spawn = 0.0
        self._safe_zone_spawn_interval = 3.0  # Spawn safe zone every 3 seconds

        # Level configuration
        self._configure_level(level)

    def _configure_level(self, level: int) -> None:
        """
        Configure game difficulty based on level.

        Args:
            level (int): Difficulty level (1-5).
        """
        # Number of spirits increases with level
        num_spirits = 2 + level
        for _ in range(num_spirits):
            self._spawn_spirit()

        # Number of danger zones increases with level
        num_dangers = 1 + level
        for _ in range(num_dangers):
            self._spawn_danger_zone()

    def _spawn_spirit(self) -> None:
        """
        Spawn a new spirit at a random position with random velocity.
        """
        # Random position in middle area (avoid start/goal zones)
        x = np.random.uniform(0, self.field_width)
        y = np.random.uniform(
            self.goal_zone_height + 50,
            self.field_height - self.start_zone_height - 50,
        )

        # Random velocity (horizontal and slight vertical)
        speed = 20 + np.random.random() * 30 * self.level  # pixels per second
        angle = np.random.uniform(0, 2 * np.pi)
        vx = speed * np.cos(angle)
        vy = speed * np.sin(angle) * 0.5  # Less vertical movement

        spirit = Spirit(
            position=(x, y),
            velocity=(vx, vy),
            radius=35.0 + np.random.random() * 15,
        )
        self.spirits.append(spirit)

    def _spawn_danger_zone(self) -> None:
        """
        Spawn a new danger zone with random position and movement.
        """
        # Random position in middle area
        x = np.random.uniform(100, self.field_width - 100)
        y = np.random.uniform(
            self.goal_zone_height + 100,
            self.field_height - self.start_zone_height - 100,
        )

        # Some zones move, some are static
        if np.random.random() < 0.6:  # 60% chance of moving
            speed = 10 + np.random.random() * 20 * self.level
            angle = np.random.uniform(0, 2 * np.pi)
            vx = speed * np.cos(angle)
            vy = speed * np.sin(angle)
        else:
            vx, vy = 0, 0

        radius = 40 + np.random.random() * 40
        damage = 3 + self.level * 2

        zone = DangerZone(
            position=(x, y), radius=radius, velocity=(vx, vy), damage=damage
        )
        self.danger_zones.append(zone)

    def _spawn_safe_zone(self) -> None:
        """
        Spawn a new safe zone at a random position.
        """
        # Random position in middle area
        x = np.random.uniform(100, self.field_width - 100)
        y = np.random.uniform(
            self.goal_zone_height + 100,
            self.field_height - self.start_zone_height - 100,
        )

        safe_zone = SafeZone(
            position=(x, y),
            radius=50.0,
            points=10 + self.level * 5,
            lifetime=5.0,
        )
        self.safe_zones.append(safe_zone)
        self._last_safe_zone_spawn = time.time()

    def start_countdown(self) -> None:
        """
        Start the countdown sequence before gameplay begins.
        """
        self.state = GameState.COUNTDOWN
        self._countdown_start_time = time.time()

    def start_game(self) -> None:
        """
        Start active gameplay.
        """
        self.state = GameState.PLAYING
        self._game_start_time = time.time()
        self._last_update_time = time.time()

    def update(self, player_position: Optional[Tuple[float, float]]) -> None:
        """
        Update game state for the current frame.

        Args:
            player_position (tuple | None): Current player (x, y) position or None if not detected.
        """
        current_time = time.time()
        dt = current_time - self._last_update_time
        self._last_update_time = current_time

        # Update based on game state
        if self.state == GameState.COUNTDOWN:
            elapsed = current_time - self._countdown_start_time
            if elapsed >= 3.0:  # 3 second countdown
                self.start_game()
            return

        if self.state != GameState.PLAYING:
            return

        # Update time remaining
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.state = GameState.LOSE
            return

        # Update player position
        self.player_position = player_position

        if player_position is None:
            return  # No player detected, skip updates

        px, py = player_position

        # Check if player reached goal
        if py < self.goal_zone_height:
            self.state = GameState.WIN
            # Bonus points for remaining time
            self.score += int(self.time_remaining * 10)
            return

        # Update spirits
        self._update_spirits(dt)

        # Update danger zones
        self._update_danger_zones(dt)

        # Update safe zones
        self._update_safe_zones(dt, player_position)

        # Spawn new safe zones periodically
        if current_time - self._last_safe_zone_spawn > self._safe_zone_spawn_interval:
            self._spawn_safe_zone()

        # Check collisions
        self._check_collisions(player_position)

        # Check if health depleted
        if self.health <= 0:
            self.state = GameState.LOSE

    def _update_spirits(self, dt: float) -> None:
        """
        Update spirit positions and handle boundary collisions.

        Args:
            dt (float): Time delta in seconds.
        """
        for spirit in self.spirits:
            x, y = spirit.position
            vx, vy = spirit.velocity

            # Update position
            x += vx * dt
            y += vy * dt

            # Bounce off boundaries
            if x < spirit.radius or x > self.field_width - spirit.radius:
                vx = -vx
                x = np.clip(x, spirit.radius, self.field_width - spirit.radius)

            if y < self.goal_zone_height or y > self.field_height - self.start_zone_height:
                vy = -vy
                y = np.clip(
                    y, self.goal_zone_height, self.field_height - self.start_zone_height
                )

            spirit.position = (x, y)
            spirit.velocity = (vx, vy)

    def _update_danger_zones(self, dt: float) -> None:
        """
        Update danger zone positions and handle boundary collisions.

        Args:
            dt (float): Time delta in seconds.
        """
        for zone in self.danger_zones:
            if zone.velocity == (0.0, 0.0):
                continue

            x, y = zone.position
            vx, vy = zone.velocity

            # Update position
            x += vx * dt
            y += vy * dt

            # Bounce off boundaries
            if x < zone.radius or x > self.field_width - zone.radius:
                vx = -vx
                x = np.clip(x, zone.radius, self.field_width - zone.radius)

            if y < self.goal_zone_height or y > self.field_height - self.start_zone_height:
                vy = -vy
                y = np.clip(
                    y, self.goal_zone_height, self.field_height - self.start_zone_height
                )

            zone.position = (x, y)
            zone.velocity = (vx, vy)

    def _update_safe_zones(self, dt: float, player_position: Tuple[float, float]) -> None:
        """
        Update safe zones and check for player collection.

        Args:
            dt (float): Time delta in seconds.
            player_position (tuple): Player (x, y) position.
        """
        current_time = time.time()
        zones_to_remove = []

        for i, zone in enumerate(self.safe_zones):
            # Check if zone expired
            if current_time - zone.created_at > zone.lifetime:
                zones_to_remove.append(i)
                continue

            # Check if player is standing in zone
            px, py = player_position
            zx, zy = zone.position
            distance = np.sqrt((px - zx) ** 2 + (py - zy) ** 2)

            if distance < zone.radius:
                # Award points
                self.score += zone.points
                zones_to_remove.append(i)

        # Remove collected/expired zones
        for i in reversed(zones_to_remove):
            self.safe_zones.pop(i)

    def _check_collisions(self, player_position: Tuple[float, float]) -> None:
        """
        Check for collisions between player and spirits/danger zones.

        Args:
            player_position (tuple): Player (x, y) position.
        """
        px, py = player_position

        # Check spirit collisions
        for spirit in self.spirits:
            sx, sy = spirit.position
            distance = np.sqrt((px - sx) ** 2 + (py - sy) ** 2)

            if distance < spirit.radius + 20:  # 20px player radius approximation
                # Take damage
                self.health -= 1
                self.health = max(0, self.health)

        # Check danger zone collisions
        for zone in self.danger_zones:
            zx, zy = zone.position
            distance = np.sqrt((px - zx) ** 2 + (py - zy) ** 2)

            if distance < zone.radius + 20:
                # Take damage
                self.health -= zone.damage * 0.016  # Per frame damage (at ~60fps)
                self.health = max(0, self.health)

    def get_countdown_number(self) -> Optional[int]:
        """
        Get the current countdown number (3, 2, 1) or None if not in countdown.

        Returns:
            int | None: Countdown number or None.
        """
        if self.state != GameState.COUNTDOWN:
            return None

        elapsed = time.time() - self._countdown_start_time
        remaining = 3 - int(elapsed)
        return max(0, remaining) if remaining > 0 else None

    def reset(self) -> None:
        """
        Reset the game to initial state.
        """
        self.state = GameState.READY
        self.score = 0
        self.time_remaining = self.time_limit
        self.health = 100
        self.player_position = None

        self.spirits.clear()
        self.danger_zones.clear()
        self.safe_zones.clear()

        self._configure_level(self.level)
        self._last_update_time = time.time()
