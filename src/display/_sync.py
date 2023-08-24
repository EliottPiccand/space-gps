"""Functions to create semaphores and fences.

Functions:
    create_semaphores(device: VkDevice, n: int) -> list[VkSemaphore]
    create_fences(device: VkDevice, n: int) -> list[VkFence]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vulkan import (
    VK_FENCE_CREATE_SIGNALED_BIT,
    VkError,
    VkException,
    VkFenceCreateInfo,
    VkSemaphoreCreateInfo,
    vkCreateFence,
    vkCreateSemaphore,
)

from .errors import VulkanCreationError

if TYPE_CHECKING:
    from .hinting import VkDevice, VkFence, VkSemaphore


def create_semaphores(device: VkDevice, n: int) -> list[VkSemaphore]:
    """Creates and returns n semaphores.

    Args:
        device (VkDevice): THe logical device to which the semaphores
            will be linked.
        n (int): The amount of semaphores to create.

    Raises:
        VulkanCreationError: The creation of a semaphore failed.

    Returns:
        list[VkSemaphore]: The created semaphores.
    """
    create_info = VkSemaphoreCreateInfo()

    try:
        return [
            vkCreateSemaphore(device, create_info, None)
            for _ in range(n)
        ]
    except (VkError, VkException) as e:
        logging.exception("Failed to create the semaphore !")
        raise VulkanCreationError from e

def create_fences(device: VkDevice, n: int) -> list[VkFence]:
    """Creates and returns n fences.

    Args:
        device (VkDevice): The logical device to which the fences
            will be linked.
        n (int): The amount of fences to create.

    Raises:
        VulkanCreationError: The creation of a fence failed.

    Returns:
        list[VkFence]: The created fences.
    """
    create_info = VkFenceCreateInfo(
        flags = VK_FENCE_CREATE_SIGNALED_BIT,
    )

    try:
        return [
            vkCreateFence(device, create_info, None)
            for _ in range(n)
        ]
    except (VkError, VkException) as e:
        logging.exception("Failed to create the fence !")
        raise VulkanCreationError from e
