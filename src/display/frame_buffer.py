"""
Contain all functions to create the frame buffers
"""

import logging
from typing import List

from vulkan import (
    VkError,
    VkException,
    VkExtent2D,
    VkFramebufferCreateInfo,
    vkCreateFramebuffer,
)

from .hinting import VkDevice, VkRenderPass
from .swapchain import SwapChainFrame


def make_frame_buffers(
    device: VkDevice,
    render_pass: VkRenderPass,
    swpchain_extent: VkExtent2D,
    frames: List[SwapChainFrame]
):
    """Create the frame buffer for each frame

    Args:
        device (VkDevice): the device to which the swapchain is linked
        render_pass (VkRenderPass): the render pass to which the swapchain is linked
        swpchain_extent (VkExtent2D): the linked swapchain extent
        frames (List[SwapChainFrame]): the list of frames
    """

    for i, frame in enumerate(frames):
        attachments = [frame.image_view]
        create_info = VkFramebufferCreateInfo(
            renderPass      = render_pass,
            attachmentCount = len(attachments),
            pAttachments    = attachments,
            width           = swpchain_extent.width,
            height          = swpchain_extent.height,
            layers          = 1
        )

        try:
            frame.frame_buffer = vkCreateFramebuffer(device, create_info, None)
        except (VkError, VkException):
            logging.error("Unable to create the frame buffer for frame n°%s", i)
