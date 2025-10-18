from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import time
import cv2
import numpy as np

from .segmentation import (
    BasePersonSegmenter,
    PcaBackgroundPersonSegmenter,
    BgSubtractorPersonSegmenter,
    PersonFeatures,
    SegmentationSettings,
)
from .mapping import ProjectorMapper
from .gamefield import GameField
from .renderer import OverlayRenderer


@dataclass
class GameConfig:
    camera_source: int | str = 0
    projector_resolution: Tuple[int, int] = (1280, 720)
    use_pca: bool = True
    background_warmup_seconds: float = 3.0
    spirits_count: int = 3


class GameEngine:
    """
    Coordinates capture, segmentation, mapping, game logic and rendering.
    """

    def __init__(
        self,
        segmenter: Optional[BasePersonSegmenter],
        mapper: ProjectorMapper,
        field: GameField,
        renderer: OverlayRenderer,
        camera_source: int | str = 0,
    ) -> None:
        self.segmenter = segmenter
        self.mapper = mapper
        self.field = field
        self.renderer = renderer
        self.camera_source = camera_source
        self._cap: Optional[cv2.VideoCapture] = None

    def _ensure_capture(self) -> Optional[cv2.VideoCapture]:
        if self._cap is None:
            self._cap = cv2.VideoCapture(self.camera_source)
        return self._cap if self._cap.isOpened() else None

    def warmup_background(self, duration_s: float = 3.0) -> None:
        if not hasattr(self.segmenter, "observe_background"):
            return
        assert isinstance(self.segmenter, PcaBackgroundPersonSegmenter)
        cap = self._ensure_capture()
        if cap is None:
            return
        start = time.time()
        while time.time() - start < duration_s:
            ok, frame = cap.read()
            if not ok:
                break
            self.segmenter.observe_background(frame)

    def step(self) -> Optional[np.ndarray]:
        cap = self._ensure_capture()
        if cap is None:
            return None
        ok, frame = cap.read()
        if not ok:
            return None

        features: PersonFeatures = self.segmenter.segment(frame)
        player_proj_point: Optional[Tuple[float, float]] = None
        if features.has_person and features.centroid is not None:
            player_proj_point = self.mapper.map_point(features.centroid)

        self.field.update_with_player(player_proj_point)
        overlay = self.renderer.render_overlay(self.field, player_proj_point)
        return overlay

    @staticmethod
    def build_default(aligner, config: GameConfig) -> "GameEngine":
        mapper = ProjectorMapper(aligner)
        field = GameField.build_simple_course(config.projector_resolution, rows=3)
        renderer = OverlayRenderer(config.projector_resolution)
        if config.use_pca:
            segmenter: BasePersonSegmenter = PcaBackgroundPersonSegmenter(SegmentationSettings())
        else:
            segmenter = BgSubtractorPersonSegmenter(SegmentationSettings())
        return GameEngine(segmenter, mapper, field, renderer, camera_source=config.camera_source)
