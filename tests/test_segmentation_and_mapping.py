import numpy as np
import cv2
import pytest

from game.segmentation import (
    PcaBackgroundPersonSegmenter,
    SegmentationSettings,
)
from game.mapping import ProjectorMapper
from cpa.aligner import CameraProjectorAligner


class DummyAligner:
    def __init__(self, scale_x: float, scale_y: float):
        self.H = np.array([[scale_x, 0, 0], [0, scale_y, 0], [0, 0, 1]], dtype=np.float64)

    def get_homography(self):
        return self.H

    def transform_camera_to_projector(self, pts):
        pts = np.asarray(pts, dtype=np.float32)
        out = np.zeros_like(pts)
        out[..., 0] = pts[..., 0] * self.H[0, 0]
        out[..., 1] = pts[..., 1] * self.H[1, 1]
        return out


def test_pca_segmenter_learns_and_segments():
    settings = SegmentationSettings(downscale_factor=2, background_frames=5, pca_components=2, threshold=20)
    seg = PcaBackgroundPersonSegmenter(settings)

    h, w = 120, 160
    bg = np.full((h, w, 3), 30, dtype=np.uint8)

    # Warmup background frames with slight noise
    rng = np.random.default_rng(0)
    for _ in range(settings.background_frames):
        noise = rng.normal(0, 1, size=(h, w, 3)).astype(np.float32)
        frame = np.clip(bg.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        seg.observe_background(frame)

    assert seg.ready()

    # Add a bright square representing a person
    frame = bg.copy()
    cv2.rectangle(frame, (60, 40), (90, 80), (200, 200, 200), thickness=-1)
    features = seg.segment(frame)

    assert features.has_person
    assert features.centroid is not None
    cx, cy = features.centroid
    assert 60 <= cx <= 90
    assert 40 <= cy <= 80


def test_projector_mapper_maps_point():
    dummy = DummyAligner(scale_x=2.0, scale_y=0.5)
    mapper = ProjectorMapper(dummy)  # type: ignore[arg-type]
    proj = mapper.map_point((100.0, 200.0))
    assert proj is not None
    x, y = proj
    assert x == pytest.approx(200.0)
    assert y == pytest.approx(100.0)
