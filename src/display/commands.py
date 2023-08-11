"""
Contain all functions to create the command pool
"""

import logging
from typing import Optional

from vulkan import (
    VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    VkCommandBufferAllocateInfo,
    VkCommandBufferBeginInfo,
    VkCommandPoolCreateInfo,
    VkError,
    VkException,
    vkAllocateCommandBuffers,
    vkBeginCommandBuffer,
    vkCmdBeginRenderPass,
    vkCmdEndRenderPass,
    vkCreateCommandPool,
    vkEndCommandBuffer,
)

from .hinting import (
    VkCommandBuffer,
    VkCommandPool,
    VkDevice,
    VkRenderPassBeginInfoStruct,
    VkSubpassContents,
)
from .queue_families import QueueFamilyIndices


def make_command_pool(
    device: VkDevice,
    indices: QueueFamilyIndices
) -> Optional[VkCommandPool]:
    """Create the command pool

    Args:
        device (VkDevice): the device to which the command pool will be linked
        indices (QueueFamilyIndices): its queues indices

    Returns:
        Optional[VkCommandPool]: The created command pool. Might be None if creation
            failed.
    """

    create_info = VkCommandPoolCreateInfo(
        flags            = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
        queueFamilyIndex = indices.graphics
    )

    try:
        return vkCreateCommandPool(device, create_info, None)
    except (VkError, VkException):
        logging.error("Failed to create the command buffer")
        return None

def make_command_buffer(
    device: VkDevice,
    command_pool: VkCommandPool
) -> Optional[VkCommandBuffer]:
    """Allocate a command buffer

    Args:
        device (VkDevice): the device to which the command buffer will be linked 
        command_pool (VkCommandPool): the command pool used

    Returns:
        Optional[VkCommandPool]: The created command pool. Might be None if creation
            failed.
    """

    allocate_info = VkCommandBufferAllocateInfo(
        commandPool        = command_pool,
        level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        commandBufferCount = 1
    )

    try:
        return vkAllocateCommandBuffers(device, allocate_info, None)[0]
    except (VkError, VkException):
        logging.error("Failed to allocate the command buffer")
        return None

class CommandBufferManager:
    """
    A context manager to begin and end VkCommandBuffer
    """

    def __init__(self, command_buffer: VkCommandBuffer, flags: int = None):
        self.__command_buffer = command_buffer
        self.__flags = flags

    def __enter__(self):
        begin_info = VkCommandBufferBeginInfo(
            flags = self.__flags
        )
        try:
            vkBeginCommandBuffer(self.__command_buffer, begin_info)
        except (VkError, VkException):
            logging.error("Failed to begin recording command buffer")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            vkEndCommandBuffer(self.__command_buffer)
        except (VkError, VkException):
            logging.error("Failed to end recording command buffer")

class RenderPassManager:
    """
    A context manager to begin and end VkRenderPass
    """

    def __init__(
        self,
        command_buffer: VkCommandBuffer,
        render_pass_begin_info: VkRenderPassBeginInfoStruct,
        contents: VkSubpassContents
    ):
        self.__command_buffer = command_buffer
        self.__render_pass_begin_info = render_pass_begin_info
        self.__contents = contents

    def __enter__(self):
        vkCmdBeginRenderPass(
            self.__command_buffer,
            self.__render_pass_begin_info,
            self.__contents
        )

    def __exit__(self, exc_type, exc_value, exc_traceback):
        vkCmdEndRenderPass(self.__command_buffer)
