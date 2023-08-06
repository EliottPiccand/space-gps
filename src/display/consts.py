"""
All constants for the display module
"""

from vulkan import VK_MAKE_VERSION


REQUIRED_VULKAN_VERSION: int = VK_MAKE_VERSION(1, 0, 0)

GRAPHICS_ENGINE_NAME = "PyVulkan"
GRAPHICS_ENGINE_VERSION: int = VK_MAKE_VERSION(0, 1, 0)

VERT_SHADER_PATH = "src/display/shaders/vert.spv"
FRAG_SHADER_PATH = "src/display/shaders/frag.spv"

RENDER_FENCE_TIMEOUT = 1_000_000_000 # 1s
