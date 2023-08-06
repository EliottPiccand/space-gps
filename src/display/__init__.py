"""
Fix the vulkan binding errors
"""

import collections
from _collections_abc import Iterable

collections.Iterable = Iterable
