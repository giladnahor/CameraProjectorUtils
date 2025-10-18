# Spirit Crossing - Quick Start Guide

## 🎃 Welcome to Spirit Crossing!

An interactive Halloween projection game where players must cross a haunted field while avoiding ghosts and danger zones!

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Game
```bash
# Easy way - use the quick start script
./run_game.sh

# Or run directly with Python
PYTHONPATH=. python3 -m game.halloween_game
```

### 3. Play!
- Stand in the **START zone** (bottom, green)
- The game will countdown 3-2-1
- Cross to the **GOAL zone** (top, orange)
- Avoid red danger zones and ghost spirits
- Stand on green safe circles for bonus points!

## 🎮 Game Controls

| Key | Action |
|-----|--------|
| Q or ESC | Quit game |
| R | Reset/Restart game |
| D | Toggle debug info |
| C | Toggle camera feed preview |
| B | Recalibrate background |

## 🎯 Game Rules

### Objective
Cross from the START zone to the GOAL zone without losing all your health!

### Obstacles
- 🔴 **Danger Zones**: Red pulsating areas that drain health
- 👻 **Spirits**: Floating ghosts that damage you on contact
- ⏰ **Time Limit**: 60 seconds to complete (varies by level)

### Bonuses
- 🟢 **Safe Circles**: Glowing green zones that give you points
- ⚡ **Time Bonus**: Extra points for completing quickly

### Difficulty Levels
- **Level 1** (Easy): 3 spirits, 2 danger zones - Perfect for kids!
- **Level 2** (Normal): 4 spirits, 3 danger zones
- **Level 3** (Hard): 5 spirits, 4 danger zones
- **Level 4** (Expert): 6 spirits, 5 danger zones
- **Level 5** (Master): 7 spirits, 6 danger zones

## 📸 Setup for Projection

### Hardware Needed
- Camera (webcam or USB camera)
- Projector or large display
- Open floor space (8ft x 10ft recommended)

### Calibration Steps

1. **Camera-Projector Calibration** (Optional but recommended)
   ```bash
   ./run_game.sh --calibrate
   ```
   - Follow the on-screen instructions
   - Ensures accurate position tracking

2. **Background Calibration** (Automatic)
   - Game will ask you to clear the play area
   - Stand still for 3 seconds
   - Background model is learned automatically

## 🎨 Customization

### Change Difficulty
```bash
./run_game.sh --level 3 --time 90
```

### Change Resolution
```bash
./run_game.sh --width 1280 --height 720
```

### Windowed Mode (for testing)
```bash
./run_game.sh --windowed
```

### Use Different Camera
```bash
./run_game.sh --camera 1
# Or use a video file
./run_game.sh --camera /path/to/video.mp4
```

## 🐛 Troubleshooting

### Camera Not Working
- Check camera is connected: `ls /dev/video*`
- Try different camera index: `--camera 1` or `--camera 2`
- Check permissions: `sudo usermod -a -G video $USER`

### Poor Person Detection
- Ensure good lighting in play area
- Avoid busy/cluttered backgrounds
- Recalibrate background with **B** key

### Low Performance
- Reduce resolution: `--width 1280 --height 720`
- Lower difficulty level: `--level 1`
- Close other applications

### Projection Misalignment
- Run calibration: `./run_game.sh --calibrate`
- Use `--no-projection-mapping` for simple scaling
- Ensure camera sees entire projected area

## 🎉 Tips for Best Experience

### For Kids (Ages 6-12)
- Use **Level 1** or **Level 2**
- Increase time limit: `--time 120`
- Play in teams - one person crosses while others cheer!

### For Parties
- Set up a "high score" board
- Run multiple rounds with increasing difficulty
- Create tournaments with different age groups

### For Halloween Events
- Dim the lights for spooky atmosphere
- Add Halloween music in the background
- Decorate the play area with Halloween props
- Project onto white sheets for best visibility

## 🔧 Advanced Options

### All Command Line Options
```bash
./run_game.sh --help
```

### Run Tests
```bash
PYTHONPATH=. pytest tests/ -v
```

### Custom Game Assets
Edit `game/game_assets.py` to use your own sprites and graphics!

## 📚 More Information

- Full documentation: See `README.md`
- Project architecture: See `PLANNING.md`
- Current tasks: See `TASK.md`

## 🎃 Have Fun and Happy Halloween! 🎃
