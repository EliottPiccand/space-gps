"""The main file.

If this file is executed, the logger will be setup then the program will start.

Classes:
    SpaceGPS()
"""

from glfw import get_time, poll_events, set_window_title, window_should_close

from src.display.engine import Engine as DisplayEngine
from src.logger import setup_logger


class SpaceGPS:
    """The main class of the project.

    Methods:
        run()
        close()
    """

    def __init__(self):
        self.__display_engine = DisplayEngine(
            640, 480,
            "Space GPS",
        )

        self.__last_time = get_time()
        self.__current_time = get_time()
        self.__num_frames = 0

    def run(self) -> None:
        """The main loop."""
        while not window_should_close(self.__display_engine.window):
            self.__mainloop()

    def __mainloop(self) -> None:
        poll_events()

        self.__display_engine.render()

        self.__calculate_fps()

    def __calculate_fps(self) -> None:
        self.__current_time = get_time()
        dt = self.__current_time - self.__last_time

        # Show fps on window title
        if dt >= 1:
            fps = max(1, int(self.__num_frames / dt))
            set_window_title(
                self.__display_engine.window,
                f"{self.__display_engine.title} ({fps} fps)",
            )
            self.__last_time = self.__current_time
            self.__num_frames = -1

        self.__num_frames += 1

    def close(self) -> None:
        """Cleanup the application.

        Must be called at the end of the program.
        """
        self.__display_engine.cleanup()

if __name__ == "__main__":
    setup_logger()
    app = SpaceGPS()
    app.run()
    app.close()
