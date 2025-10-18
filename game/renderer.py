from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

from .gamefield import GameField, ZoneType


@dataclass
class OverlayRenderer:
    projector_resolution: Tuple[int, int]

    def render_overlay(self, field: GameField, player_proj_point: Optional[Tuple[float, float]]) -> np.ndarray:
        """
        Render a projector-space overlay visualizing safe/danger zones and player position.
        """
        width, height = self.projector_resolution
        overlay = np.zeros((height, width, 3), dtype=np.uint8)

        # Draw zones
        for z in field.danger_zones:
            cv2.rectangle(overlay, (z.x, z.y), (z.x + z.w, z.y + z.h), (0, 0, 180), thickness=-1)  # dark red
        for z in field.safe_zones:
            color = (0, 100, 0)
            cv2.rectangle(overlay, (z.x, z.y), (z.x + z.w, z.y + z.h), color, thickness=2)

        # Highlight current target safe zone
        target = field.current_target()
        if target is not None:
            cv2.rectangle(overlay, (target.x, target.y), (target.x + target.w, target.y + target.h), (0, 255, 0), 3)

        # Player marker
        if player_proj_point is not None:
            cx, cy = int(player_proj_point[0]), int(player_proj_point[1])
            cv2.circle(overlay, (cx, cy), 10, (255, 255, 255), thickness=-1)
            cv2.circle(overlay, (cx, cy), 14, (0, 0, 0), thickness=2)

        # Halloween theme accents (placeholder): pumpkin icons as orange circles bordering safe zones
        if target is not None:
            cx = target.x + target.w // 2
            cy = target.y + target.h // 2
            cv2.circle(overlay, (cx, cy), 18, (0, 140, 255), thickness=3)  # pumpkin glow

        # Victory / failure banners
        if field.is_completed():
            cv2.putText(overlay, "YOU ESCAPED THE HAUNTED FIELD!", (50, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (0, 255, 0), 3, cv2.LINE_AA)
        elif field.is_failed():
            cv2.putText(overlay, "GHOSTS GOT YOU!", (50, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                        (0, 0, 255), 3, cv2.LINE_AA)

        return overlay
