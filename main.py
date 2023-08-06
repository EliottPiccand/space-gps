"""
The main file of the project : launch the main class
"""

from src.logger import setup_logger
from src.display.engine import Engine as DisplayEngine


class SpaceGPS:
    """
    The main class of the project
    """

    def __init__(self):
        self.__display_engine = DisplayEngine(
            640, 480,
            "Space GPS"
        )

    def __del__(self):
        self.__display_engine.close()


if __name__ == "__main__":
    setup_logger()
    SpaceGPS()
