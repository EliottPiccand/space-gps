"""Classes and functions to handle the swap chain.

Classes:
    SwapchainSupportDetails

Functions:
    query_swapchain_support(instance: VkInstance, surface: VkSurfaceKHR,
        physical_device: VkPhysicalDevice,
    ) -> SwapchainSupportDetails
    create_swapchain(instance: VkInstance, surface: VkSurfaceKHR,
        physical_device: VkPhysicalDevice, device: VkDevice,
        width: int, height: int,
    ) -> tuple[VkSwapchainKHR, list[VkImage], VkFormat, VkExtent2D]
    destroy_swapchain(device: VkDevice, swapchain: VkSwapchainKHR) -> None
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from vulkan import (
    VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,
    VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
    VK_FORMAT_B8G8R8A8_SRGB,
    VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
    VK_PRESENT_MODE_MAILBOX_KHR,
    VK_SHARING_MODE_CONCURRENT,
    VK_SHARING_MODE_EXCLUSIVE,
    VK_TRUE,
    VkError,
    VkException,
    VkExtent2D,
    VkSwapchainCreateInfoKHR,
    vkGetDeviceProcAddr,
    vkGetInstanceProcAddr,
)

from ._queues import find_queue_families
from ._utils import clamp
from .errors import VulkanCreationError

if TYPE_CHECKING:
    from .hinting import (
        VkDevice,
        VkFormat,
        VkImage,
        VkInstance,
        VkPhysicalDevice,
        VkPresentModeKHR,
        VkSurfaceCapabilitiesKHR,
        VkSurfaceFormatKHR,
        VkSurfaceKHR,
        VkSwapchainKHR,
    )


@dataclass
class SwapchainSupportDetails:
    """Details about the swap chain.

    Attributes:
        capabilities: VkSurfaceCapabilitiesKHR
        formats: list[VkSurfaceFormatKHR]
        present_modes: list[VkPresentModeKHR]

    Methods:
        is_suitable(self) -> bool
    """
    capabilities: VkSurfaceCapabilitiesKHR
    formats: list[VkSurfaceFormatKHR]
    present_modes: list[VkPresentModeKHR]

    def is_suitable(self) -> bool:
        """Returns whether this swap chain support is suitable or not.

        Returns:
            bool: True if this support is suitable.
        """
        return self.formats != [] and self.present_modes != []

def query_swapchain_support(
    instance: VkInstance,
    surface: VkSurfaceKHR,
    physical_device: VkPhysicalDevice,
) -> SwapchainSupportDetails:
    """Populate a SwapchainSupportDetails class.

    Args:
        instance (VkInstance): The instance to which the swap chain
            will be linked.
        surface (VkSurfaceKHR): The surface to which the swap chain
            will be linked.
        physical_device (VkPhysicalDevice): The physical device tu use.

    Returns:
        SwapchainSupportDetails: The populated support details.
    """
    # Capabilities
    vkGetPhysicalDeviceSurfaceCapabilitiesKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfaceCapabilitiesKHR")

    capabilities = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(
        physicalDevice = physical_device,
        surface        = surface,
    )

    # Formats
    vkGetPhysicalDeviceSurfaceFormatsKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfaceFormatsKHR")

    formats = vkGetPhysicalDeviceSurfaceFormatsKHR(physical_device, surface)

    # Present modes
    vkGetPhysicalDeviceSurfacePresentModesKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfacePresentModesKHR")

    present_modes = vkGetPhysicalDeviceSurfacePresentModesKHR(
        physical_device, surface)

    return SwapchainSupportDetails(
        capabilities  = capabilities,
        formats       = formats,
        present_modes = present_modes,
    )

def _chose_surface_format(
    available_formats: list[VkSurfaceFormatKHR],
) -> VkSurfaceFormatKHR:
    for available_format in available_formats:
        if (available_format.format == VK_FORMAT_B8G8R8A8_SRGB
        and available_format.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
            return available_format

    return available_formats[0]

def _chose_present_mode(
    available_present_modes: list[VkPresentModeKHR],
) -> VkPresentModeKHR:
    for available_present_mode in available_present_modes:
        if available_present_mode == VK_PRESENT_MODE_MAILBOX_KHR:
            return available_present_mode

    return available_present_modes[0]

def _chose_extent(
    width: int,
    height: int,
    capabilities: VkSurfaceCapabilitiesKHR,
) -> VkExtent2D:

    width = clamp(
        capabilities.minImageExtent.width,
        width,
        capabilities.maxImageExtent.width,
    )

    height = clamp(
        capabilities.minImageExtent.height,
        height,
        capabilities.maxImageExtent.height,
    )

    return VkExtent2D(width, height)

def create_swapchain(
    instance: VkInstance,
    surface: VkSurfaceKHR,
    physical_device: VkPhysicalDevice,
    device: VkDevice,
    width: int,
    height: int,
) -> tuple[VkSwapchainKHR, list[VkImage], VkFormat, VkExtent2D]:
    """Creates and returns the swapchain.

    Args:
        instance (VkInstance): The instance to which the swapchain will
            be linked.
        surface (VkSurfaceKHR): The surface to which the swapchain will
            be linked.
        physical_device (VkPhysicalDevice): The physical device to use.
        device (VkDevice): The logical device to which the swapchain
            will be linked.
        width (int): The window width.
        height (int): The window height.

    Raises:
        VulkanCreationError: The creation failed.

    Returns:
        tuple[VkSwapchainKHR, list[VkImage], VkFormat, VkExtent2D]:
            The created swapchain, its images, its image format and
            its extent.
    """
    swapchain_supprt = query_swapchain_support(
        instance        = instance,
        surface         = surface,
        physical_device = physical_device,
    )

    surface_format = _chose_surface_format(swapchain_supprt.formats)
    present_mode = _chose_present_mode(swapchain_supprt.present_modes)
    extent = _chose_extent(width, height, swapchain_supprt.capabilities)

    image_count = swapchain_supprt.capabilities.minImageCount + 1
    max_image_count = swapchain_supprt.capabilities.maxImageCount
    if 0 < max_image_count < image_count:
        image_count = max_image_count

    indices = find_queue_families(instance, surface, physical_device)
    if indices.graphics_family != indices.present_family:
        image_sharing_mode = VK_SHARING_MODE_CONCURRENT
        queue_family_index_count = 2
        queue_family_indices = [
            indices.graphics_family,
            indices.present_family,
        ]
    else:
        image_sharing_mode = VK_SHARING_MODE_EXCLUSIVE
        queue_family_index_count = 0
        queue_family_indices = None

    create_info = VkSwapchainCreateInfoKHR(
        surface               = surface,
        minImageCount         = image_count,
        imageFormat           = surface_format.format,
        imageColorSpace       = surface_format.colorSpace,
        imageExtent           = extent,
        imageArrayLayers      = 1,
        imageUsage            = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
        imageSharingMode      = image_sharing_mode,
        queueFamilyIndexCount = queue_family_index_count,
        pQueueFamilyIndices   = queue_family_indices,
        preTransform          = swapchain_supprt.capabilities.currentTransform,
        compositeAlpha        = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
        presentMode           = present_mode,
        clipped               = VK_TRUE,
    )

    vkCreateSwapchainKHR = vkGetDeviceProcAddr(
        device, "vkCreateSwapchainKHR")
    try:
        swapchain = vkCreateSwapchainKHR(device, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the swapchain !")
        raise VulkanCreationError from e

    vkGetSwapchainImagesKHR = vkGetDeviceProcAddr(
        device, "vkGetSwapchainImagesKHR")
    images = vkGetSwapchainImagesKHR(device, swapchain)

    return swapchain, images, surface_format.format, extent

def destroy_swapchain(device: VkDevice, swapchain: VkSwapchainKHR) -> None:
    """Destroy the given swapchain.

    Args:
        device (VkDevice): the device to which the swapchain is linked
        swapchain (VkSwapchainKHR): the swapchain
    """
    vkDestroySwapchainKHR = vkGetDeviceProcAddr(
        device, "vkDestroySwapchainKHR")
    vkDestroySwapchainKHR(device, swapchain, None)
