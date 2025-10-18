# Camera-Projector Aligner (CPA)

A lightweight Python library to align a camera and projector (or display) via planar homography using a checkerboard pattern.

## Features
- Generate and display a high-contrast checkerboard pattern
- Detect corners with OpenCV and estimate homography with RANSAC
- Save/load calibration to JSON with validation
- Transform camera-space points into projector-space

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```python
from cpa import CameraProjectorAligner

aligner = CameraProjectorAligner(
    camera_source=0,  # or a path to an image file for testing
    projector_resolution=(1920, 1080),
    pattern_size=(7, 10),  # rows, cols of internal corners
)

H = aligner.calibrate()            # display pattern, capture, detect, compute H
pts_proj = aligner.transform_camera_to_projector([[100, 200], [300, 400]])
```

## Testing
```bash
pytest -q
```

## Notes
- If pygame is not available or a display is not present, pattern display is skipped.
- When `camera_source` is a string path to an image file, calibration uses that image instead of opening a camera device. This is useful for headless testing.
