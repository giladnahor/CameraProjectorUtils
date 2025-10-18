from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from cpa.aligner import CameraProjectorAligner


@dataclass
class ProjectorMapper:
    """
    Thin wrapper around `CameraProjectorAligner` to transform camera-space points to projector-space.
    """

    aligner: CameraProjectorAligner

    def map_point(self, point_cam: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Map a single camera-space point to projector coordinates using loaded/calibrated homography.

        Args:
            point_cam: (x, y) in camera pixels.

        Returns:
            (x, y) in projector pixels, or None if no homography.
        """
        H = self.aligner.get_homography()
        if H is None:
            return None
        pts = np.array([[point_cam[0], point_cam[1]]], dtype=np.float32)
        proj = self.aligner.transform_camera_to_projector(pts)
        return float(proj[0, 0]), float(proj[0, 1])
