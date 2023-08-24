"""Handle vulkan debug messages.

Functions:
    populate_debug_utils_messenger_create_info(
        ) -> VkDebugUtilsMessengerCreateInfoEXT
    setup_debug_messenger(
        instance: VkInstance) -> VkDebugUtilsMessengerEXT
    destroy_debug_messenger(
        instance: VkInstance, debug_messenger: VkDebugUtilsMessengerEXT)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from vulkan import (
    VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT,
    VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT,
    VK_DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT,
    VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT,
    VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT,
    VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT,
    VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT,
    VK_FALSE,
    StrWrap,
    VkDebugUtilsMessengerCreateInfoEXT,
    VkError,
    VkException,
    vkGetInstanceProcAddr,
)

from .errors import VulkanCreationError

if TYPE_CHECKING:
    from .hinting import (
        VkDebugUtilsMessageSeverityFlagBitsEXT,
        VkDebugUtilsMessageTypeFlagsEXT,
        VkDebugUtilsMessengerCallbackDataEXT,
        VkDebugUtilsMessengerEXT,
        VkInstance,
        VoidPointer,
    )


def _debug_callback( # pylint: disable=too-many-arguments,unused-argument
    message_severity: VkDebugUtilsMessageSeverityFlagBitsEXT,
    message_type: VkDebugUtilsMessageTypeFlagsEXT,  # noqa: ARG001
    p_callback_data: tuple[VkDebugUtilsMessengerCallbackDataEXT],
    p_user_data: VoidPointer,  # noqa: ARG001
) -> Literal[VK_FALSE]:
    """Log a validation layer.

    Args:
        message_severity (VkDebugUtilsMessageSeverityFlagBitsEXT): The
            severity flag that triggered this callback.
        message_type (VkDebugUtilsMessageTypeFlagsEXT): The type flag
            that triggered this callback.
        p_callback_data (Tuple[VkDebugUtilsMessengerCallbackDataEXT]):
            Contains all the callback related data.
        p_user_data (VoidPointer): The user data provided when the
            VkDebugUtilsMessengerEXT was created.

    Returns:
        Literal[VK_FALSE]: VK_FALSE
    """
    message = StrWrap(p_callback_data[0]).pMessage

    if message_severity >= VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT:
        logging.error("%s\n", message)

    elif (message_severity >= VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT
      or "using deprecated" in message):
        logging.warning("%s\n", message)

    elif message_severity >= VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT:
        logging.info(message)

    else: # VK_DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT
        logging.debug(message)

    return VK_FALSE

def populate_debug_utils_messenger_create_info(
)-> VkDebugUtilsMessengerCreateInfoEXT:
    """Populate the creation structure for VkDebugUtilsMessenger.

    Returns:
        VkDebugUtilsMessengerCreateInfoEXT: the populated structure
    """
    message_severity = (
          VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT
        | VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT
        | VK_DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT
        | VK_DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT
    )

    message_type = (
          VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT
        | VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT
        | VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT
    )

    return VkDebugUtilsMessengerCreateInfoEXT(
        messageSeverity = message_severity,
        messageType     = message_type,
        pfnUserCallback = _debug_callback,
    )

def setup_debug_messenger(instance: VkInstance) -> VkDebugUtilsMessengerEXT:
    """Create and return the debug messenger.

    Args:
        instance (VkInstance): The instance to which will be linked to
            the messenger

    Raises:
        VulkanCreationError: The debug messenger creation failed

    Returns:
        VkDebugReportCallbackEXT: The created messenger
    """
    create_info = populate_debug_utils_messenger_create_info()

    vkCreateDebugUtilsMessengerEXT = vkGetInstanceProcAddr(
        instance, "vkCreateDebugUtilsMessengerEXT")

    try:
        return vkCreateDebugUtilsMessengerEXT(instance, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the debug messenger !")
        raise VulkanCreationError from e

def destroy_debug_messenger(
    instance: VkInstance,
    debug_messenger: VkDebugUtilsMessengerEXT,
) -> None:
    """Destroy the given debug messenger.

    Args:
        instance (VkInstance): the instance to which the messenger is linked
        debug_messenger (VkDebugUtilsMessengerEXT): the messenger
    """
    vkDestroyDebugUtilsMessengerEXT = vkGetInstanceProcAddr(
        instance, "vkDestroyDebugUtilsMessengerEXT")
    vkDestroyDebugUtilsMessengerEXT(instance, debug_messenger, None)
