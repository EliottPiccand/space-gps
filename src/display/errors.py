"""Custom errors for display module.

Classes:
    VulkanVersionTooOldError()
    MissingVulkanInstanceExtensionError()
    MissingVulkanInstanceLayerError()
    VulkanCreationError()
    NoPhysicalDeviceFoundError()
    CommandRecordError()
    QueueSubmitError()
    NoValidMemoryTypeError()
"""

class VulkanVersionTooOldError(Exception):
    """Vulkan installed version is prior the required version !"""

class MissingVulkanInstanceExtensionError(Exception):
    """A required extension is missing !"""

class MissingVulkanInstanceLayerError(Exception):
    """A required layer is missing !"""

class VulkanCreationError(Exception):
    """Vulkan object cretion failed !"""

class NoPhysicalDeviceFoundError(Exception):
    """No suitable physical device found !"""

class CommandRecordError(Exception):
    """Failed to recod a command to the buffer !"""

class QueueSubmitError(Exception):
    """Failed to submit a command to the queue !"""

class NoValidMemoryTypeError(Exception):
    """Failed to find a valid memory type !"""
