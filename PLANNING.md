# Camera-Projector Aligner (CPA) - Planning

## Goals
- Provide a stand-alone Python module to estimate a planar homography mapping camera pixels to projector pixels using an on-screen checkerboard pattern.
- Persist calibration to JSON and support transforming arbitrary points.
- Provide an interactive Halloween-themed projection game using person segmentation.

## Architecture
- Package `cpa` with modules:
  - `aligner.py`: `CameraProjectorAligner` class. Load/save JSON, calibrate, transform.
  - `patterns.py`: Checkerboard generation and corner coordinate computation.
- Package `game` with modules:
  - `person_detector.py`: Person segmentation and position tracking using background subtraction.
  - `game_engine.py`: Core game logic, rules, state management, and scoring.
  - `game_renderer.py`: Rendering game elements (zones, spirits, effects) for projection.
  - `game_assets.py`: Placeholder asset generation for sprites and zones.
  - `halloween_game.py`: Main game application integrating all components.
- Keep modules under 500 lines each; prefer small, focused functions.

## Game Design: "Spirit Crossing"
### Objective
Player must cross from one side of the projection field to the other while avoiding haunted zones and collecting magic circles.

### Rules
1. **Danger Zones**: Red pulsating areas that move and change - touching them reduces time/health
2. **Safe Circles**: Green glowing circles that appear randomly - standing on them gives bonus points/time
3. **Floating Spirits**: Ghost sprites that drift across the field - avoid contact
4. **Time Limit**: Player has limited time to cross the field
5. **Levels**: Progressive difficulty with more spirits and faster danger zones

## Conventions
- Python 3.10+, PEP8, type hints, docstrings (Google style), `black` formatting.
- Use `pydantic` for validation of persisted calibration data.
- Tests with `pytest` in `tests/` mirroring structure.

## Notes
- `calibrate()` supports file-based camera source for headless testing by reading an image when `camera_source` is a path to an existing file.
- Display backend is best-effort via pygame and safely no-ops if unavailable.
- Person detection uses OpenCV background subtraction (MOG2) for real-time performance.
- Game uses pygame for rendering and projector display integration.
