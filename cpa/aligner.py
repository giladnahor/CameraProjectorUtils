from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Union, List

import cv2
import numpy as np
from pydantic import BaseModel, Field, ValidationError

from .patterns import (
    compute_checkerboard_internal_corners,
    generate_checkerboard_image,
)


class CalibrationData(BaseModel):
    """Pydantic model for persisted homography calibration data."""

    projector_resolution: Tuple[int, int]
    pattern_size: Tuple[int, int]  # (rows, cols)
    homography: List[List[float]] = Field(..., min_length=3, max_length=3)
    version: int = 1


@dataclass
class CameraProjectorAligner:
    """
    Provides automated camera-to-projector alignment via planar homography.

    Attributes:
        _H (np.ndarray | None): 3x3 homography from camera pixel coords to projector pixel coords.
        _camera_source (int | str): Video capture index or path. If string and a file path, a single
            image will be loaded for calibration instead of opening a camera.
        _pattern_size (tuple[int, int]): (rows, cols) of internal corners.
        _proj_res (tuple[int, int]): (width, height) of projector.
        _calib_file_path (str): JSON path for saving/loading homography and metadata.
    """

    camera_source: Union[int, str]
    projector_resolution: Tuple[int, int]
    pattern_size: Tuple[int, int]
    calib_file_path: str = "calibration_data.json"

    def __post_init__(self) -> None:
        self._H: Optional[np.ndarray] = None
        self._camera_source: Union[int, str] = self.camera_source
        self._pattern_size: Tuple[int, int] = self.pattern_size
        self._proj_res: Tuple[int, int] = self.projector_resolution
        self._calib_file_path: str = self.calib_file_path

        self._load_homography_if_available()

    # ------------------------- Public API -------------------------
    def calibrate(self) -> np.ndarray:
        """
        Execute calibration by detecting a checkerboard and estimating homography with RANSAC.

        Returns:
            np.ndarray: 3x3 homography mapping camera pixel coordinates to projector pixel coordinates.

        Raises:
            RuntimeError: If calibration fails to detect the pattern or compute homography.
        """
        # Prepare projector pattern geometry and image (for optional display)
        projector_corners = compute_checkerboard_internal_corners(
            self._proj_res, self._pattern_size
        )  # shape (N, 2), float32

        pattern_image = generate_checkerboard_image(self._proj_res, self._pattern_size)
        self._display_pattern(pattern_image)

        # Acquire a single frame from camera source or image file
        frame = self._capture_single_frame()
        if frame is None:
            raise RuntimeError("Failed to capture frame from camera source")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame

        # OpenCV expects (cols, rows)
        rows, cols = self._pattern_size
        pattern_size_cv = (cols, rows)

        found, corners = cv2.findChessboardCorners(
            gray,
            pattern_size_cv,
            flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE,
        )
        if not found or corners is None:
            raise RuntimeError("Checkerboard not found in camera frame")

        # Refine detected corners for sub-pixel accuracy
        termination_criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,
            0.001,
        )
        cv2.cornerSubPix(
            gray,
            corners,
            winSize=(11, 11),
            zeroZone=(-1, -1),
            criteria=termination_criteria,
        )

        # corners shape is (N, 1, 2) float32; reshape to (N, 2)
        camera_corners = corners.reshape(-1, 2).astype(np.float32)

        if camera_corners.shape[0] != projector_corners.shape[0]:
            raise RuntimeError(
                "Mismatch in number of detected corners vs expected projector corners"
            )

        H, mask = cv2.findHomography(camera_corners, projector_corners, cv2.RANSAC)
        if H is None or not np.all(np.isfinite(H)):
            raise RuntimeError("cv2.findHomography failed to compute a valid matrix")

        self._H = H.astype(np.float64)
        self._save_homography(self._H)
        return self._H

    def transform_camera_to_projector(self, points_cam: np.ndarray) -> np.ndarray:
        """
        Transform camera pixel coordinates to projector pixel coordinates using the estimated H.

        Args:
            points_cam (np.ndarray): Array of shape (N, 2) of camera pixel coords.

        Returns:
            np.ndarray: Array of shape (N, 2) of projector pixel coords.

        Raises:
            ValueError: If homography is not available.
        """
        if self._H is None:
            raise ValueError("Homography is not available. Run calibrate() first or load from file.")

        pts = np.asarray(points_cam, dtype=np.float32)
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError("points_cam must be of shape (N, 2)")

        pts_reshaped = pts.reshape(-1, 1, 2)
        transformed = cv2.perspectiveTransform(pts_reshaped, self._H)
        return transformed.reshape(-1, 2)

    def get_homography(self) -> Optional[np.ndarray]:
        """
        Get the current homography or None if not calibrated.

        Returns:
            Optional[np.ndarray]: 3x3 homography matrix or None.
        """
        return self._H.copy() if self._H is not None else None

    # ------------------------- Private/Utility -------------------------
    def _capture_single_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the configured camera source or an image file.

        Returns:
            Optional[np.ndarray]: BGR or grayscale image as numpy array, or None on failure.
        """
        # If camera_source is a string that points to a file, read it as an image
        if isinstance(self._camera_source, str):
            path = Path(self._camera_source)
            if path.exists() and path.is_file():
                img = cv2.imread(str(path), cv2.IMREAD_COLOR)
                return img

        # Otherwise try to open a camera device
        cap = cv2.VideoCapture(self._camera_source)
        if not cap.isOpened():
            cap.release()
            return None
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return None
        return frame

    def _display_pattern(self, pattern_image: np.ndarray) -> None:
        """
        Display the calibration pattern in a dedicated window if a display backend is available.

        This implementation is best-effort and safe to no-op in headless environments.
        """
        # Attempt pygame if available and a display seems present
        try:
            import os

            if os.environ.get("SDL_VIDEODRIVER") == "dummy":
                return

            import pygame

            pygame.init()
            display_flags = pygame.FULLSCREEN
            screen = pygame.display.set_mode(self._proj_res, display_flags)
            pygame.display.set_caption("CPA Calibration Pattern")

            surface = pygame.surfarray.make_surface(
                np.stack([pattern_image] * 3, axis=-1).swapaxes(0, 1)
            )
            screen.blit(surface, (0, 0))
            pygame.display.flip()

            # Pump events briefly to ensure the window actually shows
            pygame.event.pump()
        except Exception:
            # Silently ignore in environments without a display or pygame
            return

    def _save_homography(self, H: np.ndarray) -> None:
        """
        Persist the homography and metadata to JSON file.

        Args:
            H (np.ndarray): 3x3 homography matrix.
        """
        data = CalibrationData(
            projector_resolution=self._proj_res,
            pattern_size=self._pattern_size,
            homography=H.tolist(),
        )
        path = Path(self._calib_file_path)
        path.write_text(data.model_dump_json(indent=2))

    def _load_homography_if_available(self) -> None:
        """
        Attempt to load previously saved calibration from disk.
        """
        path = Path(self._calib_file_path)
        if not path.exists():
            return
        try:
            json_text = path.read_text()
            parsed = CalibrationData.model_validate_json(json_text)
            if (
                tuple(parsed.projector_resolution) == tuple(self._proj_res)
                and tuple(parsed.pattern_size) == tuple(self._pattern_size)
            ):
                H = np.array(parsed.homography, dtype=np.float64)
                if H.shape == (3, 3) and np.all(np.isfinite(H)):
                    self._H = H
        except (ValidationError, json.JSONDecodeError):
            # Ignore invalid file content
            return
