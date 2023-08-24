"""Classes and functions to use commands.

Classes:
    CommandBufferManager(command_buffer: VkCommandBuffer,
        flags: int | None = None)

Functions:
    create_command_pool(instance: VkInstance, surface: VkSurfaceKHR,
        physical_device: VkPhysicalDevice, device: VkDevice,
        ) -> VkCommandPool
    create_command_buffers(device: VkDevice,
        frame_buffers: list[VkFrameBuffer], command_pool: VkCommandPool,
        ) -> list[VkCommandBuffer]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vulkan import (
    VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    VkCommandBufferAllocateInfo,
    VkCommandBufferBeginInfo,
    VkCommandPoolCreateInfo,
    VkError,
    VkException,
    VkSubmitInfo,
    vkAllocateCommandBuffers,
    vkBeginCommandBuffer,
    vkCreateCommandPool,
    vkEndCommandBuffer,
    vkQueueSubmit,
    vkQueueWaitIdle,
)

from ._queues import find_queue_families
from .errors import CommandRecordError, VulkanCreationError

if TYPE_CHECKING:
    from types import TracebackType

    from .hinting import (
        VkCommandBuffer,
        VkCommandPool,
        VkDevice,
        VkFrameBuffer,
        VkGraphicsQueue,
        VkInstance,
        VkPhysicalDevice,
        VkSurfaceKHR,
    )


def create_command_pool(
    instance: VkInstance,
    surface: VkSurfaceKHR,
    physical_device: VkPhysicalDevice,
    device: VkDevice,
) -> VkCommandPool:
    """Creates and returns the command pool.

    Args:
        instance (VkInstance): The instance to which the command pool
            will be linked.
        surface (VkSurfaceKHR): The surface to which the command pool
            will be linked.
        physical_device (VkPhysicalDevice): The physical device to
            which the command pool will be linked.
        device (VkDevice): The logical device to which the command
            pool will be linked.

    Raises:
        VulkanCreationError: The command pool creation failed.

    Returns:
        VkCommandPool: The created command pool.
    """
    indices = find_queue_families(instance, surface, physical_device)

    create_info = VkCommandPoolCreateInfo(
        queueFamilyIndex = indices.graphics_family,
        flags            = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    )

    try:
        return vkCreateCommandPool(device, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the command pool !")
        raise VulkanCreationError from e

def create_command_buffers(
    device: VkDevice,
    frame_buffers: list[VkFrameBuffer],
    command_pool: VkCommandPool,
) -> list[VkCommandBuffer]:
    """Allocate and returns a command buffer for each frame buffer.

    Args:
        device (VkDevice): The logical device to which the command buffers
            will be linked.
        frame_buffers (list[VkFrameBuffer]): The frame buffers.
        command_pool (VkCommandPool): The command pool to use.

    Raises:
        VulkanCreationError: The command buffer allocation failed.

    Returns:
        list[VkCommandBuffer]: The created command buffers.
    """
    alloc_info = VkCommandBufferAllocateInfo(
        commandPool = command_pool,
        level       = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        commandBufferCount = len(frame_buffers),
    )

    try:
        return vkAllocateCommandBuffers(device, alloc_info)
    except (VkError, VkException) as e:
        logging.exception("Failed to allocate the command buffers !")
        raise VulkanCreationError from e


class CommandBufferManager:
    """A context manager to begin and end VkCommandBuffer."""

    def __init__(
        self,
        command_buffer: VkCommandBuffer,
        flags: int | None = None,
        queue: VkGraphicsQueue = None,
    ):
        self._command_buffer = command_buffer
        self.__flags = flags
        self.__queue = queue

    def __enter__(self):
        begin_info = VkCommandBufferBeginInfo(
            flags = self.__flags,
        )
        try:
            vkBeginCommandBuffer(self._command_buffer, begin_info)
        except (VkError, VkException) as e:
            logging.exception("Failed to begin recording command buffer !")
            raise CommandRecordError from e

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        try:
            vkEndCommandBuffer(self._command_buffer)
        except (VkError, VkException) as e:
            logging.exception("Failed to end recording command buffer !")
            raise CommandRecordError from e

        if self.__queue is not None:
            submit_info = VkSubmitInfo(
                commandBufferCount = 1,
                pCommandBuffers    = [self._command_buffer],
            )

            vkQueueSubmit(
                queue       = self.__queue,
                submitCount = 1,
                pSubmits    = [submit_info],
                fence       = None,
            )

            vkQueueWaitIdle(self.__queue)
