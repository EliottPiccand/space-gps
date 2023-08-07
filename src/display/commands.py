"""
Contain all functions to create the command pool
"""

import logging
from typing import Optional

from numpy import float32
from pyrr import matrix44
from vulkan import (
    VK_COMMAND_BUFFER_LEVEL_PRIMARY,
    VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_SHADER_STAGE_VERTEX_BIT,
    VK_SUBPASS_CONTENTS_INLINE,
    VkClearValue,
    VkCommandBufferAllocateInfo,
    VkCommandBufferBeginInfo,
    VkCommandPoolCreateInfo,
    VkError,
    VkException,
    VkExtent2D,
    VkRenderPassBeginInfo,
    vkAllocateCommandBuffers,
    vkBeginCommandBuffer,
    vkCmdBeginRenderPass,
    vkCmdBindPipeline,
    vkCmdDraw,
    vkCmdEndRenderPass,
    vkCmdPushConstants,
    vkCreateCommandPool,
    vkEndCommandBuffer,
)
from vulkan import ffi as c_link

from .hinting import (
    VkCommandBuffer,
    VkCommandPool,
    VkDevice,
    VkFrameBuffer,
    VkPipeline,
    VkPipelineLayout,
    VkRenderPass,
    VkRenderPassBeginInfoStruct,
    VkSubpassContents,
)
from .queue_families import QueueFamilyIndices
from .scene import Scene


def make_command_pool(
    device: VkDevice,
    indices: QueueFamilyIndices
) -> Optional[VkCommandPool]:
    """Create the command pool

    Args:
        device (VkDevice): the device to which the command pool will be linked
        indices (QueueFamilyIndices): its queues indices

    Returns:
        Optional[VkCommandPool]: The created command pool. Might be None if creation
            failed.
    """

    create_info = VkCommandPoolCreateInfo(
        flags            = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
        queueFamilyIndex = indices.graphics
    )

    try:
        return vkCreateCommandPool(device, create_info, None)
    except (VkError, VkException):
        logging.error("Failed to create the command buffer")
        return None

def make_command_buffer(
    device: VkDevice,
    command_pool: VkCommandPool
) -> Optional[VkCommandBuffer]:
    """Allocate a command buffer

    Args:
        device (VkDevice): the device to which the command buffer will be linked 
        command_pool (VkCommandPool): the command pool used

    Returns:
        Optional[VkCommandPool]: The created command pool. Might be None if creation
            failed.
    """

    allocate_info = VkCommandBufferAllocateInfo(
        commandPool        = command_pool,
        level              = VK_COMMAND_BUFFER_LEVEL_PRIMARY,
        commandBufferCount = 1
    )

    try:
        return vkAllocateCommandBuffers(device, allocate_info, None)[0]
    except (VkError, VkException):
        logging.error("Failed to allocate the command buffer")
        return None

class CommandBufferManager:
    """
    A context manager to begin and end VkCommandBuffer
    """

    def __init__(self, command_buffer: VkCommandBuffer):
        self.__command_buffer = command_buffer

    def __enter__(self):
        begin_info = VkCommandBufferBeginInfo()
        try:
            vkBeginCommandBuffer(self.__command_buffer, begin_info)
        except (VkError, VkException):
            logging.error("Failed to begin recording command buffer")

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            vkEndCommandBuffer(self.__command_buffer)
        except (VkError, VkException):
            logging.error("Failed to end recording command buffer")

class RenderPassManager:
    """
    A context manager to begin and end VkRenderPass
    """

    def __init__(
        self,
        command_buffer: VkCommandBuffer,
        render_pass_begin_info: VkRenderPassBeginInfoStruct,
        contents: VkSubpassContents
    ):
        self.__command_buffer = command_buffer
        self.__render_pass_begin_info = render_pass_begin_info
        self.__contents = contents

    def __enter__(self):
        vkCmdBeginRenderPass(
            self.__command_buffer,
            self.__render_pass_begin_info,
            self.__contents
        )

    def __exit__(self, exc_type, exc_value, exc_traceback):
        vkCmdEndRenderPass(self.__command_buffer)

def record_draw_command(
    pipeline_layout: VkPipelineLayout,
    render_pass: VkRenderPass,
    frame_buffer: VkFrameBuffer,
    swapchain_extent: VkExtent2D,
    graphics_pipeline: VkPipeline,
    command_buffer: VkCommandBuffer,
    scene: Scene
):
    """Record draw command to the render pass

    Args:
        render_pass (VkRenderPass): the render pass
        frame_buffer (VkFrameBuffer): the current frame buffer
        swapchain_extent (VkExtent2D): the swapchain extent
        graphics_pipeline (VkPipeline): the graphics pipeline to use
        command_buffer (VkCommandBuffer): the command buffer to use
    """

    with CommandBufferManager(command_buffer):

        clear_color = VkClearValue([[1.0, 0.5, 0.25, 1.0]])
        render_pass_begin_info = VkRenderPassBeginInfo(
            renderPass = render_pass,
            framebuffer = frame_buffer,
            renderArea = [[0, 0], swapchain_extent],
            clearValueCount = 1,
            pClearValues = c_link.addressof(clear_color)
        )

        with RenderPassManager(
            command_buffer,
            render_pass_begin_info,
            VK_SUBPASS_CONTENTS_INLINE
        ):
            vkCmdBindPipeline(
                command_buffer,
                VK_PIPELINE_BIND_POINT_GRAPHICS,
                graphics_pipeline
            )


            for pos in scene.triangle_positions:
                model_transform = matrix44.create_from_translation(
                    vec   = pos,
                    dtype = float32
                )

                object_data = c_link.cast("float*", c_link.from_buffer(model_transform))

                vkCmdPushConstants(
                    commandBuffer = command_buffer,
                    layout        = pipeline_layout,
                    stageFlags    = VK_SHADER_STAGE_VERTEX_BIT,
                    offset        = 0,
                    size          = (4 * 4) * 4, # mat4 * float32
                    pValues       = object_data
                )

                vkCmdDraw(
                    commandBuffer = command_buffer,
                    vertexCount   = 3,
                    instanceCount = 1,
                    firstVertex   = 0,
                    firstInstance = 0
                )
