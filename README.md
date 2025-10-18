# Camera-Projector Aligner (CPA)

A lightweight Python library to align a camera and projector (or display) via planar homography using a checkerboard pattern.

## Features
- Generate and display a high-contrast checkerboard pattern
- Detect corners with OpenCV and estimate homography with RANSAC
- Save/load calibration to JSON with validation
- Transform camera-space points into projector-space

## Halloween Interactive Projection Game (New)

This repo now includes a simple Halloween-themed interactive projection game built on top of CPA. It:

- Uses PCA-based or MOG2 background subtraction to segment a player from the camera feed
- Maps the player's centroid from camera pixels to projector pixels via the calibrated homography
- Renders a "haunted field" with alternating safe pumpkin patches and dangerous ghost fog strips
- Adds drifting spirits (placeholder graphics) which count as danger on contact
- Shows victory/failure overlays

### Run the Game (example)

```python
from cpa import CameraProjectorAligner
from game.engine import GameEngine, GameConfig

aligner = CameraProjectorAligner(camera_source=0, projector_resolution=(1280, 720), pattern_size=(7, 10))

# Calibrate once (or load from existing calibration_data.json)
# H = aligner.calibrate()

engine = GameEngine.build_default(aligner, GameConfig(camera_source=0, projector_resolution=(1280, 720), use_pca=True))

# Warmup PCA background for a few seconds if using PCA
engine.warmup_background(duration_s=3.0)

while True:
    overlay = engine.step()
    if overlay is None:
        break
    # Display the overlay using OpenCV for development; in production, draw via projector pipeline
    import cv2
    cv2.imshow("Haunted Field Overlay", overlay)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break
```

Note: For real projection, draw `overlay` to the projector surface instead of an on-screen window.

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
