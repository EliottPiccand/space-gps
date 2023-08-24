"""Functions to create the graphics pipeline.

Functions:
    create_pipeline_layout(device: VkDevice) -> VkPipelineLayout
    create_render_pass(device: VkDevice,
        image_format: VkFormat) -> VkRenderPass
    create_graphics_pipeline(device: VkDevice, extent: VkExtent2D,
        pipeline_layout: VkPipelineLayout, render_pass: VkRenderPass,
        ) -> VkPipeline
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vulkan import (
    VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
    VK_ATTACHMENT_LOAD_OP_CLEAR,
    VK_ATTACHMENT_LOAD_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_STORE,
    VK_COLOR_COMPONENT_A_BIT,
    VK_COLOR_COMPONENT_B_BIT,
    VK_COLOR_COMPONENT_G_BIT,
    VK_COLOR_COMPONENT_R_BIT,
    VK_CULL_MODE_BACK_BIT,
    VK_DYNAMIC_STATE_SCISSOR,
    VK_DYNAMIC_STATE_VIEWPORT,
    VK_FALSE,
    VK_FRONT_FACE_CLOCKWISE,
    VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
    VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
    VK_IMAGE_LAYOUT_UNDEFINED,
    VK_NULL_HANDLE,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_POLYGON_MODE_FILL,
    VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    VK_SAMPLE_COUNT_1_BIT,
    VK_SHADER_STAGE_FRAGMENT_BIT,
    VK_SHADER_STAGE_VERTEX_BIT,
    VK_SUBPASS_CONTENTS_INLINE,
    VK_SUBPASS_EXTERNAL,
    VkAttachmentDescription,
    VkAttachmentReference,
    VkClearValue,
    VkError,
    VkException,
    VkExtent2D,
    VkGraphicsPipelineCreateInfo,
    VkPipelineColorBlendAttachmentState,
    VkPipelineColorBlendStateCreateInfo,
    VkPipelineDynamicStateCreateInfo,
    VkPipelineInputAssemblyStateCreateInfo,
    VkPipelineLayoutCreateInfo,
    VkPipelineMultisampleStateCreateInfo,
    VkPipelineRasterizationStateCreateInfo,
    VkPipelineShaderStageCreateInfo,
    VkPipelineVertexInputStateCreateInfo,
    VkPipelineViewportStateCreateInfo,
    VkRect2D,
    VkRenderPassBeginInfo,
    VkRenderPassCreateInfo,
    VkSubpassDependency,
    VkSubpassDescription,
    VkViewport,
    ffi,
    vkCmdBeginRenderPass,
    vkCmdEndRenderPass,
    vkCreateGraphicsPipelines,
    vkCreatePipelineLayout,
    vkCreateRenderPass,
    vkDestroyShaderModule,
)

from ._consts import FRAGMENT_SHADER_FILEPATH, VERTEX_SHADER_FILEPATH
from ._shaders import create_shader_module
from ._vertex import Vertex
from .errors import VulkanCreationError

if TYPE_CHECKING:
    from types import TracebackType

    from .hinting import (
        VkCommandBuffer,
        VkDevice,
        VkFormat,
        VkFrameBuffer,
        VkPipeline,
        VkPipelineLayout,
        VkRenderPass,
    )


def create_pipeline_layout(device: VkDevice) -> VkPipelineLayout:
    """Creates and returns the pipeline layout.

    Args:
        device (VkDevice): The logical device to which the pipeline
            layout will be linked.

    Raises:
        VulkanCreationError: The pipeline layout creation failed.

    Returns:
        VkPipelineLayout: The created pipeline layout.
    """
    create_info = VkPipelineLayoutCreateInfo()
    try:
        return vkCreatePipelineLayout(device, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the pipeline layout !")
        raise VulkanCreationError from e

def create_render_pass(
    device: VkDevice,
    image_format: VkFormat,
) -> VkRenderPass:
    """Creates and returns the render pass.

    Args:
        device (VkDevice): The logical device to which the render pass
            will be linked.
        image_format (VkFormat): The image format to use.

    Raises:
        VulkanCreationError: The render pass creation failed.

    Returns:
        VkRenderPass: The created render pass.
    """
    color_attachment = VkAttachmentDescription(
        format         = image_format,
        samples        = VK_SAMPLE_COUNT_1_BIT,
        loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR,
        storeOp        = VK_ATTACHMENT_STORE_OP_STORE,
        stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE,
        stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED,
        finalLayout    = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
    )

    color_attachment_ref = VkAttachmentReference(
        attachment = 0,
        layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
    )

    subpass = VkSubpassDescription(
        pipelineBindPoint    = VK_PIPELINE_BIND_POINT_GRAPHICS,
        colorAttachmentCount = 1,
        pColorAttachments    = color_attachment_ref,
    )

    dependency = VkSubpassDependency(
        srcSubpass    = VK_SUBPASS_EXTERNAL,
        dstSubpass    = 0,
        srcStageMask  = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
        dstStageMask  = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
        srcAccessMask = 0,
        dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
    )

    create_info = VkRenderPassCreateInfo(
        attachmentCount = 1,
        pAttachments    = color_attachment,
        subpassCount    = 1,
        pSubpasses      = subpass,
        dependencyCount = 1,
        pDependencies   = dependency,
    )

    try:
        return vkCreateRenderPass(device, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the render pass !")
        raise VulkanCreationError from e

def create_graphics_pipeline(
    device: VkDevice,
    extent: VkExtent2D,
    pipeline_layout: VkPipelineLayout,
    render_pass: VkRenderPass,
) -> VkPipeline:
    """Creates and returns the graphics pipeline.

    Args:
        device (VkDevice): The logical device to which the pipeline
            will be linked.
        extent (VkExtent2D): The images extent.
        pipeline_layout (VkPipelineLayout): The pipeline layout.
        render_pass (VkRenderPass): The render pass to which the pipeline
            will be linked.

    Raises:
        VulkanCreationError: The pipeline creation failed.

    Returns:
        VkPipeline: The created graphics pipeline.
    """
    # Shaders
    vertex_shader_module = create_shader_module(
        device   = device,
        filename = VERTEX_SHADER_FILEPATH,
    )
    vertex_stage_create_info = VkPipelineShaderStageCreateInfo(
        stage  = VK_SHADER_STAGE_VERTEX_BIT,
        module = vertex_shader_module,
        pName  = "main",
    )

    fragment_shader_module = create_shader_module(
        device   = device,
        filename = FRAGMENT_SHADER_FILEPATH,
    )
    fragment_stage_create_info = VkPipelineShaderStageCreateInfo(
        stage  = VK_SHADER_STAGE_FRAGMENT_BIT,
        module = fragment_shader_module,
        pName  = "main",
    )

    shader_stages = [
        vertex_stage_create_info,
        fragment_stage_create_info,
    ]

    # Vertex input
    binding_description = Vertex.get_binding_description()
    attribute_descrptions = Vertex.get_attribut_descriptions()

    vertex_input_create_info = VkPipelineVertexInputStateCreateInfo(
        vertexBindingDescriptionCount   = 1,
        pVertexBindingDescriptions      = [binding_description],
        vertexAttributeDescriptionCount = len(attribute_descrptions),
        pVertexAttributeDescriptions    = attribute_descrptions,
    )

    # Input assembly
    input_assembly_create_info = VkPipelineInputAssemblyStateCreateInfo(
        topology               = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
        primitiveRestartEnable = VK_FALSE,
    )

    # Viewport and Scissor
    viewport = VkViewport(
        x        = 0,
        y        = 0,
        width    = extent.width,
        height   = extent.height,
        minDepth = 0,
        maxDepth = 1,
    )

    scissor = VkRect2D(
        offset = [0, 0],
        extent = extent,
    )

    viewport_state_create_info = VkPipelineViewportStateCreateInfo(
        viewportCount = 1,
        pViewports    = viewport,
        scissorCount  = 1,
        pScissors     = scissor,
    )

    # Rasterization
    rasterizer_create_info = VkPipelineRasterizationStateCreateInfo(
        depthClampEnable        = VK_FALSE,
        rasterizerDiscardEnable = VK_FALSE,
        polygonMode             = VK_POLYGON_MODE_FILL,
        lineWidth               = 1,
        cullMode                = VK_CULL_MODE_BACK_BIT,
        frontFace               = VK_FRONT_FACE_CLOCKWISE,
        depthBiasClamp          = VK_FALSE,
    )

    # Multisampler
    multisampler_create_info = VkPipelineMultisampleStateCreateInfo(
        sampleShadingEnable  = VK_FALSE,
        rasterizationSamples = VK_SAMPLE_COUNT_1_BIT,
    )

    # Depth stencil

    # Color blending
    color_write_mask = (
          VK_COLOR_COMPONENT_R_BIT
        | VK_COLOR_COMPONENT_G_BIT
        | VK_COLOR_COMPONENT_B_BIT
        | VK_COLOR_COMPONENT_A_BIT
    )

    color_blend_attachment = VkPipelineColorBlendAttachmentState(
        colorWriteMask = color_write_mask,
        blendEnable    = VK_FALSE,
    )

    color_blend_create_info = VkPipelineColorBlendStateCreateInfo(
        logicOpEnable = VK_FALSE,
        attachmentCount = 1,
        pAttachments    = color_blend_attachment,
    )

    # Dynamic states
    dynamic_states = [
        VK_DYNAMIC_STATE_VIEWPORT,
        VK_DYNAMIC_STATE_SCISSOR,
    ]
    dynamic_state_create_info = VkPipelineDynamicStateCreateInfo(
        dynamicStateCount = len(dynamic_states),
        pDynamicStates    = dynamic_states,
    )

    # Creation
    create_info = VkGraphicsPipelineCreateInfo(
        stageCount          = 2,
        pStages             = shader_stages,
        pVertexInputState   = vertex_input_create_info,
        pInputAssemblyState = input_assembly_create_info,
        pViewportState      = viewport_state_create_info,
        pRasterizationState = rasterizer_create_info,
        pMultisampleState   = multisampler_create_info,
        pDepthStencilState  = None,
        pColorBlendState    = color_blend_create_info,
        pDynamicState       = dynamic_state_create_info,
        layout              = pipeline_layout,
        renderPass          = render_pass,
        subpass             = 0,
    )

    try:
        graphics_pipeline = vkCreateGraphicsPipelines(
            device          = device,
            pipelineCache   = VK_NULL_HANDLE,
            createInfoCount = 1,
            pCreateInfos    = create_info,
            pAllocator      = None,
        )[0]
    except (VkError, VkException) as e:
        logging.exception("Failed to create the graphics pipeline !")
        raise VulkanCreationError from e

    vkDestroyShaderModule(device, vertex_shader_module, None)
    vkDestroyShaderModule(device, fragment_shader_module, None)

    return graphics_pipeline

class RenderPassManager:
    """A context manager to begin and end VkRenderPass."""

    def __init__(
        self,
        extent: VkExtent2D,
        render_pass: VkRenderPass,
        frame_buffer: VkFrameBuffer,
        command_buffer: VkCommandBuffer,
    ):
        self.__extent = extent
        self.__render_pass = render_pass
        self.__frame_buffer = frame_buffer
        self.__command_buffer = command_buffer

    def __enter__(self):
        clear_color = VkClearValue([[1.0, 0.5, 0.25, 1.0]])
        begin_info = VkRenderPassBeginInfo(
            renderPass      = self.__render_pass,
            framebuffer     = self.__frame_buffer,
            renderArea      = [[0, 0], self.__extent],
            clearValueCount = 1,
            pClearValues    = ffi.addressof(clear_color),
        )

        vkCmdBeginRenderPass(
            commandBuffer    = self.__command_buffer,
            pRenderPassBegin = begin_info,
            contents         = VK_SUBPASS_CONTENTS_INLINE,
        )

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        vkCmdEndRenderPass(self.__command_buffer)
