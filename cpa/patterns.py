from __future__ import annotations

from typing import Tuple

import numpy as np
import cv2


def compute_checkerboard_internal_corners(
    projector_resolution: Tuple[int, int], pattern_size: Tuple[int, int]
) -> np.ndarray:
    """
    Compute the ideal 2D coordinates of checkerboard internal corners in projector pixel space.

    Args:
        projector_resolution (Tuple[int, int]): (width, height) of the projector/display in pixels.
        pattern_size (Tuple[int, int]): (rows, cols) of internal corners.

    Returns:
        np.ndarray: Array of shape (rows*cols, 2) with float32 coordinates ordered row-major
            from top-left to bottom-right, matching OpenCV's chessboard corner ordering.
    """
    width, height = projector_resolution
    rows, cols = pattern_size

    if rows <= 1 or cols <= 1:
        raise ValueError("pattern_size must have at least 2x2 internal corners")

    # Leave a margin of 1 square around the internal corners grid to ensure good detection
    # and room for displaying full squares. Choose square size that fits within the display.
    square_size = int(min(width / (cols + 3), height / (rows + 3)))
    if square_size < 5:
        raise ValueError("Projector resolution too small for the given pattern_size")

    margin_x = (width - square_size * (cols + 1)) // 2
    margin_y = (height - square_size * (rows + 1)) // 2

    corners: list[tuple[float, float]] = []
    for r in range(rows):
        for c in range(cols):
            x = margin_x + (c + 1) * square_size
            y = margin_y + (r + 1) * square_size
            corners.append((float(x), float(y)))

    return np.array(corners, dtype=np.float32)


def generate_checkerboard_image(
    projector_resolution: Tuple[int, int], pattern_size: Tuple[int, int]
) -> np.ndarray:
    """
    Generate a high-contrast checkerboard image suitable for display on a projector.

    The checkerboard is constructed such that the internal corners (pattern_size) are centered
    on the screen and spaced by a constant square size. There is a 1-square margin around the
    internal-corner grid to yield full squares at borders.

    Args:
        projector_resolution (Tuple[int, int]): (width, height) in pixels.
        pattern_size (Tuple[int, int]): (rows, cols) internal corners.

    Returns:
        np.ndarray: Grayscale image (H, W) uint8 with values 0 or 255.
    """
    width, height = projector_resolution
    rows, cols = pattern_size

    if rows <= 1 or cols <= 1:
        raise ValueError("pattern_size must have at least 2x2 internal corners")

    # Compute square size consistent with corner computation
    square_size = int(min(width / (cols + 3), height / (rows + 3)))
    if square_size < 5:
        raise ValueError("Projector resolution too small for the given pattern_size")

    margin_x = (width - square_size * (cols + 1)) // 2
    margin_y = (height - square_size * (rows + 1)) // 2

    image = np.full((height, width), 255, dtype=np.uint8)

    # The full grid will be (rows + 2) by (cols + 2) squares to create a 1-square margin
    grid_rows = rows + 2
    grid_cols = cols + 2

    top_left_x = margin_x - square_size
    top_left_y = margin_y - square_size

    for gr in range(grid_rows):
        for gc in range(grid_cols):
            # Checkerboard alternates by parity
            is_black = (gr + gc) % 2 == 0
            x0 = top_left_x + gc * square_size
            y0 = top_left_y + gr * square_size
            x1 = x0 + square_size
            y1 = y0 + square_size

            # Clip to image bounds
            x0_clamped = max(0, x0)
            y0_clamped = max(0, y0)
            x1_clamped = min(width, x1)
            y1_clamped = min(height, y1)

            if x0_clamped < x1_clamped and y0_clamped < y1_clamped and is_black:
                image[y0_clamped:y1_clamped, x0_clamped:x1_clamped] = 0

    return image
