"""
Game renderer module for projecting game visuals.

This module handles rendering all game elements including zones,
spirits, UI, and effects onto the projection surface.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

import cv2
import numpy as np

from .game_assets import GameAssets
from .game_engine import GameEngine, GameState, Spirit, DangerZone, SafeZone


class GameRenderer:
    """
    Renders game elements for projection display.

    Handles drawing all visual elements including spirits, zones,
    UI elements, and effects.
    """

    def __init__(self, width: int, height: int):
        """
        Initialize the game renderer.

        Args:
            width (int): Width of the projection surface in pixels.
            height (int): Height of the projection surface in pixels.
        """
        self.width = width
        self.height = height
        self.assets = GameAssets()

        # Pre-render some assets
        self._spirit_sprite = self.assets.create_spirit_sprite(size=80)
        self._start_time = time.time()

    def render_frame(
        self, engine: GameEngine, show_debug: bool = False
    ) -> np.ndarray:
        """
        Render a complete game frame.

        Args:
            engine (GameEngine): The game engine instance to render.
            show_debug (bool): Whether to show debug information.

        Returns:
            np.ndarray: BGR image of the rendered frame.
        """
        # Create black background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Render based on game state
        if engine.state == GameState.READY:
            self._render_ready_screen(frame)
        elif engine.state == GameState.COUNTDOWN:
            self._render_countdown(frame, engine)
        elif engine.state == GameState.PLAYING:
            self._render_gameplay(frame, engine, show_debug)
        elif engine.state == GameState.WIN:
            self._render_win_screen(frame, engine)
        elif engine.state == GameState.LOSE:
            self._render_lose_screen(frame, engine)

        return frame

    def _render_ready_screen(self, frame: np.ndarray) -> None:
        """
        Render the ready/waiting screen.

        Args:
            frame (np.ndarray): Frame to render onto.
        """
        # Draw title
        title = "SPIRIT CROSSING"
        self._draw_text(
            frame,
            title,
            (self.width // 2, self.height // 3),
            font_scale=2.5,
            color=(0, 255, 255),
            thickness=4,
            centered=True,
        )

        # Draw instructions
        instructions = [
            "Stand in the START zone to begin",
            "",
            "GOAL: Reach the goal zone at the top",
            "AVOID: Red danger zones and ghosts",
            "COLLECT: Green safe circles for points",
        ]

        y_start = self.height // 2
        for i, line in enumerate(instructions):
            self._draw_text(
                frame,
                line,
                (self.width // 2, y_start + i * 40),
                font_scale=0.8,
                color=(200, 200, 200),
                thickness=2,
                centered=True,
            )

    def _render_countdown(self, frame: np.ndarray, engine: GameEngine) -> None:
        """
        Render the countdown screen.

        Args:
            frame (np.ndarray): Frame to render onto.
            engine (GameEngine): Game engine instance.
        """
        # Draw game field zones first
        self._render_zones(frame, engine)

        # Draw large countdown number
        number = engine.get_countdown_number()
        if number is not None and number > 0:
            countdown_sprite = self.assets.create_countdown_number(number, size=300)
            self._overlay_sprite(
                frame,
                countdown_sprite,
                (self.width // 2 - 150, self.height // 2 - 150),
            )

        # Draw "GET READY" text
        self._draw_text(
            frame,
            "GET READY!",
            (self.width // 2, self.height // 4),
            font_scale=2.0,
            color=(0, 255, 255),
            thickness=3,
            centered=True,
        )

    def _render_gameplay(
        self, frame: np.ndarray, engine: GameEngine, show_debug: bool
    ) -> None:
        """
        Render active gameplay elements.

        Args:
            frame (np.ndarray): Frame to render onto.
            engine (GameEngine): Game engine instance.
            show_debug (bool): Whether to show debug overlays.
        """
        # Draw zones (start, goal)
        self._render_zones(frame, engine)

        # Draw danger zones
        phase = (time.time() - self._start_time) % 1.0
        for danger_zone in engine.danger_zones:
            self._render_danger_zone(frame, danger_zone, phase)

        # Draw safe zones
        for safe_zone in engine.safe_zones:
            self._render_safe_zone(frame, safe_zone, phase)

        # Draw spirits
        for spirit in engine.spirits:
            self._render_spirit(frame, spirit)

        # Draw player indicator (if detected)
        if engine.player_position is not None:
            self._render_player_indicator(frame, engine.player_position)

        # Draw UI (score, time, health)
        self._render_ui(frame, engine)

        # Debug overlay
        if show_debug:
            self._render_debug_info(frame, engine)

    def _render_win_screen(self, frame: np.ndarray, engine: GameEngine) -> None:
        """
        Render the victory screen.

        Args:
            frame (np.ndarray): Frame to render onto.
            engine (GameEngine): Game engine instance.
        """
        # Draw celebratory message
        self._draw_text(
            frame,
            "YOU WIN!",
            (self.width // 2, self.height // 3),
            font_scale=3.0,
            color=(0, 255, 0),
            thickness=5,
            centered=True,
        )

        # Draw final score
        score_text = f"Final Score: {engine.score}"
        self._draw_text(
            frame,
            score_text,
            (self.width // 2, self.height // 2),
            font_scale=1.5,
            color=(0, 255, 255),
            thickness=3,
            centered=True,
        )

        # Draw particle effects
        particles = self.assets.create_particle_effect(
            num_particles=100, size=self.width, color=(0, 255, 0)
        )
        self._overlay_sprite(frame, particles, (0, 0))

    def _render_lose_screen(self, frame: np.ndarray, engine: GameEngine) -> None:
        """
        Render the game over screen.

        Args:
            frame (np.ndarray): Frame to render onto.
            engine (GameEngine): Game engine instance.
        """
        # Draw game over message
        self._draw_text(
            frame,
            "GAME OVER",
            (self.width // 2, self.height // 3),
            font_scale=3.0,
            color=(0, 0, 255),
            thickness=5,
            centered=True,
        )

        # Draw final score
        score_text = f"Score: {engine.score}"
        self._draw_text(
            frame,
            score_text,
            (self.width // 2, self.height // 2),
            font_scale=1.5,
            color=(200, 200, 200),
            thickness=3,
            centered=True,
        )

    def _render_zones(self, frame: np.ndarray, engine: GameEngine) -> None:
        """
        Render start and goal zones.

        Args:
            frame (np.ndarray): Frame to render onto.
            engine (GameEngine): Game engine instance.
        """
        # Draw goal zone (top)
        goal_texture = self.assets.create_goal_zone_texture(
            self.width, engine.goal_zone_height
        )
        self._overlay_sprite(frame, goal_texture, (0, 0))

        # Draw start zone (bottom)
        start_y = self.height - engine.start_zone_height
        start_texture = self.assets.create_goal_zone_texture(
            self.width, engine.start_zone_height
        )
        # Flip colors for start zone (make it greenish)
        start_texture[:, :, [0, 1]] = start_texture[:, :, [1, 0]]
        self._overlay_sprite(frame, start_texture, (0, start_y))

        # Draw labels
        self._draw_text(
            frame,
            "GOAL",
            (self.width // 2, engine.goal_zone_height // 2),
            font_scale=1.5,
            color=(255, 255, 255),
            thickness=3,
            centered=True,
        )

        self._draw_text(
            frame,
            "START",
            (self.width // 2, start_y + engine.start_zone_height // 2),
            font_scale=1.5,
            color=(255, 255, 255),
            thickness=3,
            centered=True,
        )

    def _render_danger_zone(
        self, frame: np.ndarray, zone: DangerZone, phase: float
    ) -> None:
        """
        Render a danger zone.

        Args:
            frame (np.ndarray): Frame to render onto.
            zone (DangerZone): Danger zone to render.
            phase (float): Animation phase (0-1).
        """
        # Create danger texture
        size = int(zone.radius * 2)
        texture = self.assets.create_danger_zone_texture(size=size, phase=phase)

        # Calculate position (center the texture)
        x = int(zone.position[0] - zone.radius)
        y = int(zone.position[1] - zone.radius)

        self._overlay_sprite(frame, texture, (x, y))

    def _render_safe_zone(
        self, frame: np.ndarray, zone: SafeZone, phase: float
    ) -> None:
        """
        Render a safe zone.

        Args:
            frame (np.ndarray): Frame to render onto.
            zone (SafeZone): Safe zone to render.
            phase (float): Animation phase (0-1).
        """
        # Create safe zone texture
        size = int(zone.radius * 2)
        texture = self.assets.create_safe_zone_texture(size=size, phase=phase)

        # Calculate position
        x = int(zone.position[0] - zone.radius)
        y = int(zone.position[1] - zone.radius)

        self._overlay_sprite(frame, texture, (x, y))

    def _render_spirit(self, frame: np.ndarray, spirit: Spirit) -> None:
        """
        Render a spirit/ghost.

        Args:
            frame (np.ndarray): Frame to render onto.
            spirit (Spirit): Spirit to render.
        """
        # Calculate position
        x = int(spirit.position[0] - spirit.sprite_size // 2)
        y = int(spirit.position[1] - spirit.sprite_size // 2)

        # Use pre-rendered sprite
        self._overlay_sprite(frame, self._spirit_sprite, (x, y))

    def _render_player_indicator(
        self, frame: np.ndarray, position: Tuple[float, float]
    ) -> None:
        """
        Render a visual indicator at the player's position.

        Args:
            frame (np.ndarray): Frame to render onto.
            position (tuple): Player (x, y) position.
        """
        px, py = int(position[0]), int(position[1])

        # Draw pulsating circle
        phase = (time.time() * 2) % 1.0
        radius = int(20 + 10 * np.sin(phase * 2 * np.pi))

        cv2.circle(frame, (px, py), radius, (255, 255, 0), 3)
        cv2.circle(frame, (px, py), 5, (255, 255, 255), -1)

    def _render_ui(self, frame: np.ndarray, engine: GameEngine) -> None:
        """
        Render UI elements (score, time, health).

        Args:
            frame (np.ndarray): Frame to render onto.
            engine (GameEngine): Game engine instance.
        """
        # Score
        score_text = f"Score: {engine.score}"
        self._draw_text(
            frame, score_text, (20, 40), font_scale=1.0, color=(255, 255, 255), thickness=2
        )

        # Time
        time_text = f"Time: {int(engine.time_remaining)}s"
        time_color = (0, 255, 255) if engine.time_remaining > 10 else (0, 0, 255)
        self._draw_text(
            frame, time_text, (20, 80), font_scale=1.0, color=time_color, thickness=2
        )

        # Health bar
        self._render_health_bar(frame, engine.health, (20, 110))

    def _render_health_bar(
        self, frame: np.ndarray, health: float, position: Tuple[int, int]
    ) -> None:
        """
        Render a health bar.

        Args:
            frame (np.ndarray): Frame to render onto.
            health (float): Current health (0-100).
            position (tuple): (x, y) position of the bar.
        """
        bar_width = 200
        bar_height = 20
        x, y = position

        # Background
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (100, 100, 100), -1)

        # Health fill
        fill_width = int(bar_width * (health / 100.0))
        health_color = (0, 255, 0) if health > 50 else (0, 165, 255) if health > 25 else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x + fill_width, y + bar_height), health_color, -1)

        # Border
        cv2.rectangle(frame, (x, y), (x + bar_width, y + bar_height), (255, 255, 255), 2)

        # Text
        health_text = f"Health: {int(health)}"
        cv2.putText(
            frame,
            health_text,
            (x + bar_width + 10, y + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

    def _render_debug_info(self, frame: np.ndarray, engine: GameEngine) -> None:
        """
        Render debug information overlay.

        Args:
            frame (np.ndarray): Frame to render onto.
            engine (GameEngine): Game engine instance.
        """
        debug_lines = [
            f"Spirits: {len(engine.spirits)}",
            f"Dangers: {len(engine.danger_zones)}",
            f"Safe Zones: {len(engine.safe_zones)}",
            f"Player: {engine.player_position}",
        ]

        y = self.height - 100
        for line in debug_lines:
            self._draw_text(
                frame, line, (self.width - 300, y), font_scale=0.5, color=(255, 255, 0), thickness=1
            )
            y += 20

    def _overlay_sprite(
        self, frame: np.ndarray, sprite: np.ndarray, position: Tuple[int, int]
    ) -> None:
        """
        Overlay a sprite with alpha channel onto the frame.

        Args:
            frame (np.ndarray): Destination BGR frame.
            sprite (np.ndarray): BGRA sprite to overlay.
            position (tuple): (x, y) top-left position.
        """
        x, y = position
        h, w = sprite.shape[:2]

        # Clamp to frame boundaries
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            # Compute valid region
            src_x1 = max(0, -x)
            src_y1 = max(0, -y)
            src_x2 = w - max(0, (x + w) - self.width)
            src_y2 = h - max(0, (y + h) - self.height)

            dst_x1 = max(0, x)
            dst_y1 = max(0, y)
            dst_x2 = min(self.width, x + w)
            dst_y2 = min(self.height, y + h)

            if src_x2 <= src_x1 or src_y2 <= src_y1:
                return  # Completely outside frame

            sprite = sprite[src_y1:src_y2, src_x1:src_x2]
            x, y = dst_x1, dst_y1
            h, w = sprite.shape[:2]

        # Extract alpha channel
        if sprite.shape[2] == 4:
            alpha = sprite[:, :, 3:4] / 255.0
            sprite_bgr = sprite[:, :, :3]
        else:
            alpha = np.ones((h, w, 1), dtype=np.float32)
            sprite_bgr = sprite

        # Blend
        roi = frame[y : y + h, x : x + w]
        blended = (sprite_bgr * alpha + roi * (1 - alpha)).astype(np.uint8)
        frame[y : y + h, x : x + w] = blended

    def _draw_text(
        self,
        frame: np.ndarray,
        text: str,
        position: Tuple[int, int],
        font_scale: float = 1.0,
        color: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = 2,
        centered: bool = False,
    ) -> None:
        """
        Draw text on the frame with optional centering.

        Args:
            frame (np.ndarray): Frame to draw on.
            text (str): Text to draw.
            position (tuple): (x, y) position.
            font_scale (float): Font scale factor.
            color (tuple): BGR color.
            thickness (int): Text thickness.
            centered (bool): Whether to center text at position.
        """
        font = cv2.FONT_HERSHEY_SIMPLEX

        if centered:
            (text_width, text_height), baseline = cv2.getTextSize(
                text, font, font_scale, thickness
            )
            x = position[0] - text_width // 2
            y = position[1] + text_height // 2
            position = (x, y)

        # Draw outline for better visibility
        cv2.putText(
            frame, text, position, font, font_scale, (0, 0, 0), thickness + 2
        )
        cv2.putText(frame, text, position, font, font_scale, color, thickness)
