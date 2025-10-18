from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import math
import random


@dataclass
class Spirit:
    """
    A Halloween-themed spirit that floats in the field.

    Spirits patrol along simple parametric paths; touching a spirit is treated as danger.
    """

    x: float
    y: float
    radius: int
    speed: float
    path_phase: float
    path_amplitude: float

    def update(self, dt: float, bounds: Tuple[int, int]) -> None:
        width, height = bounds
        # Circular-ish Lissajous path
        self.path_phase += self.speed * dt
        self.x = (width / 2) + self.path_amplitude * math.cos(self.path_phase)
        self.y = (height / 2) + self.path_amplitude * math.sin(2 * self.path_phase)
        # Keep within bounds softly
        self.x = max(self.radius, min(width - self.radius, self.x))
        self.y = max(self.radius, min(height - self.radius, self.y))

    def collides(self, point: Tuple[float, float]) -> bool:
        px, py = point
        return (px - self.x) ** 2 + (py - self.y) ** 2 <= self.radius ** 2


class SpiritManager:
    def __init__(self, num_spirits: int, bounds: Tuple[int, int]) -> None:
        self.bounds = bounds
        self.spirits: List[Spirit] = []
        width, height = bounds
        for i in range(num_spirits):
            radius = random.randint(20, 40)
            amplitude = random.uniform(min(width, height) * 0.1, min(width, height) * 0.25)
            speed = random.uniform(0.5, 1.2)
            phase = random.uniform(0, math.tau)
            x0 = random.uniform(radius, width - radius)
            y0 = random.uniform(radius, height - radius)
            self.spirits.append(
                Spirit(x=x0, y=y0, radius=radius, speed=speed, path_phase=phase, path_amplitude=amplitude)
            )

    def update(self, dt: float) -> None:
        for s in self.spirits:
            s.update(dt, self.bounds)

    def any_collision(self, point: Tuple[float, float]) -> bool:
        return any(s.collides(point) for s in self.spirits)
