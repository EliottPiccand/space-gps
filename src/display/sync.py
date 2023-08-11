"""
Contain all functions to create semaphores and fences to syncronize the GPU and the CPU
"""

import logging
from typing import Optional

from vulkan import (
    VK_FENCE_CREATE_SIGNALED_BIT,
    VkError,
    VkException,
    VkFenceCreateInfo,
    VkSemaphoreCreateInfo,
    vkCreateFence,
    vkCreateSemaphore,
)

from .hinting import VkDevice, VkFence, VkSemaphore


def make_semaphore(device: VkDevice) -> Optional[VkSemaphore]:
    """Create a semaphore

    Args:
        device (VkDevice): the device to which the semaphore will be linked.

    Returns:
        Optional[VkSemaphore]: the created semaphore. Might be None if the creation
            failed.
    """

    create_info = VkSemaphoreCreateInfo()

    try:
        return vkCreateSemaphore(device, create_info, None)
    except (VkError, VkException):
        logging.error("Failed to create the semaphore")
        return None

def make_fence(device: VkDevice) -> Optional[VkFence]:
    """Create a fence

    Args:
        device (VkDevice): the device to which the fence will be linked.

    Returns:
        Optional[VkFence]: the created fence. Might be None if the creation failed.
    """

    create_info = VkFenceCreateInfo(
        flags = VK_FENCE_CREATE_SIGNALED_BIT
    )

    try:
        return vkCreateFence(device, create_info, None)
    except (VkError, VkException):
        logging.error("Failed to create the fence")
        return None
