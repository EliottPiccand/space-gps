"""
All constants for the display module
"""

from vulkan import VK_MAKE_VERSION


REQUIRED_VULKAN_VERSION: int = VK_MAKE_VERSION(1, 0, 0)

GRAPHICS_ENGINE_NAME = "PyVulkan"
GRAPHICS_ENGINE_VERSION: int = VK_MAKE_VERSION(0, 1, 0)
