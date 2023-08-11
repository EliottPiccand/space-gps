"""
Contain all functions to handle the swapchain
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from numpy import array, float32, ndarray
from pyrr import matrix44
from vulkan import (
    VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
    VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
    VK_COLOR_SPACE_SRGB_NONLINEAR_KHR,
    VK_COMPONENT_SWIZZLE_IDENTITY,
    VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
    VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
    VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
    VK_FORMAT_B8G8R8A8_UNORM,
    VK_IMAGE_ASPECT_COLOR_BIT,
    VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
    VK_IMAGE_VIEW_TYPE_2D,
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_PRESENT_MODE_FIFO_KHR,
    VK_PRESENT_MODE_MAILBOX_KHR,
    VK_SHARING_MODE_CONCURRENT,
    VK_SHARING_MODE_EXCLUSIVE,
    VK_TRUE,
    VkComponentMapping,
    VkDescriptorBufferInfo,
    VkExtent2D,
    VkImageSubresourceRange,
    VkImageViewCreateInfo,
    VkSwapchainCreateInfoKHR,
    VkWriteDescriptorSet,
    vkCreateImageView,
    vkGetDeviceProcAddr,
    vkGetInstanceProcAddr,
    vkMapMemory,
    vkUpdateDescriptorSets,
)

from .hinting import (
    VkBuffer,
    VkCommandBuffer,
    VkDescriptorSet,
    VkDevice,
    VkDeviceMemory,
    VkFence,
    VkFrameBuffer,
    VkImage,
    VkInstance,
    VkPhysicalDevice,
    VkSemaphore,
    VkSurface,
    VkSurfaceFormatKHR,
    VkSurfaceTransformFlagBitsKHR,
    VkSwapchainKHR,
    VoidPointer,
)
from .memory import create_buffer
from .queue_families import QueueFamilyIndices


@dataclass
class UniformBufferObject:
    """
    Represent an uniform buffer object
    """

    view:            Optional[ndarray] = None
    projection:      Optional[ndarray] = None
    view_projection: Optional[ndarray] = None

@dataclass
class SwapChainFrame:
    """
    A frame as it is stored in the swapchain
    """

    image:                         VkImage
    image_view:                    int
    frame_buffer:                  Optional[VkFrameBuffer] = None

    command_buffer:                Optional[VkCommandBuffer] = None

    in_flight_fence:               Optional[VkFence] = None
    image_available_semaphore:     Optional[VkSemaphore] = None
    render_finished_semaphore:     Optional[VkSemaphore] = None

    camera_data:                   UniformBufferObject = None
    uniform_buffer:                Optional[VkBuffer] = None
    uniform_buffer_memory:         Optional[VkDeviceMemory] = None
    uniform_buffer_write_location: Optional[VoidPointer] = None

    model_transforms:              ndarray = None
    model_buffer:                  Optional[VkBuffer] = None
    model_buffer_memory:           Optional[VkDeviceMemory] = None
    model_buffer_write_location:   Optional[VoidPointer] = None

    uniform_buffer_descriptor:     Optional[None] = None
    model_buffer_descriptor:       Optional[None] = None
    descriptor_set:                Optional[VkDescriptorSet] = None

    def make_descriptor_resources(
        self,
        device: VkDevice,
        physical_device: VkPhysicalDevice
    ):
        """Initialize the uniform  and model buffers, their memory and write location

        Args:
            device (VkDevice): the device to which the uniform buffer will be linked
            physical_device (VkPhysicalDevice): the physical device used to create the
                device
        """

        # ubo
        uniform_buffer_size = 3 * (4 * 4) * 4 # nb of * mat4 * float32

        self.uniform_buffer, self.uniform_buffer_memory = create_buffer(
            device               = device,
            physical_device      = physical_device,
            size                 = uniform_buffer_size,
            usage                = VK_BUFFER_USAGE_UNIFORM_BUFFER_BIT,
            requested_properties = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
                                 | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT
        )

        self.uniform_buffer_write_location = vkMapMemory(
            device = device,
            memory = self.uniform_buffer_memory,
            offset = 0,
            size   = uniform_buffer_size,
            flags  = 0
        )

        self.uniform_buffer_descriptor = VkDescriptorBufferInfo(
            buffer = self.uniform_buffer,
            offset = 0,
            range  = uniform_buffer_size
        )

        # Model
        self.model_transforms = array(
            [matrix44.create_identity(dtype=float32) for _ in range(1024)],
            dtype=float32
        )

        model_buffer_size = 1024 * (4 * 4) * 4 # nb of * mat4 * float32

        self.model_buffer, self.model_buffer_memory = create_buffer(
            device               = device,
            physical_device      = physical_device,
            size                 = model_buffer_size,
            usage                = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT,
            requested_properties = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
                                 | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT
        )

        self.model_buffer_write_location = vkMapMemory(
            device = device,
            memory = self.model_buffer_memory,
            offset = 0,
            size   = model_buffer_size,
            flags  = 0
        )

        self.model_buffer_descriptor = VkDescriptorBufferInfo(
            buffer = self.model_buffer,
            offset = 0,
            range  = model_buffer_size
        )

    def write_descriptor_set(self, device: VkDevice):
        """Initialize the descriptor set 

        Args:
            device (VkDevice): the device to which the descriptor set is linked
        """

        descriptor_writes = [
            VkWriteDescriptorSet(
                dstSet          = self.descriptor_set,
                dstBinding      = 0,
                dstArrayElement = 0,
                descriptorType  = VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
                descriptorCount = 1,
                pBufferInfo     = self.uniform_buffer_descriptor
            ),
            VkWriteDescriptorSet(
                dstSet          = self.descriptor_set,
                dstBinding      = 1,
                dstArrayElement = 0,
                descriptorType  = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                descriptorCount = 1,
                pBufferInfo     = self.model_buffer_descriptor
            )
        ]

        vkUpdateDescriptorSets(
            device               = device,
            descriptorWriteCount = len(descriptor_writes),
            pDescriptorWrites    = descriptor_writes,
            descriptorCopyCount  = 0,
            pDescriptorCopies    = None
        )

def _chose_swapchain_surface_format(
    instance: VkInstance,
    physical_device: VkPhysicalDevice,
    surface: VkSurface
) -> VkSurfaceFormatKHR:

    vkGetPhysicalDeviceSurfaceFormatsKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfaceFormatsKHR")

    formats = vkGetPhysicalDeviceSurfaceFormatsKHR(physical_device, surface)

    for fmt in formats:
        if (fmt.format == VK_FORMAT_B8G8R8A8_UNORM
            and fmt.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR):
            return fmt.format, fmt.colorSpace

    return formats[0].format, formats[0].colorSpace

def _chose_swapchain_surface_present_mode(
    instance: VkInstance,
    physical_device: VkPhysicalDevice,
    surface: VkSurface
) -> int:

    vkGetPhysicalDeviceSurfacePresentModesKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfacePresentModesKHR")

    present_modes = vkGetPhysicalDeviceSurfacePresentModesKHR(physical_device, surface)

    for present_mode in present_modes:
        if present_mode == VK_PRESENT_MODE_MAILBOX_KHR:
            return present_mode

    return VK_PRESENT_MODE_FIFO_KHR

def _chose_swapchain_extent(
    instance: VkInstance,
    physical_device: VkPhysicalDevice,
    surface: VkSurface,
    width: int,
    height: int
) -> Tuple[VkExtent2D, int, VkSurfaceTransformFlagBitsKHR]:

    vkGetPhysicalDeviceSurfaceCapabilitiesKHR = vkGetInstanceProcAddr(
        instance, "vkGetPhysicalDeviceSurfaceCapabilitiesKHR")

    capabilities = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical_device, surface)

    extent = VkExtent2D(width, height)

    extent.width = min(
        capabilities.maxImageExtent.width,
        max(
            capabilities.minImageExtent.width,
            extent.width
        )
    )

    extent.height = min(
        capabilities.maxImageExtent.height,
        max(
            capabilities.minImageExtent.height,
            extent.height
        )
    )

    image_count = min(
        capabilities.maxImageCount,
        capabilities.minImageCount + 1
    )

    return extent, image_count, capabilities.currentTransform

def make_swapchain(
    instance: VkInstance,
    device: VkDevice,
    physical_device: VkPhysicalDevice,
    surface: VkSurface,
    width: int,
    height: int,
    indices: QueueFamilyIndices
) -> Tuple[VkSwapchainKHR, List[SwapChainFrame], int, VkExtent2D]:
    """Create the swapchain

    Args:
        instance (VkInstance): the instance to which the swapchain will be linked
        device (VkDevice): the device to which the swapchain will be linked
        physical_device (VkPhysicalDevice): the physical device to which the swapchain
            will be linked
        surface (VkSurface): the surface to which the swapchain will be linked
        width (int): the width of the window
        height (int): the height of the window
        indices (QueueFamilyIndices): the graphics and present queue indices

    Returns:
        Tuple[VkSwapchainKHR, List[SwapChainFrame], int, VkExtent2D]: In order :
            - the created swapchain
            - its frame list (all optional attributes are None)
            - its image format
            - its extent
    """

    fmt, color_space = _chose_swapchain_surface_format(
        instance,
        physical_device,
        surface
    )

    present_mode = _chose_swapchain_surface_present_mode(
        instance,
        physical_device,
        surface
    )

    extent, image_count, current_transform = _chose_swapchain_extent(
        instance,
        physical_device,
        surface,
        width,
        height
    )

    if indices.graphics != indices.present:
        image_sharing_mode = VK_SHARING_MODE_CONCURRENT
        queue_family_index_count = 2
        queue_family_indices = [
            indices.graphics,
            indices.present,
        ]
    else:
        image_sharing_mode = VK_SHARING_MODE_EXCLUSIVE
        queue_family_index_count = 0
        queue_family_indices = None

    create_info = VkSwapchainCreateInfoKHR(
        surface               = surface,
        minImageCount         = image_count,
        imageFormat           = fmt,
        imageColorSpace       = color_space,
        imageExtent           = extent,
        imageArrayLayers      = 1,
        imageUsage            = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT,
        imageSharingMode      = image_sharing_mode,
        queueFamilyIndexCount = queue_family_index_count,
        pQueueFamilyIndices   = queue_family_indices,
        preTransform          = current_transform,
        compositeAlpha        = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
        presentMode           = present_mode,
        clipped               = VK_TRUE
    )

    vkCreateSwapchainKHR = vkGetInstanceProcAddr(instance, "vkCreateSwapchainKHR")
    swapchain = vkCreateSwapchainKHR(device, create_info, None)

    vkGetSwapchainImagesKHR = vkGetDeviceProcAddr(device, "vkGetSwapchainImagesKHR")
    images = vkGetSwapchainImagesKHR(device, swapchain)

    frames = []
    for image in images:

        components = VkComponentMapping(
            r = VK_COMPONENT_SWIZZLE_IDENTITY,
            g = VK_COMPONENT_SWIZZLE_IDENTITY,
            b = VK_COMPONENT_SWIZZLE_IDENTITY,
            a = VK_COMPONENT_SWIZZLE_IDENTITY
        )

        subresource_range = VkImageSubresourceRange(
            aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
            baseMipLevel   = 0,
            levelCount     = 1,
            baseArrayLayer = 0,
            layerCount     = 1
        )

        image_view_create_info = VkImageViewCreateInfo(
            image            = image,
            viewType         = VK_IMAGE_VIEW_TYPE_2D,
            format           = fmt,
            components       = components,
            subresourceRange = subresource_range
        )

        frames.append(SwapChainFrame(
            image      = image,
            image_view = vkCreateImageView(device, image_view_create_info, None),
            camera_data = UniformBufferObject()
        ))

    return swapchain, frames, fmt, extent

def destroy_swapchain(device: VkDevice, swapchain: VkSwapchainKHR):
    """Destroy the given swapchain

    Args:
        device (VkDevice): the device to which the swapchain is linked
        swapchain (VkSwapchainKHR): the swapchain
    """

    vkDestroySwapchainKHR = vkGetDeviceProcAddr(device, "vkDestroySwapchainKHR")
    vkDestroySwapchainKHR(device, swapchain, None)
