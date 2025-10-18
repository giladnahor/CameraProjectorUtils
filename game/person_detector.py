"""
Person detection and segmentation module using background subtraction.

This module provides real-time person detection and position tracking
for interactive projection games.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, List

import cv2
import numpy as np


@dataclass
class PersonPosition:
    """
    Represents a detected person's position in the frame.

    Attributes:
        centroid (tuple[float, float]): (x, y) center point of person in pixels.
        bounding_box (tuple[int, int, int, int]): (x, y, width, height) bounding box.
        contour_area (float): Area of the detected contour in pixels.
        mask (np.ndarray): Binary mask of the person's silhouette.
    """

    centroid: Tuple[float, float]
    bounding_box: Tuple[int, int, int, int]
    contour_area: float
    mask: np.ndarray


class PersonDetector:
    """
    Detects and tracks person position using background subtraction.

    This class uses OpenCV's MOG2 background subtractor for robust
    person segmentation in varying lighting conditions.
    """

    def __init__(
        self,
        camera_source: int | str = 0,
        learning_rate: float = 0.01,
        min_contour_area: float = 1000.0,
        history: int = 500,
        var_threshold: int = 16,
    ):
        """
        Initialize the person detector.

        Args:
            camera_source (int | str): Camera index or video file path.
            learning_rate (float): Background learning rate (0-1). Lower = slower adaptation.
            min_contour_area (float): Minimum contour area to consider as a person.
            history (int): Number of frames for background model history.
            var_threshold (int): Threshold on squared Mahalanobis distance for pixel classification.
        """
        self.camera_source = camera_source
        self.learning_rate = learning_rate
        self.min_contour_area = min_contour_area

        # Initialize background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=True,
        )

        # Camera capture object
        self.cap: Optional[cv2.VideoCapture] = None
        self._frame_width: int = 0
        self._frame_height: int = 0

    def start(self) -> None:
        """
        Start the camera capture.

        Raises:
            RuntimeError: If camera cannot be opened.
        """
        self.cap = cv2.VideoCapture(self.camera_source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera source: {self.camera_source}")

        # Get frame dimensions
        self._frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def stop(self) -> None:
        """
        Stop the camera capture and release resources.
        """
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def get_frame_dimensions(self) -> Tuple[int, int]:
        """
        Get the camera frame dimensions.

        Returns:
            tuple[int, int]: (width, height) of the camera frame.
        """
        return (self._frame_width, self._frame_height)

    def detect_person(self) -> Tuple[Optional[np.ndarray], List[PersonPosition]]:
        """
        Capture a frame and detect person positions.

        Returns:
            tuple: (frame, list of PersonPosition objects).
                frame is the captured BGR image or None if capture failed.
                List contains detected persons sorted by contour area (largest first).
        """
        if self.cap is None or not self.cap.isOpened():
            return None, []

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return None, []

        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame, learningRate=self.learning_rate)

        # Remove shadows (value 127 in MOG2 output)
        _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(
            fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract person positions from contours
        persons = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_contour_area:
                continue

            # Calculate centroid using moments
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue

            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Create a mask for this contour
            person_mask = np.zeros(fg_mask.shape, dtype=np.uint8)
            cv2.drawContours(person_mask, [contour], -1, 255, -1)

            person = PersonPosition(
                centroid=(cx, cy),
                bounding_box=(x, y, w, h),
                contour_area=area,
                mask=person_mask,
            )
            persons.append(person)

        # Sort by area (largest first) - assume largest is the player
        persons.sort(key=lambda p: p.contour_area, reverse=True)

        return frame, persons

    def calibrate_background(self, num_frames: int = 30) -> None:
        """
        Calibrate the background model by processing several frames.

        This should be called when no person is in the frame to establish
        a clean background model.

        Args:
            num_frames (int): Number of frames to process for calibration.
        """
        if self.cap is None or not self.cap.isOpened():
            raise RuntimeError("Camera not started. Call start() first.")

        for _ in range(num_frames):
            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Apply with higher learning rate for faster adaptation
                self.bg_subtractor.apply(frame, learningRate=0.1)

    def reset_background_model(self) -> None:
        """
        Reset the background subtraction model.

        Useful when lighting conditions change or scene changes dramatically.
        """
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True,
        )

    def __enter__(self) -> PersonDetector:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()
