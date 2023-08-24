"""Hintings for vulkan binding and GLFW types.

TypesAlias:
    VoidPointer

    GLFWWindow

    VkInstance
    VkDebugUtilsMessengerEXT
    VkDebugUtilsMessageSeverityFlagBitsEXT
    VkDebugUtilsMessageTypeFlagsEXT
    VkDebugUtilsMessengerCallbackDataEXT
    VkPhysicalDevice
    VkDevice
    VkGraphicsQueue
    VkPresentQueue
    VkSurfaceKHR
    VkSurfaceCapabilitiesKHR
    VkSurfaceFormatKHR
    VkPresentModeKHR
    VkSwapchainKHR
    VkImage
    VkFormat
    VkImageView
    VkShaderModule
    VkPipelineLayout
    VkRenderPass
    VkPipeline
    VkFrameBuffer
    VkCommandPool
    VkCommandBuffer
    VkSemaphore
    VkFence
    VkBuffer
    VkMemoryPropertyFlags
    VkDeviceMemory
    VkBufferUsageFlags
"""

from typing import TypeAlias

from _cffi_backend import (  # pylint: disable=no-name-in-module
    __CDataOwn,
    _CDataBase,
    buffer,
)
from glfw import _GLFWwindow

VoidPointer: TypeAlias = buffer | _CDataBase

# NOTE: Supposed to be glfw.LP__GLFWwindow but it is not importable
GLFWWindow: TypeAlias = _GLFWwindow

VkInstance: TypeAlias = _CDataBase
VkDebugUtilsMessengerEXT: TypeAlias = _CDataBase
VkDebugUtilsMessageSeverityFlagBitsEXT: TypeAlias = int
VkDebugUtilsMessageTypeFlagsEXT: TypeAlias = int
VkDebugUtilsMessengerCallbackDataEXT: TypeAlias = _CDataBase
VkPhysicalDevice: TypeAlias = _CDataBase
VkDevice: TypeAlias = _CDataBase
VkGraphicsQueue: TypeAlias = _CDataBase
VkPresentQueue: TypeAlias = _CDataBase
VkSurfaceKHR: TypeAlias = _CDataBase
VkSurfaceCapabilitiesKHR: TypeAlias = __CDataOwn
VkSurfaceFormatKHR: TypeAlias = _CDataBase
VkPresentModeKHR: TypeAlias = __CDataOwn
VkSwapchainKHR: TypeAlias = _CDataBase
VkImage: TypeAlias = __CDataOwn
VkFormat: TypeAlias = int
VkImageView: TypeAlias = _CDataBase
VkShaderModule: TypeAlias = _CDataBase
VkPipelineLayout: TypeAlias = _CDataBase
VkRenderPass: TypeAlias = _CDataBase
VkPipeline: TypeAlias = _CDataBase
VkFrameBuffer: TypeAlias = _CDataBase
VkCommandPool: TypeAlias = _CDataBase
VkCommandBuffer: TypeAlias = _CDataBase
VkSemaphore: TypeAlias = _CDataBase
VkFence: TypeAlias = _CDataBase
VkBuffer: TypeAlias = _CDataBase
VkMemoryPropertyFlags: TypeAlias = int
VkDeviceMemory: TypeAlias = _CDataBase
VkBufferUsageFlags: TypeAlias = int
# VkRenderPassBeginInfoStruct: TypeAlias = __CDataOwn
# VkSubpassContents: TypeAlias = int
# VkBufferUsageFlagBits: TypeAlias = int
# VkDeviceSize: TypeAlias = int
# VkSurfaceTransformFlagBitsKHR: TypeAlias = int
# VkDescriptorType: TypeAlias = int
# VkShaderStageFlags: TypeAlias = int
# VkDescriptorSetLayout: TypeAlias = _CDataBase
# VkDescriptorPool: TypeAlias = _CDataBase
# VkDescriptorSet: TypeAlias = _CDataBase
# VkImageTiling: TypeAlias = None
# VkImageUsageFlags: TypeAlias = None
# VkImageLayout: TypeAlias = None
# VkColorSpaceKHR: TypeAlias = None

# VkSampler: TypeAlias = None
