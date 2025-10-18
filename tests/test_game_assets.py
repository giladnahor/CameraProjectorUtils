"""
Unit tests for the GameAssets module.
"""

import numpy as np
import pytest

from game.game_assets import GameAssets


class TestGameAssets:
    """Tests for GameAssets class."""

    def test_create_spirit_sprite(self):
        """Test creating a spirit sprite."""
        sprite = GameAssets.create_spirit_sprite(size=80)

        assert sprite.shape == (80, 80, 4)  # BGRA
        assert sprite.dtype == np.uint8
        # Should have some non-zero alpha values
        assert np.any(sprite[:, :, 3] > 0)

    def test_create_spirit_sprite_custom_size(self):
        """Test creating spirit sprite with custom size."""
        sprite = GameAssets.create_spirit_sprite(size=100, color=(255, 128, 64))

        assert sprite.shape == (100, 100, 4)

    def test_create_danger_zone_texture(self):
        """Test creating a danger zone texture."""
        texture = GameAssets.create_danger_zone_texture(size=100, phase=0.0)

        assert texture.shape == (100, 100, 4)  # BGRA
        assert texture.dtype == np.uint8
        # Should have red channel values
        assert np.any(texture[:, :, 2] > 0)

    def test_create_danger_zone_texture_animation(self):
        """Test that danger zone texture changes with phase."""
        texture1 = GameAssets.create_danger_zone_texture(size=100, phase=0.0)
        texture2 = GameAssets.create_danger_zone_texture(size=100, phase=0.5)

        # Textures should be different due to animation phase
        assert not np.array_equal(texture1, texture2)

    def test_create_safe_zone_texture(self):
        """Test creating a safe zone texture."""
        texture = GameAssets.create_safe_zone_texture(size=100, phase=0.0)

        assert texture.shape == (100, 100, 4)  # BGRA
        assert texture.dtype == np.uint8
        # Should have green channel values
        assert np.any(texture[:, :, 1] > 0)

    def test_create_safe_zone_texture_animation(self):
        """Test that safe zone texture changes with phase."""
        texture1 = GameAssets.create_safe_zone_texture(size=100, phase=0.0)
        texture2 = GameAssets.create_safe_zone_texture(size=100, phase=0.5)

        # Textures should be different due to animation
        assert not np.array_equal(texture1, texture2)

    def test_create_particle_effect(self):
        """Test creating a particle effect."""
        effect = GameAssets.create_particle_effect(
            num_particles=20, size=200, color=(255, 255, 255)
        )

        assert effect.shape == (200, 200, 4)  # BGRA
        assert effect.dtype == np.uint8
        # Should have some non-zero alpha values (particles)
        assert np.any(effect[:, :, 3] > 0)

    def test_create_particle_effect_custom_params(self):
        """Test creating particle effect with custom parameters."""
        effect = GameAssets.create_particle_effect(
            num_particles=50, size=300, color=(0, 255, 0)
        )

        assert effect.shape == (300, 300, 4)

    def test_create_goal_zone_texture(self):
        """Test creating a goal zone texture."""
        texture = GameAssets.create_goal_zone_texture(width=1920, height=200)

        assert texture.shape == (200, 1920, 4)  # BGRA
        assert texture.dtype == np.uint8
        # Should have non-zero alpha
        assert np.any(texture[:, :, 3] > 0)

    def test_create_game_border(self):
        """Test creating a game border."""
        border = GameAssets.create_game_border(width=800, height=600, border_width=10)

        assert border.shape == (600, 800, 4)  # BGRA
        assert border.dtype == np.uint8

    def test_create_game_border_has_corners(self):
        """Test that game border has decorative corners."""
        border = GameAssets.create_game_border(width=800, height=600, border_width=10)

        # Check corners have non-zero alpha (decorations)
        assert np.any(border[0:30, 0:30, 3] > 0)  # Top-left
        assert np.any(border[0:30, -30:, 3] > 0)  # Top-right
        assert np.any(border[-30:, 0:30, 3] > 0)  # Bottom-left
        assert np.any(border[-30:, -30:, 3] > 0)  # Bottom-right

    def test_create_countdown_number(self):
        """Test creating a countdown number graphic."""
        number_img = GameAssets.create_countdown_number(number=3, size=200)

        assert number_img.shape == (200, 200, 4)  # BGRA
        assert number_img.dtype == np.uint8
        # Should have non-zero alpha values (text)
        assert np.any(number_img[:, :, 3] > 0)

    def test_create_countdown_number_all_digits(self):
        """Test creating countdown numbers for all digits."""
        for digit in range(10):
            number_img = GameAssets.create_countdown_number(number=digit, size=150)
            assert number_img.shape == (150, 150, 4)
            assert np.any(number_img[:, :, 3] > 0)


class TestGameAssetsEdgeCases:
    """Edge case tests for GameAssets."""

    def test_create_spirit_sprite_small_size(self):
        """Test creating a very small spirit sprite."""
        sprite = GameAssets.create_spirit_sprite(size=20)

        assert sprite.shape == (20, 20, 4)
        # Should still have some content
        assert np.any(sprite[:, :, 3] > 0)

    def test_create_danger_zone_texture_edge_phases(self):
        """Test danger zone texture at edge phase values."""
        texture_0 = GameAssets.create_danger_zone_texture(size=50, phase=0.0)
        texture_1 = GameAssets.create_danger_zone_texture(size=50, phase=1.0)

        assert texture_0.shape == (50, 50, 4)
        assert texture_1.shape == (50, 50, 4)

    def test_create_particle_effect_few_particles(self):
        """Test particle effect with very few particles."""
        effect = GameAssets.create_particle_effect(num_particles=1, size=100)

        assert effect.shape == (100, 100, 4)

    def test_create_particle_effect_many_particles(self):
        """Test particle effect with many particles."""
        effect = GameAssets.create_particle_effect(num_particles=1000, size=500)

        assert effect.shape == (500, 500, 4)
        # Should have lots of alpha values
        assert np.sum(effect[:, :, 3] > 0) > 100


class TestGameAssetsConsistency:
    """Tests for consistency across multiple calls."""

    def test_spirit_sprites_consistent_size(self):
        """Test that sprite size matches requested size."""
        for size in [40, 60, 80, 100, 120]:
            sprite = GameAssets.create_spirit_sprite(size=size)
            assert sprite.shape == (size, size, 4)

    def test_danger_zone_textures_consistent_size(self):
        """Test that danger zone texture size matches requested size."""
        for size in [50, 100, 150]:
            texture = GameAssets.create_danger_zone_texture(size=size)
            assert texture.shape == (size, size, 4)

    def test_countdown_numbers_consistent_size(self):
        """Test that countdown numbers maintain consistent size."""
        for size in [100, 200, 300]:
            for number in [1, 2, 3]:
                img = GameAssets.create_countdown_number(number=number, size=size)
                assert img.shape == (size, size, 4)
