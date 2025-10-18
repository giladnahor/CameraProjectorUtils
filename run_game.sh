#!/bin/bash
# Quick start script for Spirit Crossing Halloween Game

echo "╔════════════════════════════════════════════════════════╗"
echo "║     🎃 SPIRIT CROSSING - Halloween Projection Game 🎃  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if dependencies are installed
if ! python3 -c "import cv2, pygame, numpy, pydantic" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip3 install -q -r requirements.txt
    echo "✅ Dependencies installed!"
    echo ""
fi

# Parse command line arguments
ARGS=""
if [ "$#" -eq 0 ]; then
    echo "🎮 Starting game with default settings..."
    echo "   - Camera: 0"
    echo "   - Resolution: 1920x1080"
    echo "   - Level: 1"
    echo "   - Time: 60 seconds"
    echo ""
    echo "💡 Tip: Run './run_game.sh --help' for more options"
    echo ""
else
    ARGS="$@"
fi

# Run the game
PYTHONPATH=. python3 -m game.halloween_game $ARGS
