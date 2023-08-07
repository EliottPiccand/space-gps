"""
Contain classes and functions related to graphics and present queue families
"""

import logging
from typing import Tuple

from vulkan import (
    VK_QUEUE_GRAPHICS_BIT,
    vkGetDeviceQueue,
    vkGetInstanceProcAddr,
    vkGetPhysicalDeviceQueueFamilyProperties,
)

from .hinting import (
    VkDevice,
    VkGraphicsQueue,
    VkInstance,
    VkPhysicalDevice,
    VkPresentQueue,
    VkSurface,
)


class QueueFamilyIndices:
    """
    Store graphics and present queues indices
    """

    def __init__(self):
        self.graphics: int = None
        self.present: int = None

    def are_complete(self) -> bool:
        """Whether both graphics and present indices are defined or not

        Returns:
            bool: True only if both are not None
        """

        return not(self.graphics is None or self.present is None)

def find_queue_families(
    instance: VkInstance,
    surface: VkSurface,
    physical_device: VkPhysicalDevice
) -> QueueFamilyIndices:
    """Querry queue familes from device

    Args:
        instance (VkInstance): the instance to which the queues will be linked
        surface (VkSurface): the surface to which the queues will be linked
        device (VkPhysicalDevice): the device to which the queues will be linked

    Returns:
        QueueFamilyIndices: contains the indices of the queues (indices might be None)
    """

    indices = QueueFamilyIndices()

    queue_families_properties = \
        vkGetPhysicalDeviceQueueFamilyProperties(physical_device)

    vkGetPhysicalDeviceSurfaceSupportKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfaceSupportKHR")

    for i, queue_family_properties in enumerate(queue_families_properties):

        if queue_family_properties.queueFlags & VK_QUEUE_GRAPHICS_BIT:
            indices.graphics = i

        if vkGetPhysicalDeviceSurfaceSupportKHR(physical_device, i, surface):
            indices.present = i

        if indices.are_complete():
            break

    if not indices.are_complete():
        logging.error("Failed to fetch the graphics or present queue")

    return indices

def get_queues(
    device: VkDevice,
    indices: QueueFamilyIndices
) -> Tuple[VkGraphicsQueue, VkPresentQueue]:
    """Get graphics queue from indices

    Args:
        device (VkDevice): the device to which the queues are linked
        indices (QueueFamilyIndices): the queue indices

    Returns:
        Tuple[VkGraphicsQueue, VkPresentQueue]: the graphics and present queue
    """

    graphics_queue = vkGetDeviceQueue(
        device           = device,
        queueFamilyIndex = indices.graphics,
        queueIndex       = 0
    )

    present_queue = vkGetDeviceQueue(
        device           = device,
        queueFamilyIndex = indices.present,
        queueIndex       = 0
    )

    return graphics_queue, present_queue
