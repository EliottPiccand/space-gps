"""Classes and Functions related to queues (graphics and present).

Classes:
    QueueFamilyIndices()

Functions:
    find_queue_families(instance: VkInstance, surface: VkSurfaceKHR,
        physical_device: VkPhysicalDevice) -> QueueFamilyIndices
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from vulkan import (
    VK_QUEUE_GRAPHICS_BIT,
    vkGetDeviceQueue,
    vkGetInstanceProcAddr,
    vkGetPhysicalDeviceQueueFamilyProperties,
)

if TYPE_CHECKING:
    from .hinting import (
        VkDevice,
        VkGraphicsQueue,
        VkInstance,
        VkPhysicalDevice,
        VkPresentQueue,
        VkSurfaceKHR,
    )


@dataclass
class QueueFamilyIndices:
    """The queues indices.

    Attributes:
        graphics_family: Optional[int]
        present_family: Optional[int] = None

    Methods:
        is_complete(self) -> bool
    """

    graphics_family: int | None = None
    present_family: int | None = None

    def is_complete(self) -> bool:
        """Returns whether all indices are set or not.

        Returns:
            bool: True if all indices are not None
        """
        return (
                self.graphics_family is not None
            and self.present_family  is not None
        )

def find_queue_families(
    instance: VkInstance,
    surface: VkSurfaceKHR,
    physical_device: VkPhysicalDevice,
) -> QueueFamilyIndices:
    """Populate a QueueFamilyIndices class with valid queue indices.

    Args:
        instance (VkInstance): The instance to which the queues will be
            linked.
        surface (VkSurfaceKHR): The surface to which the present queue
            will be linked.
        physical_device (VkPhysicalDevice): The physical device to use.

    Returns:
        QueueFamilyIndices: The populated indices structures.
    """
    indices = QueueFamilyIndices()

    queue_families = vkGetPhysicalDeviceQueueFamilyProperties(physical_device)

    vkGetPhysicalDeviceSurfaceSupportKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfaceSupportKHR")

    for i, queue_family in enumerate(queue_families):
        if queue_family.queueFlags & VK_QUEUE_GRAPHICS_BIT:
            indices.graphics_family = i

        if vkGetPhysicalDeviceSurfaceSupportKHR(physical_device, i, surface):
            indices.present_family = i

        if indices.is_complete():
            break

    return indices

def get_queues(
    instance: VkInstance,
    surface: VkSurfaceKHR,
    physical_device: VkPhysicalDevice,
    device: VkDevice,
) -> tuple[VkGraphicsQueue | VkPresentQueue]:
    """Get vulkan queues from indices.

    Args:
        instance (VkInstance): The linked instance.
        surface (VkSurfaceKHR): The linked surface.
        physical_device (VkPhysicalDevice): The used physical device.
        device (VkDevice): The used logical device.

    Returns:
        VkGraphicsQueue: The created queues.
    """
    indices = find_queue_families(instance, surface, physical_device)

    graphics_queue = vkGetDeviceQueue(
        device           = device,
        queueFamilyIndex = indices.graphics_family,
        queueIndex       = 0,
    )

    present_queue = vkGetDeviceQueue(
        device           = device,
        queueFamilyIndex = indices.present_family,
        queueIndex       = 0,
    )

    return graphics_queue, present_queue
