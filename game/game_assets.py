"""
Game asset generation module for placeholder sprites and zones.

This module creates placeholder graphics for the Halloween game
until actual game assets are produced.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np


class GameAssets:
    """
    Generates placeholder game assets like spirits, zones, and effects.

    All assets are generated procedurally as numpy arrays (images).
    """

    @staticmethod
    def create_spirit_sprite(size: int = 80, color: Tuple[int, int, int] = (200, 200, 255)) -> np.ndarray:
        """
        Create a ghost/spirit sprite with transparency.

        Args:
            size (int): Size of the sprite in pixels (square).
            color (tuple): BGR color for the spirit.

        Returns:
            np.ndarray: BGRA image with alpha channel.
        """
        # Create BGRA image
        sprite = np.zeros((size, size, 4), dtype=np.uint8)

        # Draw ghost body (rounded shape)
        center = (size // 2, size // 2)
        # Head circle
        cv2.circle(sprite, center, size // 3, (*color, 255), -1)

        # Body (ellipse below head)
        body_center = (size // 2, int(size * 0.65))
        axes = (size // 3, size // 3)
        cv2.ellipse(sprite, body_center, axes, 0, 0, 180, (*color, 255), -1)

        # Wavy bottom edge (ghost tail)
        for i in range(3):
            x = size // 4 + i * size // 4
            y = int(size * 0.85 + np.sin(i * np.pi / 2) * 5)
            cv2.circle(sprite, (x, y), size // 8, (*color, 255), -1)

        # Eyes (dark circles)
        eye_y = int(size * 0.45)
        cv2.circle(sprite, (int(size * 0.4), eye_y), size // 12, (50, 50, 50, 255), -1)
        cv2.circle(sprite, (int(size * 0.6), eye_y), size // 12, (50, 50, 50, 255), -1)

        # Apply gaussian blur for smooth edges
        sprite = cv2.GaussianBlur(sprite, (5, 5), 0)

        return sprite

    @staticmethod
    def create_danger_zone_texture(size: int = 100, phase: float = 0.0) -> np.ndarray:
        """
        Create an animated danger zone texture (red, pulsating).

        Args:
            size (int): Size of the texture in pixels (square).
            phase (float): Animation phase (0-1) for pulsating effect.

        Returns:
            np.ndarray: BGRA image with alpha channel.
        """
        texture = np.zeros((size, size, 4), dtype=np.uint8)

        # Pulsating intensity based on phase
        intensity = int(150 + 105 * np.sin(phase * 2 * np.pi))
        alpha = int(100 + 80 * np.sin(phase * 2 * np.pi))

        # Create gradient from center
        center = (size // 2, size // 2)
        for y in range(size):
            for x in range(size):
                dist = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
                max_dist = size / 2
                if dist < max_dist:
                    factor = 1 - (dist / max_dist)
                    r = min(255, int(intensity * factor))
                    texture[y, x] = (0, 0, r, int(alpha * factor))

        # Add some fiery texture
        noise = np.random.randint(0, 30, (size, size), dtype=np.uint8)
        texture[:, :, 2] = np.clip(texture[:, :, 2].astype(np.int16) + noise, 0, 255).astype(np.uint8)

        return texture

    @staticmethod
    def create_safe_zone_texture(size: int = 100, phase: float = 0.0) -> np.ndarray:
        """
        Create a safe zone texture (green, glowing).

        Args:
            size (int): Size of the texture in pixels (square).
            phase (float): Animation phase (0-1) for glowing effect.

        Returns:
            np.ndarray: BGRA image with alpha channel.
        """
        texture = np.zeros((size, size, 4), dtype=np.uint8)

        # Glowing intensity based on phase
        intensity = int(150 + 105 * np.sin(phase * 2 * np.pi))
        alpha = 180

        # Create circular gradient
        center = (size // 2, size // 2)
        for y in range(size):
            for x in range(size):
                dist = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
                max_dist = size / 2
                if dist < max_dist:
                    factor = 1 - (dist / max_dist)
                    g = min(255, int(intensity * factor))
                    texture[y, x] = (0, g, 0, int(alpha * factor))

        # Add sparkle effect
        num_sparkles = 5 + int(5 * np.sin(phase * 2 * np.pi))
        for _ in range(num_sparkles):
            sx = np.random.randint(size // 4, 3 * size // 4)
            sy = np.random.randint(size // 4, 3 * size // 4)
            cv2.circle(texture, (sx, sy), 2, (200, 255, 200, 255), -1)

        return texture

    @staticmethod
    def create_particle_effect(
        num_particles: int = 20,
        size: int = 200,
        color: Tuple[int, int, int] = (255, 255, 255),
    ) -> np.ndarray:
        """
        Create a particle effect (for collecting safe zones, etc.).

        Args:
            num_particles (int): Number of particles.
            size (int): Size of the effect area in pixels.
            color (tuple): BGR color for particles.

        Returns:
            np.ndarray: BGRA image with particles.
        """
        effect = np.zeros((size, size, 4), dtype=np.uint8)

        for _ in range(num_particles):
            x = np.random.randint(0, size)
            y = np.random.randint(0, size)
            radius = np.random.randint(1, 4)
            alpha = np.random.randint(150, 255)
            cv2.circle(effect, (x, y), radius, (*color, alpha), -1)

        return effect

    @staticmethod
    def create_goal_zone_texture(width: int, height: int) -> np.ndarray:
        """
        Create the goal zone texture (where player needs to reach).

        Args:
            width (int): Width of the zone.
            height (int): Height of the zone.

        Returns:
            np.ndarray: BGRA image.
        """
        texture = np.zeros((height, width, 4), dtype=np.uint8)

        # Create a glowing orange/yellow zone
        for y in range(height):
            progress = y / height
            b = 0
            g = int(150 + 105 * (1 - progress))
            r = int(200 + 55 * (1 - progress))
            alpha = 150

            texture[y, :] = (b, g, r, alpha)

        # Add horizontal stripes
        stripe_height = height // 10
        for i in range(0, height, stripe_height * 2):
            texture[i : i + stripe_height // 2, :, 3] = 200

        return texture

    @staticmethod
    def create_game_border(width: int, height: int, border_width: int = 10) -> np.ndarray:
        """
        Create a border frame for the game field.

        Args:
            width (int): Width of the game field.
            height (int): Height of the game field.
            border_width (int): Width of the border.

        Returns:
            np.ndarray: BGRA image with border.
        """
        border = np.zeros((height, width, 4), dtype=np.uint8)

        # Draw purple/dark border
        color = (139, 69, 19, 255)  # Dark purple/brown
        cv2.rectangle(
            border,
            (0, 0),
            (width - 1, height - 1),
            color,
            border_width,
        )

        # Add decorative corners
        corner_size = border_width * 3
        corners = [
            (0, 0),
            (width - corner_size, 0),
            (0, height - corner_size),
            (width - corner_size, height - corner_size),
        ]

        for cx, cy in corners:
            cv2.rectangle(
                border,
                (cx, cy),
                (cx + corner_size, cy + corner_size),
                (200, 100, 50, 255),
                -1,
            )

        return border

    @staticmethod
    def create_countdown_number(number: int, size: int = 200) -> np.ndarray:
        """
        Create a large countdown number graphic.

        Args:
            number (int): Number to display (0-9).
            size (int): Size of the number graphic.

        Returns:
            np.ndarray: BGRA image with the number.
        """
        img = np.zeros((size, size, 4), dtype=np.uint8)

        # Draw number with large font
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = str(number)
        font_scale = size / 100
        thickness = max(5, size // 40)

        # Get text size for centering
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )

        x = (size - text_width) // 2
        y = (size + text_height) // 2

        # Draw text with outline for visibility
        cv2.putText(img, text, (x, y), font, font_scale, (0, 0, 0, 255), thickness + 4)
        cv2.putText(
            img, text, (x, y), font, font_scale, (0, 255, 255, 255), thickness
        )

        return img
