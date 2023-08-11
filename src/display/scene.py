"""
Contains the Scene class used to store models to render 
"""

from numpy import arange, array, float32


class Scene:
    """
    Used to store models to render 
    """

    def __init__(self):

        self.triangle_positions = []
        self.square_positions = []
        self.pentagon_positions = []

        for y in arange(-1, 1, 0.2):
            self.triangle_positions.append(
                array([-0.6, y, 0], dtype=float32)
            )

            self.square_positions.append(
                array([0, y, 0], dtype=float32)
            )

            self.pentagon_positions.append(
                array([0.6, y, 0], dtype=float32)
            )
