"""
Unit tests for the PersonDetector module.
"""

import numpy as np
import pytest

from game.person_detector import PersonDetector, PersonPosition


class TestPersonPosition:
    """Tests for PersonPosition dataclass."""

    def test_person_position_creation(self):
        """Test creating a PersonPosition instance."""
        mask = np.zeros((100, 100), dtype=np.uint8)
        person = PersonPosition(
            centroid=(50.0, 60.0),
            bounding_box=(25, 30, 50, 60),
            contour_area=3000.0,
            mask=mask,
        )

        assert person.centroid == (50.0, 60.0)
        assert person.bounding_box == (25, 30, 50, 60)
        assert person.contour_area == 3000.0
        assert person.mask.shape == (100, 100)


class TestPersonDetector:
    """Tests for PersonDetector class."""

    def test_initialization(self):
        """Test PersonDetector initialization with default parameters."""
        detector = PersonDetector(camera_source=0)

        assert detector.camera_source == 0
        assert detector.learning_rate == 0.01
        assert detector.min_contour_area == 1000.0
        assert detector.cap is None

    def test_initialization_custom_params(self):
        """Test PersonDetector initialization with custom parameters."""
        detector = PersonDetector(
            camera_source="video.mp4",
            learning_rate=0.05,
            min_contour_area=2000.0,
            history=300,
            var_threshold=20,
        )

        assert detector.camera_source == "video.mp4"
        assert detector.learning_rate == 0.05
        assert detector.min_contour_area == 2000.0

    def test_detect_person_without_start(self):
        """Test that detect_person returns None when camera not started."""
        detector = PersonDetector(camera_source=0)
        frame, persons = detector.detect_person()

        assert frame is None
        assert persons == []

    def test_context_manager_interface(self):
        """Test PersonDetector context manager usage."""
        # Note: This test will fail if no camera is available
        # In CI/CD, this would be mocked
        detector = PersonDetector(camera_source=0)

        # Test that context manager methods exist
        assert hasattr(detector, "__enter__")
        assert hasattr(detector, "__exit__")

    def test_reset_background_model(self):
        """Test resetting the background model."""
        detector = PersonDetector(camera_source=0)
        old_bg = detector.bg_subtractor

        detector.reset_background_model()

        # Background subtractor should be a new instance
        assert detector.bg_subtractor is not old_bg

    def test_get_frame_dimensions_before_start(self):
        """Test getting frame dimensions before starting camera."""
        detector = PersonDetector(camera_source=0)
        width, height = detector.get_frame_dimensions()

        assert width == 0
        assert height == 0


class TestPersonDetectorEdgeCases:
    """Edge case tests for PersonDetector."""

    def test_stop_without_start(self):
        """Test that stop() works even if start() was never called."""
        detector = PersonDetector(camera_source=0)
        # Should not raise an exception
        detector.stop()

    def test_multiple_stop_calls(self):
        """Test calling stop() multiple times."""
        detector = PersonDetector(camera_source=0)
        detector.stop()
        # Second stop should not raise an exception
        detector.stop()


class TestPersonDetectorFailureCases:
    """Failure case tests for PersonDetector."""

    def test_invalid_camera_source(self):
        """Test that invalid camera source raises RuntimeError on start."""
        detector = PersonDetector(camera_source=999)  # Very unlikely to exist

        with pytest.raises(RuntimeError, match="Failed to open camera source"):
            detector.start()

    def test_calibrate_without_start(self):
        """Test that calibrate_background raises error when camera not started."""
        detector = PersonDetector(camera_source=0)

        with pytest.raises(RuntimeError, match="Camera not started"):
            detector.calibrate_background(num_frames=10)
