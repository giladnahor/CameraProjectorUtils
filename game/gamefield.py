from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np


class ZoneType(str, Enum):
    SAFE = "safe"
    DANGER = "danger"


@dataclass
class Zone:
    """
    A rectangular zone in projector coordinate space.
    """

    x: int
    y: int
    w: int
    h: int
    zone_type: ZoneType

    def contains(self, point: Tuple[float, float]) -> bool:
        px, py = point
        return (self.x <= px < self.x + self.w) and (self.y <= py < self.y + self.h)


@dataclass
class GameField:
    """
    Defines the game field layout and progression rules.

    The field consists of alternating SAFE "pumpkin patches" that the player should step on,
    and DANGER "ghost fog" regions that the player must avoid. The player wins by stepping 
    through all SAFE zones in order without touching DANGER zones for more than a grace time.
    """

    projector_resolution: Tuple[int, int]
    safe_zones: List[Zone]
    danger_zones: List[Zone]
    grace_frames: int = 10

    _current_safe_index: int = 0
    _danger_counter: int = 0
    _completed: bool = False
    _failed: bool = False

    def reset(self) -> None:
        self._current_safe_index = 0
        self._danger_counter = 0
        self._completed = False
        self._failed = False

    def update_with_player(self, player_proj_point: Optional[Tuple[float, float]]) -> None:
        """
        Update game state given the player's current projector-space position (centroid).
        """
        if self._completed or self._failed:
            return

        if player_proj_point is None:
            # No observation; do not penalize
            return

        # Check danger first
        in_danger = any(zone.contains(player_proj_point) for zone in self.danger_zones)
        if in_danger:
            self._danger_counter += 1
            if self._danger_counter > self.grace_frames:
                self._failed = True
            return
        else:
            # reset danger counter when safe
            self._danger_counter = 0

        # Check current safe zone
        if self._current_safe_index < len(self.safe_zones):
            current_zone = self.safe_zones[self._current_safe_index]
            if current_zone.contains(player_proj_point):
                self._current_safe_index += 1
                if self._current_safe_index >= len(self.safe_zones):
                    self._completed = True

    def is_completed(self) -> bool:
        return self._completed

    def is_failed(self) -> bool:
        return self._failed

    def current_target(self) -> Optional[Zone]:
        if self._completed:
            return None
        if self._current_safe_index < len(self.safe_zones):
            return self.safe_zones[self._current_safe_index]
        return None

    @staticmethod
    def build_simple_course(projector_resolution: Tuple[int, int], rows: int = 3) -> "GameField":
        """
        Build a simple course of horizontal safe strips separated by danger strips.
        """
        width, height = projector_resolution
        strip_h = height // (rows * 2 + 1)
        safe_zones: List[Zone] = []
        danger_zones: List[Zone] = []
        y = strip_h
        for i in range(rows):
            # SAFE strip
            safe_zones.append(Zone(0, y, width, strip_h, ZoneType.SAFE))
            y += strip_h
            # DANGER strip
            danger_zones.append(Zone(0, y, width, strip_h, ZoneType.DANGER))
            y += strip_h
        # Final safe at the top
        safe_zones.append(Zone(0, y, width, strip_h, ZoneType.SAFE))
        return GameField(projector_resolution, safe_zones, danger_zones)
