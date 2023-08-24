"""Functions related to images.

Functions:
    create_image_views(device: VkDevice, swapchain_images: list[VkImage],
        swapchain_image_format: VkFormat,
    ) -> list[VkImageView]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vulkan import (
    VK_COMPONENT_SWIZZLE_IDENTITY,
    VK_IMAGE_ASPECT_COLOR_BIT,
    VK_IMAGE_VIEW_TYPE_2D,
    VkComponentMapping,
    VkError,
    VkException,
    VkExtent2D,
    VkFramebufferCreateInfo,
    VkImageSubresourceRange,
    VkImageViewCreateInfo,
    vkCreateFramebuffer,
    vkCreateImageView,
)

from .errors import VulkanCreationError

if TYPE_CHECKING:
    from .hinting import (
        VkDevice,
        VkFormat,
        VkFrameBuffer,
        VkImage,
        VkImageView,
        VkRenderPass,
    )


def create_image_views(
    device: VkDevice,
    swapchain_images: list[VkImage],
    swapchain_image_format: VkFormat,
) -> list[VkImageView]:
    """Create an image view for each image.

    Args:
        device (VkDevice): The device to which the images are linked.
        swapchain_images (list[VkImage]): The images.
        swapchain_image_format (VkFormat): The images format.

    Raises:
        VulkanCreationError: The creation failed.

    Returns:
        list[VkImageView]: The created image views.
    """
    image_views = []

    for image in swapchain_images:
        components = VkComponentMapping(
            r = VK_COMPONENT_SWIZZLE_IDENTITY,
            g = VK_COMPONENT_SWIZZLE_IDENTITY,
            b = VK_COMPONENT_SWIZZLE_IDENTITY,
            a = VK_COMPONENT_SWIZZLE_IDENTITY,
        )

        subresource_range = VkImageSubresourceRange(
            aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
            baseMipLevel   = 0,
            levelCount     = 1,
            baseArrayLayer = 0,
            layerCount     = 1,
        )

        create_info = VkImageViewCreateInfo(
            image            = image,
            viewType         = VK_IMAGE_VIEW_TYPE_2D,
            format           = swapchain_image_format,
            components       = components,
            subresourceRange = subresource_range,
        )

        try:
            image_view = vkCreateImageView(device, create_info, None)
        except (VkError, VkException) as e:
            logging.exception("Failed to create the image view :")
            raise VulkanCreationError from e

        image_views.append(image_view)

    return image_views

def create_frame_buffers(
    device: VkDevice,
    extent: VkExtent2D,
    image_views: list[VkImageView],
    render_pass: VkRenderPass,
) -> list[VkFrameBuffer]:
    """Creates and returns a frame buffer for each image view.

    Args:
        device (VkDevice): The logical device to which the frame buffers
            will be linked.
        extent (VkExtent2D): The window extent.
        image_views (list[VkImageView]): The image views.
        render_pass (VkRenderPass): The render pass to which the frame
            buffers will be linked.

    Raises:
        VulkanCreationError: The frame buffers creation failed.

    Returns:
        list[VkFrameBuffer]: The created frame buffers.
    """
    frame_buffers = []

    for image_view in image_views:
        attachments = [image_view]
        create_info = VkFramebufferCreateInfo(
            renderPass      = render_pass,
            attachmentCount = len(attachments),
            pAttachments    = attachments,
            width           = extent.width,
            height          = extent.height,
            layers          = 1,
        )

        try:
            frame_buffers.append(
                vkCreateFramebuffer(device, create_info, None),
            )
        except (VkError, VkException) as e:
            logging.exception("Failed to create the frame buffer !")
            raise VulkanCreationError from e

    return frame_buffers
