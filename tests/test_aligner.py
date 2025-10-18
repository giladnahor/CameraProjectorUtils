from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
import pytest

from cpa import CameraProjectorAligner
from cpa.patterns import generate_checkerboard_image, compute_checkerboard_internal_corners


def invert_homography(H: np.ndarray) -> np.ndarray:
    return np.linalg.inv(H)


def warp_image_with_homography(image: np.ndarray, H: np.ndarray, out_size: tuple[int, int]) -> np.ndarray:
    return cv2.warpPerspective(image, H, out_size)


def test_transform_camera_to_projector_basic():
    # Simple translation homography
    tx, ty = 30.0, -15.0
    H = np.array([[1.0, 0.0, tx], [0.0, 1.0, ty], [0.0, 0.0, 1.0]], dtype=np.float64)

    aligner = CameraProjectorAligner(camera_source=0, projector_resolution=(800, 600), pattern_size=(7, 10))
    aligner._H = H

    pts_cam = np.array([[0.0, 0.0], [100.0, 100.0], [400.0, 50.0]], dtype=np.float32)
    pts_proj = aligner.transform_camera_to_projector(pts_cam)

    expected = pts_cam + np.array([tx, ty], dtype=np.float32)
    assert np.allclose(pts_proj, expected, atol=1e-5)


def test_save_and_load_homography(tmp_path: Path):
    calib_path = tmp_path / "calib.json"

    H = np.array([[1.1, 0.02, 12.0], [0.01, 0.95, -3.0], [0.0001, -0.0002, 1.0]], dtype=np.float64)

    aligner1 = CameraProjectorAligner(
        camera_source=0, projector_resolution=(1024, 768), pattern_size=(6, 9), calib_file_path=str(calib_path)
    )
    aligner1._H = H
    aligner1._save_homography(H)

    # New instance should load existing
    aligner2 = CameraProjectorAligner(
        camera_source=0, projector_resolution=(1024, 768), pattern_size=(6, 9), calib_file_path=str(calib_path)
    )
    H_loaded = aligner2.get_homography()
    assert H_loaded is not None
    assert np.allclose(H_loaded, H, atol=1e-12)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_calibrate_with_synthetic_image(tmp_path: Path):
    # Define projector and pattern
    proj_res = (800, 600)
    pattern_size = (6, 9)  # rows, cols

    # Generate projector pattern and known corner positions
    pattern_img = generate_checkerboard_image(proj_res, pattern_size)
    proj_corners = compute_checkerboard_internal_corners(proj_res, pattern_size)

    # Create a random but well-conditioned projective transform from projector->camera
    rng = np.random.default_rng(42)

    # Slight perspective warp parameters
    H_forward = np.array(
        [
            [1.0, 0.02, 20.0],
            [0.01, 0.98, 10.0],
            [2e-5, -1e-5, 1.0],
        ],
        dtype=np.float64,
    )

    cam_w, cam_h = 640, 480
    cam_image = warp_image_with_homography(pattern_img, H_forward, (cam_w, cam_h))

    # Save the synthetic camera image to disk to simulate a file-based camera source
    cam_image_bgr = cv2.cvtColor(cam_image, cv2.COLOR_GRAY2BGR)
    cam_image_path = tmp_path / "cam.png"
    cv2.imwrite(str(cam_image_path), cam_image_bgr)

    # Run calibration
    aligner = CameraProjectorAligner(
        camera_source=str(cam_image_path),
        projector_resolution=proj_res,
        pattern_size=pattern_size,
        calib_file_path=str(tmp_path / "calib.json"),
    )
    H_est = aligner.calibrate()

    # Sanity check: homography is finite and has correct shape
    assert H_est.shape == (3, 3)
    assert np.isfinite(H_est).all()

    # Validate that transforming camera corners maps to projector corners reasonably
    # Detect corners on camera image directly for this test
    found, cam_corners = cv2.findChessboardCorners(
        cam_image, (pattern_size[1], pattern_size[0]), flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
    )
    assert found
    cam_corners = cam_corners.reshape(-1, 2)
    proj_from_cam = aligner.transform_camera_to_projector(cam_corners)

    # Reprojection error median should be small
    errors = np.linalg.norm(proj_from_cam - proj_corners, axis=1)
    assert np.median(errors) < 2.0


def test_transform_requires_homography():
    aligner = CameraProjectorAligner(camera_source=0, projector_resolution=(800, 600), pattern_size=(5, 8))
    pts = np.array([[1.0, 2.0]], dtype=np.float32)
    with pytest.raises(ValueError):
        _ = aligner.transform_camera_to_projector(pts)
