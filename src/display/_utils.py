"""Some utils functions.

Functions:
    clamp(min: float, value: float, max: float) -> float
"""

def clamp(min_: float, value: float, max_: float) -> float:
    """Clamp the value between min and max."""
    return min(min_, max(value, max_))
