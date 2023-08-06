"""
Contain all functions to create a vulkan instance
"""

import logging
from typing import List, Optional

from glfw import create_window_surface, get_required_instance_extensions
from vulkan import (
    VK_EXT_DEBUG_REPORT_EXTENSION_NAME,
    VK_MAKE_VERSION,
    VK_SUCCESS,
    VK_VERSION_MAJOR,
    VK_VERSION_MINOR,
    VK_VERSION_PATCH,
    VkApplicationInfo,
    VkError,
    VkException,
    VkInstanceCreateInfo,
    vkCreateInstance,
    vkEnumerateInstanceExtensionProperties,
    vkEnumerateInstanceLayerProperties,
    vkEnumerateInstanceVersion, vkGetInstanceProcAddr
)
from vulkan import ffi as c_linker

from src.consts import APPLICATION_VERSION, DEBUG

from .consts import (
    GRAPHICS_ENGINE_NAME,
    GRAPHICS_ENGINE_VERSION,
    REQUIRED_VULKAN_VERSION,
)
from .hinting import VkInstance, VkSurface, Window


def _get_required_layers() -> List[str]:
    required_layers = []
    if DEBUG:
        required_layers.append("VK_LAYER_KHRONOS_validation")

    # Check support
    supported_layers = [
        layer.layerName
        for layer in vkEnumerateInstanceLayerProperties()
    ]

    for layer in required_layers:
        if layer not in supported_layers:
            logging.warning("Required layer %s not suported", layer)

    return required_layers

def _get_required_extensions() -> List[str]:
    required_extensions = get_required_instance_extensions() # GLFW
    if DEBUG:
        required_extensions.append(VK_EXT_DEBUG_REPORT_EXTENSION_NAME)

    # Check support
    supported_extensions = [
        extension.extensionName
        for extension in vkEnumerateInstanceExtensionProperties(None)
    ]

    for extension in required_extensions:
        if extension not in supported_extensions:
            logging.warning("Required extension %s not suported", extension)

    return required_extensions

def make_instance(application_name: str) -> Optional[VkInstance]:
    """Create and return a VkInstance based on the given application name

    Args:
        application_name (str): the name of the application

    Returns:
        Optional[VkInstance]: the created vulkan instance
    """

    max_supported_version = vkEnumerateInstanceVersion()
    if REQUIRED_VULKAN_VERSION > max_supported_version:
        logging.warning(
            (
                "Application requires vulkan %s.%s.%s "
                "but system's max supported is %s.%s.%s"
            ),
            VK_VERSION_MAJOR(REQUIRED_VULKAN_VERSION) & 0x7F,
            VK_VERSION_MINOR(REQUIRED_VULKAN_VERSION),
            VK_VERSION_PATCH(REQUIRED_VULKAN_VERSION),

            VK_VERSION_MAJOR(max_supported_version) & 0x7F,
            VK_VERSION_MINOR(max_supported_version),
            VK_VERSION_PATCH(max_supported_version)
        )

    application_info = VkApplicationInfo(
        pApplicationName   = application_name,
        applicationVersion = VK_MAKE_VERSION(*APPLICATION_VERSION),
        pEngineName        = GRAPHICS_ENGINE_NAME,
        engineVersion      = GRAPHICS_ENGINE_VERSION,
        apiVersion         = REQUIRED_VULKAN_VERSION
    )

    required_layers = _get_required_layers()
    required_extensions = _get_required_extensions()

    create_info = VkInstanceCreateInfo(
        pApplicationInfo        = application_info,
        enabledLayerCount       = len(required_layers),
        ppEnabledLayerNames     = required_layers,
        enabledExtensionCount   = len(required_extensions),
        ppEnabledExtensionNames = required_extensions
    )

    try:
        return vkCreateInstance(create_info, None)
    except (VkException, VkError) as e:
        logging.error("Failed to create the vulkan instance ! (%s)", e )
        return None

def make_surface(instance: VkInstance, window: Window) -> VkSurface:
    """Create a VkSurface

    Args:
        instance (VkInstance): the instance to which the surface will be linked
        window (Window): the window to which the surface will be linked

    Returns:
        VkSurface: the created surface
    """

    surface_ptr = c_linker.new("VkSurfaceKHR*")
    if create_window_surface(instance, window, None, surface_ptr) != VK_SUCCESS:
        logging.error("Failed to create the surface")

    return surface_ptr[0]

def destroy_surface(instance: VkInstance, surface: VkSurface):
    """Destroy the given surface

    Args:
        instance (VkInstance): the instance to which the surface is linked
        surface (VkSurface): the surface
    """

    vkDestroySurfaceKHR = vkGetInstanceProcAddr(instance, "vkDestroySurfaceKHR")
    vkDestroySurfaceKHR(instance, surface, None)
