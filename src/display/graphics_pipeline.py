"""
Contain all functions to create the graphics pipeline
"""

from typing import Tuple

from vulkan import (
    VK_ATTACHMENT_LOAD_OP_CLEAR,
    VK_ATTACHMENT_LOAD_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_DONT_CARE,
    VK_ATTACHMENT_STORE_OP_STORE,
    VK_COLOR_COMPONENT_A_BIT,
    VK_COLOR_COMPONENT_B_BIT,
    VK_COLOR_COMPONENT_G_BIT,
    VK_COLOR_COMPONENT_R_BIT,
    VK_CULL_MODE_BACK_BIT,
    VK_FALSE,
    VK_FORMAT_R32G32_SFLOAT,
    VK_FORMAT_R32G32B32_SFLOAT,
    VK_FRONT_FACE_CLOCKWISE,
    VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
    VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
    VK_IMAGE_LAYOUT_UNDEFINED,
    VK_NULL_HANDLE,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_POLYGON_MODE_FILL,
    VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST,
    VK_SAMPLE_COUNT_1_BIT,
    VK_SHADER_STAGE_FRAGMENT_BIT,
    VK_SHADER_STAGE_VERTEX_BIT,
    VK_VERTEX_INPUT_RATE_VERTEX,
    VkAttachmentDescription,
    VkAttachmentReference,
    VkExtent2D,
    VkGraphicsPipelineCreateInfo,
    VkPipelineColorBlendAttachmentState,
    VkPipelineColorBlendStateCreateInfo,
    VkPipelineInputAssemblyStateCreateInfo,
    VkPipelineLayoutCreateInfo,
    VkPipelineMultisampleStateCreateInfo,
    VkPipelineRasterizationStateCreateInfo,
    VkPipelineShaderStageCreateInfo,
    VkPipelineVertexInputStateCreateInfo,
    VkPipelineViewportStateCreateInfo,
    VkPushConstantRange,
    VkRect2D,
    VkRenderPassCreateInfo,
    VkSubpassDescription,
    VkVertexInputAttributeDescription,
    VkVertexInputBindingDescription,
    VkViewport,
    vkCreateGraphicsPipelines,
    vkCreatePipelineLayout,
    vkCreateRenderPass,
    vkDestroyShaderModule,
)

from .hinting import (
    VkDescriptorSetLayout,
    VkDevice,
    VkPipeline,
    VkPipelineLayout,
    VkRenderPass,
)
from .shaders import create_shader_module


def _create_pipeline_layout(
    device: VkDevice,
    descriptor_set_layout: VkDescriptorSetLayout
) -> VkPipelineLayout:

    push_constant_model = VkPushConstantRange(
        stageFlags = VK_SHADER_STAGE_VERTEX_BIT,
        offset     = 0,
        size       = (4 * 4) * 4 # mat4 * float(4 bytes)
    )

    push_constant_ranges = [
        push_constant_model,
    ]

    create_info = VkPipelineLayoutCreateInfo(
        pushConstantRangeCount = len(push_constant_ranges),
        pPushConstantRanges    = push_constant_ranges,
        setLayoutCount         = 1,
        pSetLayouts            = [descriptor_set_layout]
    )

    return vkCreatePipelineLayout(device, create_info, None)

def _create_render_pass(device: VkDevice, swapchain_format: int) -> VkRenderPass:

    color_attachment = VkAttachmentDescription(
        format         = swapchain_format,
        samples        = VK_SAMPLE_COUNT_1_BIT,
        loadOp         = VK_ATTACHMENT_LOAD_OP_CLEAR,
        storeOp        = VK_ATTACHMENT_STORE_OP_STORE,
        stencilLoadOp  = VK_ATTACHMENT_LOAD_OP_DONT_CARE ,
        stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE,
        initialLayout  = VK_IMAGE_LAYOUT_UNDEFINED,
        finalLayout    = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR
    )

    color_attachment_ref = VkAttachmentReference(
        attachment = 0,
        layout     = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL
    )

    subpass = VkSubpassDescription(
        pipelineBindPoint    = VK_PIPELINE_BIND_POINT_GRAPHICS,
        colorAttachmentCount = 1,
        pColorAttachments    = color_attachment_ref
    )

    create_info = VkRenderPassCreateInfo(
        attachmentCount = 1,
        pAttachments    = color_attachment,
        subpassCount    = 1,
        pSubpasses      = subpass
    )

    return vkCreateRenderPass(device, create_info, None)

