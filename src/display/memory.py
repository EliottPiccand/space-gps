"""
Contains all function to create buffers
"""

from typing import Tuple

from vulkan import (
    VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
    VK_SHARING_MODE_EXCLUSIVE,
    VkBufferCopy,
    VkBufferCreateInfo,
    VkMemoryAllocateInfo,
    vkAllocateMemory,
    vkBindBufferMemory,
    vkBindImageMemory,
    vkCmdCopyBuffer,
    vkCreateBuffer,
    vkGetBufferMemoryRequirements,
    vkGetImageMemoryRequirements,
    vkGetPhysicalDeviceMemoryProperties,
    vkResetCommandBuffer,
)

from .commands import SimpleCommandBufferManager
from .hinting import (
    VkBuffer,
    VkBufferUsageFlagBits,
    VkCommandBuffer,
    VkDevice,
    VkDeviceMemory,
    VkDeviceSize,
    VkGraphicsQueue,
    VkImage,
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
    buffer: VkBuffer,
    requested_properties: int
) -> VkDeviceMemory:

    memory_requirements = vkGetBufferMemoryRequirements(
        device = device,
        buffer = buffer
    )

    memory_type_index = _find_memory_type_index(
        physical_device          = physical_device,
        supported_memory_indices = memory_requirements.memoryTypeBits,
        requested_properties     = requested_properties
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
    usage: VkBufferUsageFlagBits,
    requested_properties: int
) -> Tuple[VkBuffer, VkDeviceMemory]:
    """Create and allocate a buffer 

    Args:
        device (VkDevice): the device to which the buffer will be linked
        physical_device (VkPhysicalDevice): the physical device to which the buffer will
            be linked
        size (VkDeviceSize): the size of the buffer
        usage (VkBufferUsageFlagBits): a flag describing the usage of the buffer
        requested_properties (int): a flag describing the type of memory requested

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
        device               = device,
        physical_device      = physical_device,
        buffer               = buffer,
        requested_properties = requested_properties
    )

    return buffer, memory

def copy_buffer(
    src:VkBuffer,
    dst: VkBuffer,
    size: int,
    queue: VkGraphicsQueue,
    command_buffer: VkCommandBuffer
):
    """Copy the src buffer content to the dst buffer using the given queue and command
    pool

    Args:
        src (VkBuffer): the source buffer
        dst (VkBuffer): the destination buffer
        size (int): the size of the buffer
        queue (VkGraphicsQueue): the queue to use
        command_buffer (VkCommandBuffer): the command pool to use
    """
    vkResetCommandBuffer(
        commandBuffer = command_buffer,
        flags         = 0
    )

    with SimpleCommandBufferManager(
        command_buffer,
        queue,
        VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT
    ):
        copy_region = VkBufferCopy(
            srcOffset = 0,
            dstOffset = 0,
            size      = size
        )

        vkCmdCopyBuffer(
            commandBuffer = command_buffer,
            srcBuffer     = src,
            dstBuffer     = dst,
            regionCount   = 1,
            pRegions      = [copy_region]
        )

def allocate_image_memory(
    device: VkDevice,
    physical_device: VkPhysicalDevice,
    image: VkImage,
    memory_properties: int
) -> VkDeviceMemory:
    """Allocate and bind memory for the given image

    Args:
        device (VkDevice): the device to which the image is linked
        physical_device (VkPhysicalDevice): the physical device used to create the
            device
        image (VkImage): the image
        memory_properties (int): the properties needed

    Returns:
        VkDeviceMemory: the allocated memory
    """

    memory_requirements = vkGetImageMemoryRequirements(device, image)
    alloc_info = VkMemoryAllocateInfo(
        allocationSize  = memory_requirements.size,
        memoryTypeIndex = _find_memory_type_index(
            physical_device = physical_device,
            supported_memory_indices = memory_requirements.memoryTypeBits,
            requested_properties = memory_properties
        )
    )

    image_memory = vkAllocateMemory(device, alloc_info, None)

    vkBindImageMemory(
        device       = device,
        image        = image,
        memory       = image_memory,
        memoryOffset = 0
    )

    return image_memory
