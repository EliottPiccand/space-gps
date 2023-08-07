"""
Contains all function to create buffers
"""

from typing import Tuple

from vulkan import (
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_SHARING_MODE_EXCLUSIVE,
    VkBufferCreateInfo,
    VkMemoryAllocateInfo,
    vkAllocateMemory,
    vkBindBufferMemory,
    vkCreateBuffer,
    vkGetBufferMemoryRequirements,
    vkGetPhysicalDeviceMemoryProperties,
)

from .hinting import (
    VkBuffer,
    VkBufferUsageFlagBits,
    VkDevice,
    VkDeviceMemory,
    VkDeviceSize,
    VkPhysicalDevice,
)


def _find_memory_type_index(
    physical_device: VkPhysicalDevice,
    supported_memory_indices: int,
    requested_properties: int
) -> int:
    memory_properties = vkGetPhysicalDeviceMemoryProperties(
        physicalDevice = physical_device,
    )

    for i in range(memory_properties.memoryTypeCount):
        supported = supported_memory_indices & (1 << i)
        sufficient = \
            memory_properties.memoryTypes[i].propertyFlags & requested_properties

        if supported and sufficient:
            return i

    return 0

def _allocate_buffer_memory(
    device: VkDevice,
    physical_device: VkPhysicalDevice,
    buffer: VkBuffer
) -> VkDeviceMemory:

    memory_requirements = vkGetBufferMemoryRequirements(
        device = device,
        buffer = buffer
    )

    memory_type_index = _find_memory_type_index(
        physical_device          = physical_device,
        supported_memory_indices = memory_requirements.memoryTypeBits,
        requested_properties     = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT
                                 | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
    )

    alloc_info = VkMemoryAllocateInfo(
        allocationSize  = memory_requirements.size,
        memoryTypeIndex = memory_type_index
    )

    memory = vkAllocateMemory(device, alloc_info, None)

    vkBindBufferMemory(
        device       = device,
        buffer       = buffer,
        memory       = memory,
        memoryOffset = 0
    )

    return memory

def create_buffer(
    device: VkDevice,
    physical_device: VkPhysicalDevice,
    size: VkDeviceSize,
    usage: VkBufferUsageFlagBits
) -> Tuple[VkBuffer, VkDeviceMemory]:
    """Create and allocate a buffer 

    Args:
        device (VkDevice): the device to which the buffer will be linked
        physical_device (VkPhysicalDevice): the physical device to which the buffer will
            be linked
        size (VkDeviceSize): the size of the buffer
        usage (VkBufferUsageFlagBits): a flag describing the usage of the buffer 

    Returns:
        Tuple[VkBuffer, VkDeviceMemory]: the buffer and its memory
    """

    create_info = VkBufferCreateInfo(
        size = size,
        usage = usage,
        sharingMode = VK_SHARING_MODE_EXCLUSIVE
    )

    buffer = vkCreateBuffer(device, create_info, None)

    memory = _allocate_buffer_memory(
        device = device,
        physical_device = physical_device,
        buffer = buffer
    )

    return buffer, memory
