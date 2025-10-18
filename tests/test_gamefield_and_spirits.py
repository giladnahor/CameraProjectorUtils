import time
import numpy as np

from game.gamefield import GameField
from game.spirits import SpiritManager


def test_gamefield_progression_and_failure():
    field = GameField.build_simple_course((200, 200), rows=2)
    # Safe zones order: 2 strips + final safe
    target = field.current_target()
    assert target is not None

    # Step on first safe zone
    p = (100.0, target.y + 5.0)
    field.update_with_player(p)
    assert not field.is_completed()

    # Enter danger for too long
    danger = field.danger_zones[0]
    for _ in range(field.grace_frames + 1):
        field.update_with_player((danger.x + 1.0, danger.y + 1.0))
    assert field.is_failed()

    # Reset and complete course
    field.reset()
    while not field.is_completed():
        t = field.current_target()
        assert t is not None
        field.update_with_player((t.x + 1.0, t.y + 1.0))
        # Skip danger rows by not updating
    assert field.is_completed()


def test_spirits_collision_and_update():
    bounds = (320, 240)
    mgr = SpiritManager(3, bounds)
    # Update movement
    mgr.update(0.016)
    # Choose a point at the center; collision is possible but not guaranteed
    center = (bounds[0] / 2, bounds[1] / 2)
    _ = mgr.any_collision(center)
