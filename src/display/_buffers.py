"""Functions related to buffers.

Functions:
    create_buffer(physical_device: VkPhysicalDevice, device: VkDevice,
        size: int) -> tuple[VkBuffer, VkDeviceMemory]

    copy_buffer(device: VkDevice, queue: VkGraphicsQueue,
        command_pool: VkCommandPool, src: VkBuffer, dst: VkBuffer,
        size: int) -> None
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vulkan import (
    VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
    VK_SHARING_MODE_EXCLUSIVE,
    VkBufferCopy,
    VkBufferCreateInfo,
    VkCommandBufferAllocateInfo,
    VkError,
    VkException,
    VkMemoryAllocateInfo,
    vkAllocateCommandBuffers,
    vkAllocateMemory,
    vkBindBufferMemory,
    vkCmdCopyBuffer,
    vkCreateBuffer,
    vkFreeCommandBuffers,
    vkGetBufferMemoryRequirements,
    vkGetPhysicalDeviceMemoryProperties,
)

from ._commands import CommandBufferManager
from .errors import NoValidMemoryTypeError, VulkanCreationError

if TYPE_CHECKING:
    from .hinting import (
        VkBuffer,
        VkBufferUsageFlags,
        VkCommandPool,
        VkDevice,
        VkDeviceMemory,
        VkGraphicsQueue,
        VkMemoryPropertyFlags,
        VkPhysicalDevice,
    )

def _find_memory_type(
    physical_device: VkPhysicalDevice,
    type_filter: int,
    properties: VkMemoryPropertyFlags,
) -> int:
    mem_properties = vkGetPhysicalDeviceMemoryProperties(physical_device)

    for i in range(mem_properties.memoryTypeCount):
        property_flags = mem_properties.memoryTypes[i].propertyFlags

        if (type_filter & (1 << i)
        and (property_flags & properties == properties)):
            return i

    logging.error("Failed to find a valid memory type !")
    raise NoValidMemoryTypeError

def create_buffer(
    physical_device: VkPhysicalDevice,
    device: VkDevice,
    size: int,
    usage: VkBufferUsageFlags,
    properties: VkMemoryPropertyFlags,
) -> tuple[VkBuffer, VkDeviceMemory]:
    """Creates and returns a buffer.

    Create the buffer, allocate the memory then bind it.

    Args:
        physical_device (VkPhysicalDevice): The physical device to use.
        device (VkDevice): The logical device to which the buffer will
            be linked.
        size (int): The required size of the buffer.
        usage (VkBufferUsageFlags): The flags describing the buffer
            usage.
        properties (VkMemoryPropertyFlags): The flags describing the
            buffer required properties

    Raises:
        VulkanCreationError: The buffer creation failed or its memory
            allocation failed.

    Returns:
        tuple[VkBuffer, VkDeviceMemory]: The created buffer and its
            memory.
    """
    create_info = VkBufferCreateInfo(
        size        = size,
        usage       = usage,
        sharingMode = VK_SHARING_MODE_EXCLUSIVE,
    )

    try:
        buffer = vkCreateBuffer(device, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the buffer !")
        raise VulkanCreationError from e

    mem_requirements = vkGetBufferMemoryRequirements(device, buffer)
    memory_type_index = _find_memory_type(
        physical_device = physical_device,
        type_filter     = mem_requirements.memoryTypeBits,
        properties      = properties,
    )

    alloc_info = VkMemoryAllocateInfo(
        allocationSize  = mem_requirements.size,
        memoryTypeIndex = memory_type_index,
    )

    try:
        buffer_memory = vkAllocateMemory(device, alloc_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to allocate the buffer memory !")
        raise VulkanCreationError from e

    vkBindBufferMemory(device, buffer, buffer_memory, 0)

    return buffer, buffer_memory

def copy_buffer(
    device: VkDevice,
    queue: VkGraphicsQueue,
    command_pool: VkCommandPool,
    src: VkBuffer,
    dst: VkBuffer,
    size: int,
) -> None:
    """Copy the src buffer value to dst.

    Args:
        device (VkDevice): The device to which de buffers are linked.
        queue (VkGraphicsQueue): The queue to use.
        command_pool (VkCommandPool): The command pool to use.
        src (VkBuffer): The source buffer.
        dst (VkBuffer): The destination buffer.
        size (int): The size of the value to copy.
    """
    alloc_info = VkCommandBufferAllocateInfo(
        level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        commandPool        = command_pool,
        commandBufferCount = 1,
    )

    command_buffer = vkAllocateCommandBuffers(device, alloc_info)[0]

    with CommandBufferManager(
        command_buffer = command_buffer,
        flags          = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
        queue          = queue,
    ):
        copy_region = VkBufferCopy(
            size = size,
        )

        vkCmdCopyBuffer(
            commandBuffer = command_buffer,
            srcBuffer     = src,
            dstBuffer     = dst,
            regionCount   = 1,
            pRegions      = [copy_region],
        )

    vkFreeCommandBuffers(
        device             = device,
        commandPool        = command_pool,
        commandBufferCount = 1,
        pCommandBuffers    = [command_buffer],
    )
