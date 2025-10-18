# Camera-Projector Aligner (CPA) + Spirit Crossing Game

A lightweight Python library to align a camera and projector (or display) via planar homography using a checkerboard pattern, plus an interactive Halloween-themed projection game!

## Features

### Camera-Projector Alignment
- Generate and display a high-contrast checkerboard pattern
- Detect corners with OpenCV and estimate homography with RANSAC
- Save/load calibration to JSON with validation
- Transform camera-space points into projector-space

### Spirit Crossing Game
- **Interactive projection game** using person detection and projection mapping
- **Real-time person segmentation** using background subtraction
- **Halloween-themed gameplay** with ghosts, danger zones, and magic circles
- **Progressive difficulty** with 5 levels
- **Dynamic obstacles** including floating spirits and moving danger zones
- **Placeholder graphics** ready for custom asset integration

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies
- `numpy>=1.24` - Numerical operations
- `opencv-python>=4.8` - Computer vision and person detection
- `pydantic>=2.7` - Data validation
- `pygame>=2.5` - Display and game rendering
- `pytest>=7.4` - Testing framework

## Usage

### Camera-Projector Alignment

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

### Spirit Crossing Game

#### Quick Start

```bash
# Run the game with default settings
python -m game.halloween_game

# Run with specific camera and resolution
python -m game.halloween_game --camera 0 --width 1920 --height 1080

# Run at higher difficulty
python -m game.halloween_game --level 3 --time 90
```

#### Command Line Options

```
--camera CAMERA           Camera device index or video file path (default: 0)
--width WIDTH            Projector width in pixels (default: 1920)
--height HEIGHT          Projector height in pixels (default: 1080)
--level LEVEL            Difficulty level 1-5 (default: 1)
--time TIME              Time limit in seconds (default: 60)
--no-projection-mapping  Disable camera-projector alignment (use direct scaling)
--calibration-file FILE  Path to calibration data file (default: calibration_data.json)
--windowed              Run in windowed mode instead of fullscreen
--calibrate             Run calibration only and exit
```

#### Game Controls

- **Q** or **ESC** - Quit game
- **R** - Reset game
- **D** - Toggle debug information
- **C** - Toggle camera feed overlay
- **B** - Recalibrate background model

#### How to Play: Spirit Crossing

**Objective:** Cross from the START zone (bottom) to the GOAL zone (top) while avoiding obstacles and collecting points!

**Game Elements:**
- 🟢 **START Zone** (Green, bottom 10%): Stand here to begin
- 🟡 **GOAL Zone** (Orange, top 10%): Reach here to win
- 🔴 **Danger Zones** (Red, pulsating): Avoid these moving hazards - they drain your health
- 🟢 **Safe Circles** (Green, glowing): Stand in these to collect points
- 👻 **Spirits** (Ghost sprites): Floating enemies that damage you on contact

**Scoring:**
- Collect safe circles for points
- Reach the goal with time remaining for bonus points
- Higher levels award more points per safe circle

**Difficulty Levels:**
- **Level 1**: 3 spirits, 2 danger zones - Great for kids!
- **Level 2**: 4 spirits, 3 danger zones
- **Level 3**: 5 spirits, 4 danger zones
- **Level 4**: 6 spirits, 5 danger zones - Challenging!
- **Level 5**: 7 spirits, 6 danger zones - Expert mode!

### Python API

```python
from game import HalloweenGame

# Create game instance
game = HalloweenGame(
    camera_source=0,
    projector_resolution=(1920, 1080),
    level=2,
    time_limit=90.0,
    fullscreen=True,
)

# Run calibration (optional, but recommended for projection mapping)
game.initialize_display()
game.calibrate_projection()

# Start the game
game.run()
```

## Setup Guide for Projection Installation

### 1. Hardware Setup
1. Mount projector pointing at floor or wall play area
2. Mount camera with clear view of entire play area
3. Ensure adequate lighting for person detection
4. Test camera feed and projector display

### 2. Calibration
```bash
# First, calibrate the camera-projector alignment
python -m game.halloween_game --calibrate

# The system will:
# 1. Display a checkerboard pattern on the projector
# 2. Capture an image from the camera
# 3. Detect the checkerboard and compute homography
# 4. Save calibration data to calibration_data.json
```

### 3. Background Calibration
When you first start the game, it will:
1. Ask you to clear the play area
2. Capture background for 3 seconds
3. Build a background model for person detection

### 4. Play!
Stand in the START zone to begin. The game will countdown 3-2-1 and start!

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_game_engine.py

# Run with coverage
pytest --cov=game --cov=cpa
```

## Project Structure

```
.
├── cpa/                      # Camera-Projector Aligner package
│   ├── __init__.py
│   ├── aligner.py           # Main aligner class
│   └── patterns.py          # Checkerboard generation
├── game/                     # Halloween game package
│   ├── __init__.py
│   ├── person_detector.py   # Person segmentation using background subtraction
│   ├── game_engine.py       # Core game logic and state management
│   ├── game_renderer.py     # Rendering engine for game graphics
│   ├── game_assets.py       # Placeholder asset generation
│   └── halloween_game.py    # Main game application
├── tests/                    # Unit tests
│   ├── test_aligner.py
│   ├── test_person_detector.py
│   ├── test_game_engine.py
│   └── test_game_assets.py
├── PLANNING.md              # Project architecture and design
├── TASK.md                  # Task tracking
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Customization

### Adding Custom Game Assets

The game currently uses procedurally generated placeholder graphics. To add custom assets:

1. Replace sprite generation in `game/game_assets.py`
2. Load your own images (PNG with transparency)
3. Return them as numpy BGRA arrays

Example:
```python
import cv2

class GameAssets:
    @staticmethod
    def create_spirit_sprite(size=80, color=(200, 200, 255)):
        # Load your custom ghost image
        sprite = cv2.imread('assets/ghost.png', cv2.IMREAD_UNCHANGED)
        # Resize to requested size
        sprite = cv2.resize(sprite, (size, size))
        return sprite
```

### Adjusting Game Parameters

Modify parameters in `game/game_engine.py`:
- Spirit speed and size
- Danger zone behavior
- Safe zone spawn rate
- Health and damage values
- Time limits per level

## Troubleshooting

### Camera Issues
- **Camera not found**: Check camera index with `ls /dev/video*` on Linux
- **Permission denied**: Add user to video group: `sudo usermod -a -G video $USER`
- **Poor detection**: Adjust lighting, try different camera angle

### Projection Mapping
- **Calibration fails**: Ensure checkerboard is fully visible and well-lit
- **Inaccurate mapping**: Recalibrate with `--calibrate` flag
- **No projection mapping**: Use `--no-projection-mapping` for direct coordinate scaling

### Performance
- **Low FPS**: Reduce resolution or lower difficulty level
- **Detection lag**: Adjust `learning_rate` in `PersonDetector` class
- **Memory issues**: Check camera resolution and reduce if needed

## Contributing

This is an educational project demonstrating:
- Computer vision and homography estimation
- Real-time person detection
- Game development with Python
- Interactive projection mapping

Feel free to extend and customize for your own projects!

## License

See LICENSE file for details.

## Notes
- If pygame is not available or a display is not present, pattern display is skipped
- When `camera_source` is a string path to an image file, calibration uses that image instead of opening a camera device (useful for headless testing)
- Person detection uses OpenCV's MOG2 background subtractor for robust segmentation
- Game runs at 60 FPS for smooth animation and responsive gameplay
