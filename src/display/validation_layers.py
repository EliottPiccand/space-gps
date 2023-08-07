"""
Contain all functions to handle vulkan debug messages
"""

import logging
from typing import Any

from vulkan import (VK_DEBUG_REPORT_DEBUG_BIT_EXT,
                    VK_DEBUG_REPORT_ERROR_BIT_EXT,
                    VK_DEBUG_REPORT_INFORMATION_BIT_EXT,
                    VK_DEBUG_REPORT_PERFORMANCE_WARNING_BIT_EXT,
                    VK_DEBUG_REPORT_WARNING_BIT_EXT, VK_FALSE,
                    VkDebugReportCallbackCreateInfoEXT, vkGetInstanceProcAddr)

from .hinting import VkBool, VkDebugReportCallbackEXT, VkInstance


def _debug_callback( # pylint: disable=too-many-arguments,unused-argument
    flags: int,
    object_type: int,
    obj: int,
    location: int,
    message_code: int,
    layer_prefix: str,
    message: str,
    user_data: Any
) -> VkBool:
    """Called when a validation layer is triggerd

    Args:
        flags (int): specifies the VkDebugReportFlagBitsEXT that triggered this
            callback.
        object_type (int): a VkDebugReportObjectTypeEXT value specifying the type
            of object being used or created at the time the event was triggered.
        object (int): is the object where the issue was detected.
        location (int): is a component (layer, driver, loader) defined value specifyin
            the location of the trigger. This is an optional value.
        message_code (int): is a layer-defined value indicating what test triggered this
            callback.
        layer_prefix (str): is an abbreviation of the name of the component making the
            callback.
        message (str): is a null-terminated string detailing the trigger conditions.
        user_data (Any): is the user data given when the VkDebugReportCallbackEXT was
            created.

    Returns:
        VkBool: Should be alwaws VK_FALSE
    """

    if flags >= VK_DEBUG_REPORT_DEBUG_BIT_EXT:
        logging.debug(message)
    elif flags >= VK_DEBUG_REPORT_ERROR_BIT_EXT:
        logging.error("%s\n", message)
    elif flags >= VK_DEBUG_REPORT_WARNING_BIT_EXT:
        # and VK_DEBUG_REPORT_PERFORMANCE_WARNING_BIT_EXT
        logging.warning(message)
    else: # VK_DEBUG_REPORT_INFORMATION_BIT_EXT
        logging.info(message)

    return VK_FALSE

def make_debug_messenger(instance: VkInstance) -> VkDebugReportCallbackEXT:
    """Create and return the debug messenger

    Args:
        instance (VkInstance): The instance to which will be linked to the messenger

    Returns:
        VkDebugReportCallbackEXT: the messenger
    """

    message_severity = (
          VK_DEBUG_REPORT_INFORMATION_BIT_EXT
        | VK_DEBUG_REPORT_WARNING_BIT_EXT
        | VK_DEBUG_REPORT_PERFORMANCE_WARNING_BIT_EXT
        | VK_DEBUG_REPORT_ERROR_BIT_EXT
        | VK_DEBUG_REPORT_DEBUG_BIT_EXT
    )

    create_info = VkDebugReportCallbackCreateInfoEXT(
        flags       = message_severity,
        pfnCallback = _debug_callback
    )

    creation_function = vkGetInstanceProcAddr(
        instance, "vkCreateDebugReportCallbackEXT")
    return creation_function(instance, create_info, None)

def destroy_debug_messenger(
    instance: VkInstance,
    debug_messenger: VkDebugReportCallbackEXT
):
    """Destroy the given debug messenger

    Args:
        instance (VkInstance): the instance to which the messenger is linked
        debug_messenger (VkDebugReportCallbackEXT): the messenger
    """

    destroy_function = vkGetInstanceProcAddr(
        instance, "vkDestroyDebugReportCallbackEXT")
    destroy_function(instance, debug_messenger, None)
