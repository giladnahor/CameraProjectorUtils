"""
Main Halloween projection game application.

This module integrates person detection, game engine, rendering,
and projection mapping for the Spirit Crossing game.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

try:
    import pygame
except ImportError:
    pygame = None

from cpa import CameraProjectorAligner
from .game_engine import GameEngine, GameState
from .game_renderer import GameRenderer
from .person_detector import PersonDetector


class HalloweenGame:
    """
    Main Halloween interactive projection game.

    Integrates person detection, game logic, rendering, and projection.
    """

    def __init__(
        self,
        camera_source: int | str = 0,
        projector_resolution: Tuple[int, int] = (1920, 1080),
        use_projection_mapping: bool = True,
        calibration_file: str = "calibration_data.json",
        level: int = 1,
        time_limit: float = 60.0,
        fullscreen: bool = True,
    ):
        """
        Initialize the Halloween game.

        Args:
            camera_source (int | str): Camera device index or video file path.
            projector_resolution (tuple): (width, height) of projector.
            use_projection_mapping (bool): Whether to use CPA projection mapping.
            calibration_file (str): Path to calibration data file.
            level (int): Game difficulty level (1-5).
            time_limit (float): Time limit in seconds.
            fullscreen (bool): Whether to display in fullscreen mode.
        """
        self.camera_source = camera_source
        self.projector_resolution = projector_resolution
        self.use_projection_mapping = use_projection_mapping
        self.level = level
        self.fullscreen = fullscreen

        # Initialize person detector
        self.person_detector = PersonDetector(camera_source=camera_source)

        # Initialize game engine
        self.engine = GameEngine(
            field_width=projector_resolution[0],
            field_height=projector_resolution[1],
            level=level,
            time_limit=time_limit,
        )

        # Initialize renderer
        self.renderer = GameRenderer(
            width=projector_resolution[0],
            height=projector_resolution[1],
        )

        # Initialize camera-projector aligner if using projection mapping
        self.aligner: Optional[CameraProjectorAligner] = None
        if use_projection_mapping:
            self.aligner = CameraProjectorAligner(
                camera_source=camera_source,
                projector_resolution=projector_resolution,
                pattern_size=(7, 9),  # Standard checkerboard size
                calib_file_path=calibration_file,
            )

        # Pygame display for projection
        self.screen = None
        self._running = False
        self._show_debug = False
        self._show_camera_feed = False

    def initialize_display(self) -> None:
        """
        Initialize pygame display for projection.

        Raises:
            RuntimeError: If pygame is not available.
        """
        if pygame is None:
            raise RuntimeError(
                "Pygame is required for display. Install with: pip install pygame"
            )

        pygame.init()

        if self.fullscreen:
            self.screen = pygame.display.set_mode(
                self.projector_resolution, pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(self.projector_resolution)

        pygame.display.set_caption("Spirit Crossing - Halloween Game")

    def calibrate_projection(self) -> None:
        """
        Run the camera-projector calibration procedure.

        This should be called before starting the game if projection mapping is enabled.
        """
        if not self.use_projection_mapping or self.aligner is None:
            print("Projection mapping is disabled, skipping calibration.")
            return

        print("Starting camera-projector calibration...")
        print("Please ensure the calibration checkerboard is visible to the camera.")
        print("Press any key when ready...")

        try:
            self.aligner.calibrate()
            print("Calibration successful!")
        except RuntimeError as e:
            print(f"Calibration failed: {e}")
            print("Game will run without projection mapping.")
            self.use_projection_mapping = False

    def calibrate_background(self) -> None:
        """
        Calibrate the background model for person detection.

        The play area should be empty during this process.
        """
        print("Calibrating background model...")
        print("Please ensure the play area is empty for 3 seconds...")
        time.sleep(1)

        self.person_detector.start()
        self.person_detector.calibrate_background(num_frames=90)  # 3 seconds at 30fps
        print("Background calibration complete!")

    def run(self) -> None:
        """
        Run the main game loop.
        """
        self._running = True

        try:
            # Initialize display
            self.initialize_display()

            # Start person detector
            self.person_detector.start()

            # Calibrate background
            print("\n" + "=" * 50)
            print("BACKGROUND CALIBRATION")
            print("=" * 50)
            self.calibrate_background()

            # Wait for player to enter start zone
            print("\n" + "=" * 50)
            print("GAME READY")
            print("=" * 50)
            print("Stand in the START zone (bottom) to begin!")
            print("\nControls:")
            print("  Q - Quit")
            print("  R - Reset game")
            print("  D - Toggle debug info")
            print("  C - Toggle camera feed")
            print("=" * 50 + "\n")

            # Main game loop
            clock = pygame.time.Clock() if pygame else None
            self._game_loop(clock)

        finally:
            self.cleanup()

    def _game_loop(self, clock) -> None:
        """
        Main game loop.

        Args:
            clock: Pygame clock for frame rate control.
        """
        while self._running:
            # Handle events
            self._handle_events()

            # Detect person
            camera_frame, persons = self.person_detector.detect_person()

            # Get player position
            player_position_cam = None
            if persons:
                # Use largest detected person as player
                player_position_cam = persons[0].centroid

            # Transform position to projector space if using projection mapping
            player_position_proj = None
            if player_position_cam is not None:
                if self.use_projection_mapping and self.aligner is not None:
                    try:
                        # Transform camera coordinates to projector coordinates
                        pts = np.array([player_position_cam], dtype=np.float32)
                        transformed = self.aligner.transform_camera_to_projector(pts)
                        player_position_proj = tuple(transformed[0])
                    except Exception as e:
                        print(f"Transform error: {e}")
                        player_position_proj = None
                else:
                    # No projection mapping, use camera coordinates directly
                    # Scale to projector resolution
                    cam_w, cam_h = self.person_detector.get_frame_dimensions()
                    proj_w, proj_h = self.projector_resolution
                    x = (player_position_cam[0] / cam_w) * proj_w
                    y = (player_position_cam[1] / cam_h) * proj_h
                    player_position_proj = (x, y)

            # Check for game start trigger (player in start zone)
            if self.engine.state == GameState.READY and player_position_proj is not None:
                px, py = player_position_proj
                # Check if player is in start zone
                if py > self.projector_resolution[1] - self.engine.start_zone_height:
                    self.engine.start_countdown()

            # Update game engine
            self.engine.update(player_position_proj)

            # Check for game reset
            if self.engine.state in [GameState.WIN, GameState.LOSE]:
                # Auto-reset after 5 seconds
                if not hasattr(self, "_end_screen_time"):
                    self._end_screen_time = time.time()
                elif time.time() - self._end_screen_time > 5.0:
                    self.engine.reset()
                    delattr(self, "_end_screen_time")
            else:
                if hasattr(self, "_end_screen_time"):
                    delattr(self, "_end_screen_time")

            # Render game frame
            game_frame = self.renderer.render_frame(self.engine, show_debug=self._show_debug)

            # Display camera feed overlay if enabled
            if self._show_camera_feed and camera_frame is not None:
                self._overlay_camera_feed(game_frame, camera_frame)

            # Display frame
            self._display_frame(game_frame)

            # Control frame rate
            if clock:
                clock.tick(60)  # 60 FPS

    def _handle_events(self) -> None:
        """
        Handle pygame events and keyboard input.
        """
        if pygame is None:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    self._running = False
                elif event.key == pygame.K_r:
                    self.engine.reset()
                    print("Game reset!")
                elif event.key == pygame.K_d:
                    self._show_debug = not self._show_debug
                    print(f"Debug mode: {'ON' if self._show_debug else 'OFF'}")
                elif event.key == pygame.K_c:
                    self._show_camera_feed = not self._show_camera_feed
                    print(f"Camera feed: {'ON' if self._show_camera_feed else 'OFF'}")
                elif event.key == pygame.K_b:
                    # Recalibrate background
                    print("Recalibrating background...")
                    self.person_detector.reset_background_model()
                    self.person_detector.calibrate_background(num_frames=60)
                    print("Background recalibrated!")

    def _overlay_camera_feed(
        self, game_frame: np.ndarray, camera_frame: np.ndarray
    ) -> None:
        """
        Overlay a small camera feed preview on the game frame.

        Args:
            game_frame (np.ndarray): Game frame to overlay onto.
            camera_frame (np.ndarray): Camera frame to display.
        """
        # Resize camera frame to small preview
        preview_width = 320
        preview_height = 240
        camera_preview = cv2.resize(camera_frame, (preview_width, preview_height))

        # Position in bottom-right corner
        x = game_frame.shape[1] - preview_width - 10
        y = game_frame.shape[0] - preview_height - 10

        # Add border
        cv2.rectangle(
            game_frame,
            (x - 2, y - 2),
            (x + preview_width + 2, y + preview_height + 2),
            (255, 255, 255),
            2,
        )

        # Copy preview
        game_frame[y : y + preview_height, x : x + preview_width] = camera_preview

    def _display_frame(self, frame: np.ndarray) -> None:
        """
        Display a frame on the pygame screen.

        Args:
            frame (np.ndarray): BGR frame to display.
        """
        if pygame is None or self.screen is None:
            return

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to pygame surface
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))

        # Blit to screen
        self.screen.blit(frame_surface, (0, 0))
        pygame.display.flip()

    def cleanup(self) -> None:
        """
        Clean up resources and close the game.
        """
        print("\nCleaning up...")
        self.person_detector.stop()

        if pygame:
            pygame.quit()

        print("Game closed. Thanks for playing!")


def main():
    """
    Main entry point for the Halloween game application.
    """
    parser = argparse.ArgumentParser(
        description="Spirit Crossing - Halloween Interactive Projection Game"
    )
    parser.add_argument(
        "--camera",
        type=str,
        default="0",
        help="Camera device index or video file path (default: 0)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1920,
        help="Projector width in pixels (default: 1920)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1080,
        help="Projector height in pixels (default: 1080)",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help="Difficulty level 1-5 (default: 1)",
    )
    parser.add_argument(
        "--time",
        type=float,
        default=60.0,
        help="Time limit in seconds (default: 60)",
    )
    parser.add_argument(
        "--no-projection-mapping",
        action="store_true",
        help="Disable camera-projector alignment (use direct scaling)",
    )
    parser.add_argument(
        "--calibration-file",
        type=str,
        default="calibration_data.json",
        help="Path to calibration data file",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Run in windowed mode instead of fullscreen",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run calibration only and exit",
    )

    args = parser.parse_args()

    # Convert camera argument to int if it's a digit
    camera_source = int(args.camera) if args.camera.isdigit() else args.camera

    # Create game instance
    game = HalloweenGame(
        camera_source=camera_source,
        projector_resolution=(args.width, args.height),
        use_projection_mapping=not args.no_projection_mapping,
        calibration_file=args.calibration_file,
        level=args.level,
        time_limit=args.time,
        fullscreen=not args.windowed,
    )

    # Run calibration only if requested
    if args.calibrate:
        game.initialize_display()
        game.calibrate_projection()
        game.cleanup()
        return

    # Run the game
    try:
        game.run()
    except KeyboardInterrupt:
        print("\n\nGame interrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
