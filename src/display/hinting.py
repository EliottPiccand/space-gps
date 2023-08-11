"""
Hinting for vulkan binding types
"""

from typing import Any, Literal, TypeAlias

from _cffi_backend import ( # pylint: disable=no-name-in-module
    __CDataOwn,
    _CDataBase,
    buffer,
)
from vulkan import VK_FALSE, VK_TRUE


VoidPointer: TypeAlias = buffer

Window: TypeAlias = Any # Ugly but I dont't know how to do it properly

VkInstance: TypeAlias = _CDataBase
VkDebugReportCallbackEXT: TypeAlias = _CDataBase
VkPhysicalDevice: TypeAlias = _CDataBase
VkDevice: TypeAlias = _CDataBase
VkGraphicsQueue: TypeAlias = _CDataBase
VkPresentQueue: TypeAlias = _CDataBase
VkSurface: TypeAlias = _CDataBase
VkSurfaceCapabilitiesKHR: TypeAlias = __CDataOwn
VkSurfaceFormatsKHR: TypeAlias = __CDataOwn
VkSurfaceFormatKHR: TypeAlias = _CDataBase
VkPresentModeKHR: TypeAlias = __CDataOwn
VkSwapchainKHR: TypeAlias = _CDataBase
VkImage: TypeAlias = __CDataOwn
VkImageView: TypeAlias = _CDataBase
VkShaderModule: TypeAlias = _CDataBase
VkRenderPass: TypeAlias = _CDataBase
VkPipelineLayout: TypeAlias = _CDataBase
VkPipeline: TypeAlias = _CDataBase
VkFrameBuffer: TypeAlias = _CDataBase
VkCommandPool: TypeAlias = _CDataBase
VkCommandBuffer: TypeAlias = _CDataBase
VkSemaphore: TypeAlias = _CDataBase
VkFence: TypeAlias = _CDataBase
VkRenderPassBeginInfoStruct: TypeAlias = __CDataOwn
VkSubpassContents: TypeAlias = int
VkMemoryPropertyFlags: TypeAlias = int
VkBuffer: TypeAlias = _CDataBase
VkDeviceMemory: TypeAlias = _CDataBase
VkBufferUsageFlagBits: TypeAlias = int
VkDeviceSize: TypeAlias = int
VkSurfaceTransformFlagBitsKHR: TypeAlias = int
VkDescriptorType: TypeAlias = int
VkShaderStageFlags: TypeAlias = int
VkDescriptorSetLayout: TypeAlias = _CDataBase
VkDescriptorPool: TypeAlias = _CDataBase
VkDescriptorSet: TypeAlias = _CDataBase

VkBool: TypeAlias = Literal[VK_TRUE] | Literal[VK_FALSE]
