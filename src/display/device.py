"""
Contain all functions to create physical and logical Vulkan devices
"""

import logging
from typing import Optional, Tuple

from vulkan import (
    VK_KHR_SWAPCHAIN_EXTENSION_NAME,
    VkDeviceCreateInfo,
    VkDeviceQueueCreateInfo,
    VkPhysicalDeviceFeatures,
    vkCreateDevice,
    vkEnumerateDeviceExtensionProperties,
    vkEnumeratePhysicalDevices,
)

from src.consts import DEBUG

from .hinting import VkDevice, VkInstance, VkPhysicalDevice, VkSurface
from .queue_families import QueueFamilyIndices, find_queue_families

# Physical device
_REQUIRED_EXTENSIONS = [
    VK_KHR_SWAPCHAIN_EXTENSION_NAME,
]

def _support_extension(physical_device: VkPhysicalDevice) -> bool:
    supported_extensions = [
        extension.extensionName
        for extension in vkEnumerateDeviceExtensionProperties(physical_device, None)
    ]

    for extension in _REQUIRED_EXTENSIONS:
        if extension not in supported_extensions:
            return False

    return True

def _is_suitable(physical_device: VkPhysicalDevice) -> bool:
    return _support_extension(physical_device)

def chose_physical_device(instance:  VkInstance) -> Optional[VkPhysicalDevice]:
    """Chose a physical device suitable for the required features

    Args:
        instance (VkInstance): the instance to which the device will be linked

    Returns:
        Optional[VkPhysicalDevice]: The device found. Can be None if none is suitable.
    """

    available_physical_devices = vkEnumeratePhysicalDevices(instance)

    for physical_device in available_physical_devices:
        if _is_suitable(physical_device):
            return physical_device

    logging.error("No physical device found !")
    return None

# Logical device
_REQUIRED_LAYERS = []
if DEBUG:
    _REQUIRED_LAYERS.append("VK_LAYER_KHRONOS_validation")

def make_logical_device(
    instance: VkInstance,
    physical_device: VkPhysicalDevice,
    surface: VkSurface
) -> Tuple[VkDevice, QueueFamilyIndices]:
    """Create a logical device from a physical device

    Args:
        instance (VkInstance): the instance to which the device present queue will be
            linked
        physical_device (VkPhysicalDevice): the physical device from which the device is
            created
        surface (VkSurface): the surface to which the device present queue will be
            linked

    Returns:
        Tuple[VkDevice, QueueFamilyIndices]: the created logical device and the graphics
            and present queue indices
    """

    indices = find_queue_families(instance, surface, physical_device)
    uniques_indices = list({indices.graphics, indices.present})

    queue_create_info = []
    for queue_family_index in uniques_indices:
        queue_create_info.append(VkDeviceQueueCreateInfo(
            queueFamilyIndex = queue_family_index,
            queueCount       = 1,
            pQueuePriorities = [1.0,]
        ))

    device_features = VkPhysicalDeviceFeatures()

    create_info = VkDeviceCreateInfo(
        queueCreateInfoCount    = len(queue_create_info),
        pQueueCreateInfos       = queue_create_info,
        enabledLayerCount       = len(_REQUIRED_LAYERS),
        ppEnabledLayerNames     = _REQUIRED_LAYERS,
        enabledExtensionCount   = len(_REQUIRED_EXTENSIONS),
        ppEnabledExtensionNames = _REQUIRED_EXTENSIONS,
        pEnabledFeatures        = [device_features,]
    )

    return vkCreateDevice(physical_device, [create_info,], None), indices
