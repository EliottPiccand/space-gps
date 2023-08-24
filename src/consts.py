"""All general constants for the project.

Constants:
    BASE_DIR: Path
    DEBUG: bool
    APPLICATION_VERSION: Tuple[int, int, int]
"""

from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

DEBUG = True
APPLICATION_VERSION = 0, 1, 0
