"""Functions related to the VkInstance object.

Functions:
    create_instance(application_name: str)
    create_surface(instance: VkInstance, window: GLFWWindow) -> VkSurfaceKHR
    destroy_surface(instance: VkInstance, surface: VkSurfaceKHR)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from glfw import create_window_surface, get_required_instance_extensions
from vulkan import (
    VK_EXT_DEBUG_UTILS_EXTENSION_NAME,
    VK_MAKE_VERSION,
    VK_SUCCESS,
    VK_VERSION_MAJOR,
    VK_VERSION_MINOR,
    VK_VERSION_PATCH,
    VkApplicationInfo,
    VkError,
    VkException,
    VkInstanceCreateInfo,
    ffi,
    vkCreateInstance,
    vkEnumerateInstanceExtensionProperties,
    vkEnumerateInstanceLayerProperties,
    vkEnumerateInstanceVersion,
    vkGetInstanceProcAddr,
)

from src.consts import APPLICATION_VERSION

from ._consts import (
    GRAPHICS_ENGINE_NAME,
    GRAPHICS_ENGINE_VERSION,
    REQUIRED_VULKAN_VERSION,
    VALIDATION_LAYERS,
    VALIDATION_LAYERS_ENABLED,
)
from ._validation_layers import populate_debug_utils_messenger_create_info
from .errors import (
    MissingVulkanInstanceExtensionError,
    MissingVulkanInstanceLayerError,
    VulkanCreationError,
    VulkanVersionTooOldError,
)

if TYPE_CHECKING:
    from .hinting import GLFWWindow, VkInstance, VkSurfaceKHR


# Instance
def _check_vulkan_version() -> bool:
    max_supported_version = vkEnumerateInstanceVersion()
    if max_supported_version < REQUIRED_VULKAN_VERSION:
        logging.error(
            (
                "Application requires vulkan %s.%s.%s "
                "but system's max supported is %s.%s.%s"
            ),
            VK_VERSION_MAJOR(REQUIRED_VULKAN_VERSION) & 0x7F,
            VK_VERSION_MINOR(REQUIRED_VULKAN_VERSION),
            VK_VERSION_PATCH(REQUIRED_VULKAN_VERSION),

            VK_VERSION_MAJOR(max_supported_version) & 0x7F,
            VK_VERSION_MINOR(max_supported_version),
            VK_VERSION_PATCH(max_supported_version),
        )
        return False
    return True

def _get_required_layers() -> list[str]:
    required_layers = []

    if VALIDATION_LAYERS_ENABLED:
        required_layers += VALIDATION_LAYERS

    return required_layers

def _check_available_layers(required_layers: list[str]) -> bool:
    supported_layers = [
        layer.layerName
        for layer in vkEnumerateInstanceLayerProperties()
    ]

    suitable = True
    for layer in required_layers:
        if layer not in supported_layers:
            logging.warning("Required layer %s not available", layer)
            suitable = False

    return suitable

def _get_required_extensions() -> list[str]:
    required_extensions = []

    if VALIDATION_LAYERS_ENABLED:
        required_extensions.append(VK_EXT_DEBUG_UTILS_EXTENSION_NAME)

    glfw_extensions = get_required_instance_extensions()
    required_extensions += glfw_extensions

    return required_extensions

def _check_supported_extensions(required_extensions: list[str]) -> bool:
    supported_extensions = [
        extension.extensionName
        for extension in vkEnumerateInstanceExtensionProperties(None)
    ]

    suitable = True
    for extension in required_extensions:
        if extension not in supported_extensions:
            logging.warning("Required extension %s not suported", extension)
            suitable = False

    return suitable

def create_instance(application_name: str) -> VkInstance:
    """Create a vulkan instance.

    Args:
        application_name (str): The name of the application

    Raises:
        VulkanVersionTooOld: The installed vulkan version is prior the
            required version
        MissingVulkanInstanceLayer: At least one layer is missing
        MissingVulkanInstanceExtension: At least one extension is
            missing
        VulkanCreationError: The object creation failed

    Returns:
        VkInstance: The created vulkan instance
    """
    if not _check_vulkan_version():
        logging.error("The installed vulkan version is prior the required one")
        raise VulkanVersionTooOldError

    app_info = VkApplicationInfo(
        pApplicationName   = application_name,
        applicationVersion = VK_MAKE_VERSION(*APPLICATION_VERSION),
        pEngineName        = GRAPHICS_ENGINE_NAME,
        engineVersion      = GRAPHICS_ENGINE_VERSION,
        apiVersion         = REQUIRED_VULKAN_VERSION,
    )

    layers = _get_required_layers()
    if not _check_available_layers(layers):
        logging.errror("Required layer(s) not available !")
        raise MissingVulkanInstanceLayerError

    extensions = _get_required_extensions()
    if not _check_supported_extensions(extensions):
        logging.errror("Required extension(s) not supported !")
        raise MissingVulkanInstanceExtensionError

    if VALIDATION_LAYERS_ENABLED:
        p_next = populate_debug_utils_messenger_create_info()
    else:
        p_next = None

    create_info = VkInstanceCreateInfo(
        pApplicationInfo        = app_info,
        enabledLayerCount       = len(layers),
        ppEnabledLayerNames     = layers,
        enabledExtensionCount   = len(extensions),
        ppEnabledExtensionNames = extensions,
        pNext                   = p_next,
    )

    try:
        return vkCreateInstance(create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the instance !")
        raise VulkanCreationError from e

# Surface
def create_surface(instance: VkInstance, window: GLFWWindow) -> VkSurfaceKHR:
    """Create a VkSurfaceKHR.

    Args:
        instance (VkInstance): the instance to which the surface will be linked
        window (GLFWWindow): the window to which the surface will be linked

    Raises:
        VulkanCreationError() the surface creation failed

    Returns:
        VkSurface: the created surface
    """
    surface_ptr = ffi.new("VkSurfaceKHR *")
    if (create_window_surface(instance, window, None, surface_ptr)
        != VK_SUCCESS):
        logging.error("Failed to create the surface !")

    return surface_ptr[0]

def destroy_surface(instance: VkInstance, surface: VkSurfaceKHR) -> None:
    """Destroy the given surface.

    Args:
        instance (VkInstance): the instance to which the surface is linked
        surface (VkSurface): the surface
    """
    vkDestroySurfaceKHR = vkGetInstanceProcAddr(
        instance, "vkDestroySurfaceKHR")
    vkDestroySurfaceKHR(instance, surface, None)
