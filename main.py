"""
The main file of the project : launch the main class
"""

from glfw import get_time, poll_events, set_window_title, window_should_close

from src.display.engine import Engine as DisplayEngine
from src.display.scene import Scene
from src.logger import setup_logger


class SpaceGPS:
    """
    The main class of the project
    """

    def __init__(self):
        self.__display_engine = DisplayEngine(
            640, 480,
            "Space GPS"
        )
        self.__scene = Scene()

        self.__last_time = get_time()
        self.__current_time = get_time()
        self.__num_frames = 0
        # self.__frame_time = 0

    def run(self):
        """
        The main loop
        """
        while not window_should_close(self.__display_engine.window):
            self.__mainloop()

    def __mainloop(self):
        poll_events()

        self.__display_engine.render(self.__scene)

        self.__calculate_fps()

    def __calculate_fps(self):
        self.__current_time = get_time()
        dt = self.__current_time - self.__last_time

        # print fps
        if dt >= 1:
            fps = max(1, int(self.__num_frames / dt))
            set_window_title(self.__display_engine.window, f"Running at {fps} fps")
            self.__last_time = self.__current_time
            self.__num_frames = -1
            # self.__frame_time = 1000 / fps

        self.__num_frames += 1

    def close(self):
        """
        Cleanup the application, must be called at the end of the programm
        """
        self.__display_engine.close()


if __name__ == "__main__":
    setup_logger()
    app = SpaceGPS()
    app.run()
    app.close()
