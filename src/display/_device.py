"""Functions related to physical and logical devices.

Functions:
    pick_physical_device(
        instance: VkInstance, surface: VkSurfaceKHR) -> VkPhysicalDevice
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vulkan import (
    VkDeviceCreateInfo,
    VkDeviceQueueCreateInfo,
    VkError,
    VkException,
    VkPhysicalDeviceFeatures,
    vkCreateDevice,
    vkEnumerateDeviceExtensionProperties,
    vkEnumeratePhysicalDevices,
)

from ._consts import (
    DEVICE_EXTENSIONS,
    VALIDATION_LAYERS,
    VALIDATION_LAYERS_ENABLED,
)
from ._queues import find_queue_families
from ._swapchain import query_swapchain_support
from .errors import NoPhysicalDeviceFoundError, VulkanCreationError

if TYPE_CHECKING:
    from .hinting import VkDevice, VkInstance, VkPhysicalDevice, VkSurfaceKHR


# Physical
def _check_extensions(physical_device: VkPhysicalDevice) -> bool:

    available_extensions = [
        extension.extensionName
        for extension in vkEnumerateDeviceExtensionProperties(
            physical_device, None)
    ]

    for required_extension in DEVICE_EXTENSIONS:
        if required_extension not in available_extensions:
            return False

    return True

def _is_suitable(
    instance: VkInstance,
    surface: VkSurfaceKHR,
    physical_device: VkPhysicalDevice,
) -> bool:
    indices = find_queue_families(instance, surface, physical_device)

    swapchain_support_details = query_swapchain_support(
        instance, surface, physical_device)

    return (
            indices.is_complete()
        and _check_extensions(physical_device)
        and swapchain_support_details.is_suitable()
    )

def pick_physical_device(
    instance: VkInstance,
    surface: VkSurfaceKHR,
) -> VkPhysicalDevice:
    """Pick the first suitable physical device found.

    Args:
        instance (VkInstance): The instance to which the future logical
            device will be linked.
        surface (VkSurfaceKHR): The surface to which the present queue
            will be linked.

    Raises:
        NoPhysicalDeviceFound: Either there is no physical device or
            none is suitable.

    Returns:
        VkPhysicalDevice: The picked physical device.
    """
    available_physical_devices = vkEnumeratePhysicalDevices(instance)

    for physical_device in available_physical_devices:
        if _is_suitable(instance, surface, physical_device):
            return physical_device

    logging.error("Failed to find a suitable physical device !")
    raise NoPhysicalDeviceFoundError

# Logical
def create_logical_device(
    instance: VkInstance,
    surface: VkSurfaceKHR,
    physical_device: VkPhysicalDevice,
) -> VkDevice:
    """Creates and returns a logical device.

    Args:
        instance (VkInstance): The instance to which the device will be
            linked.
        surface (VkSurfaceKHR): The surface to which the present queue
            will be linked.
        physical_device (VkPhysicalDevice): The physical device to link.

    Raises:
        VulkanCreationError: The creation of the logical device failed.

    Returns:
        VkDevice: The created logical device.
    """
    indices = find_queue_families(instance, surface, physical_device)

    uniques_indices = list({indices.graphics_family, indices.present_family})

    queue_create_infos = [
        VkDeviceQueueCreateInfo(
            queueFamilyIndex = queue_family_index,
            queueCount       = 1,
            pQueuePriorities = [1.0],
        ) for queue_family_index in uniques_indices
    ]

    features = VkPhysicalDeviceFeatures()

    layers = []
    if VALIDATION_LAYERS_ENABLED:
        layers += VALIDATION_LAYERS

    create_info = VkDeviceCreateInfo(
        queueCreateInfoCount    = len(queue_create_infos),
        pQueueCreateInfos       = queue_create_infos,
        enabledLayerCount       = len(layers),
        ppEnabledLayerNames     = layers,
        enabledExtensionCount   = len(DEVICE_EXTENSIONS),
        ppEnabledExtensionNames = DEVICE_EXTENSIONS,
        pEnabledFeatures        = features,
    )

    try:
        return vkCreateDevice(physical_device, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the device !")
        raise VulkanCreationError from e