def make_graphics_pipeline(
    device: VkDevice,
    swapchain_extent: VkExtent2D,
    swapchain_format: int,
    descriptor_set_layout: VkDescriptorSetLayout,
    vertex_filepath: str,
    fragment_filepath: str
) -> Tuple[VkPipelineLayout, VkRenderPass, VkPipeline]:
    """Create the graphics pipeline

    Args:
        device (VkDevice): the device to which the pipeline layout will be linked
        swapchain_extent (VkExtent2D): the swapchain extent to which the pipeline layout
            will be linked
        swapchain_format (int): the linked swapchain image format
        descriptor_set_layout (VkDescriptorSetLayout): the descriptor set layout to use
        vertex_filepath (str): the path to shader.vert
        fragment_filepath (str): the path to shader.frag

    Returns:
        Tuple[VkPipelineLayout, VkRenderPass, VkPipeline]: The created pipeline layout,
            render pass and graphics_pipeline
    """
    # Vertex input
    vertex_input_binding_descriptions = [
        VkVertexInputBindingDescription(
            binding   = 0,
            stride    = (2 + 3) * 4, # (pos + color) * float size
            inputRate = VK_VERTEX_INPUT_RATE_VERTEX
        )
    ]

    vertex_input_attribute_descriptions = [
        VkVertexInputAttributeDescription(
            binding  = 0,
            location = 0,
            format   = VK_FORMAT_R32G32_SFLOAT,
            offset   = 0
        ),
        VkVertexInputAttributeDescription(
            binding  = 0,
            location = 1,
            format   = VK_FORMAT_R32G32B32_SFLOAT,
            offset   = 8 # pos * float size
        )
    ]

    vertex_input_create_info = VkPipelineVertexInputStateCreateInfo(
        vertexBindingDescriptionCount   = len(vertex_input_binding_descriptions),
        pVertexBindingDescriptions      = vertex_input_binding_descriptions,
        vertexAttributeDescriptionCount = len(vertex_input_attribute_descriptions),
        pVertexAttributeDescriptions    = vertex_input_attribute_descriptions
    )

    # Vertex shader
    vertex_shader_module = create_shader_module(device, vertex_filepath)
    vertex_shader_stage_create_info = VkPipelineShaderStageCreateInfo(
        stage  = VK_SHADER_STAGE_VERTEX_BIT,
        module = vertex_shader_module,
        pName  = "main"
    )

    # Input assembly
    input_assembly_crete_info = VkPipelineInputAssemblyStateCreateInfo(
        topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST
    )

    # Viewport & scissor
    viewport = VkViewport(
        x        = 0,
        y        = 0,
        width    = swapchain_extent.width,
        height   = swapchain_extent.height,
        minDepth = 0.0,
        maxDepth = 1.0
    )

    scissor = VkRect2D(
        offset = [0, 0],
        extent = swapchain_extent
    )

    viewport_create_info = VkPipelineViewportStateCreateInfo(
        viewportCount = 1,
        pViewports    = viewport,
        scissorCount  = 1,
        pScissors     = scissor
    )

    # Rasterizer
    rasterizer_create_info = VkPipelineRasterizationStateCreateInfo(
        depthClampEnable        = VK_FALSE,
        rasterizerDiscardEnable = VK_FALSE,
        polygonMode             = VK_POLYGON_MODE_FILL,
        lineWidth               = 1.0,
        cullMode                = VK_CULL_MODE_BACK_BIT,
        frontFace               = VK_FRONT_FACE_CLOCKWISE,
        depthBiasEnable         = VK_FALSE
    )

    # Multisampling
    multisampling_create_info = VkPipelineMultisampleStateCreateInfo(
        sampleShadingEnable  = VK_FALSE,
        rasterizationSamples = VK_SAMPLE_COUNT_1_BIT
    )

    # Fragment shader
    fragment_shader_module = create_shader_module(device, fragment_filepath)
    fragment_shader_stage_create_info = VkPipelineShaderStageCreateInfo(
        stage  = VK_SHADER_STAGE_FRAGMENT_BIT,
        module = fragment_shader_module,
        pName  = "main"
    )

    # Color blend attachment
    mask = (
          VK_COLOR_COMPONENT_R_BIT
        | VK_COLOR_COMPONENT_G_BIT
        | VK_COLOR_COMPONENT_B_BIT
        | VK_COLOR_COMPONENT_A_BIT
    )

    color_blend_attachment = VkPipelineColorBlendAttachmentState(
        colorWriteMask = mask,
        blendEnable = VK_FALSE
    )
    color_blending_create_info = VkPipelineColorBlendStateCreateInfo(
        logicOpEnable = VK_FALSE,
        attachmentCount = 1,
        pAttachments = color_blend_attachment,
        blendConstants = [0.0, 0.0, 0.0, 0.0]
    )

    # Creation
    shader_stages = [
        vertex_shader_stage_create_info,
        fragment_shader_stage_create_info,
    ]

    pipeline_layout = _create_pipeline_layout(device, descriptor_set_layout)
    render_pass = _create_render_pass(device, swapchain_format)

    create_info = VkGraphicsPipelineCreateInfo(
        stageCount          = len(shader_stages),
        pStages             = shader_stages,
        pVertexInputState   = vertex_input_create_info,
        pInputAssemblyState = input_assembly_crete_info,
        pTessellationState  = None,
        pViewportState      = viewport_create_info,
        pRasterizationState = rasterizer_create_info,
        pMultisampleState   = multisampling_create_info,
        pDepthStencilState  = None,
        pColorBlendState    = color_blending_create_info,
        pDynamicState       = None,
        layout              = pipeline_layout,
        renderPass          = render_pass,
        subpass             = 0
    )

    graphics_pipeline = vkCreateGraphicsPipelines(
        device          = device,
        pipelineCache   = VK_NULL_HANDLE,
        createInfoCount = 1,
        pCreateInfos    = create_info,
        pAllocator      = None
    )[0]

    vkDestroyShaderModule(device, vertex_shader_module, None)
    vkDestroyShaderModule(device, fragment_shader_module, None)

    return pipeline_layout, render_pass, graphics_pipeline
