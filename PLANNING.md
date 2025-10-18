# Camera-Projector Aligner (CPA) - Planning

## Goals
- Provide a stand-alone Python module to estimate a planar homography mapping camera pixels to projector pixels using an on-screen checkerboard pattern.
- Persist calibration to JSON and support transforming arbitrary points.

## Architecture
- Package `cpa` with modules:
  - `aligner.py`: `CameraProjectorAligner` class. Load/save JSON, calibrate, transform.
  - `patterns.py`: Checkerboard generation and corner coordinate computation.
- Keep modules under 500 lines each; prefer small, focused functions.

## Conventions
- Python 3.10+, PEP8, type hints, docstrings (Google style), `black` formatting.
- Use `pydantic` for validation of persisted calibration data.
- Tests with `pytest` in `tests/` mirroring structure.

## Notes
- `calibrate()` supports file-based camera source for headless testing by reading an image when `camera_source` is a path to an existing file.
- Display backend is best-effort via pygame and safely no-ops if unavailable.
