"""
Contains all functions to create a descriptor set layout
"""

import logging
from typing import List, Optional

from vulkan import (
    VkDescriptorPoolCreateInfo,
    VkDescriptorPoolSize, VkDescriptorSetAllocateInfo, vkAllocateDescriptorSets,
    VkDescriptorSetLayoutBinding,
    VkDescriptorSetLayoutCreateInfo,
    VkError,
    VkException,
    vkCreateDescriptorPool,
    vkCreateDescriptorSetLayout,
)

from .hinting import (
    VkDescriptorSetLayout,
    VkDescriptorType,
    VkDevice,
    VkShaderStageFlags,VkDescriptorPool,VkDescriptorSet
)


def make_descriptor_set_layout(
    device: VkDevice,
    count: int,
    indices: List[int],
    types: List[VkDescriptorType],
    counts: List[int],
    stage_flags: List[VkShaderStageFlags]
) -> Optional[VkDescriptorSetLayout]:
    """Create a descriptor set layout

    Args:
        device (VkDevice): the device to which the descriptor set layout will be linked
        count (int): the number of descriptor layout in the set
        indices (List[int]): the list of binding indices
        types (List[VkDescriptorType]): the list specifying which type of resource
            descriptors are used for this binding
        counts (List[int]): the list of number of descriptors contained in the binding
        stage_flags (List[VkShaderStageFlags]): a bitmask of VkShaderStageFlagBits
            specifying which pipeline shader stages can access a resource per binding

    Returns:
        Optional[VkDescriptorSetLayout]: The created descriptor set layout. Might be
            None if creation failed
    """
    layout_bindings = []

    for i in range(count):

        layout_bindings.append(VkDescriptorSetLayoutBinding(
            binding = indices[i],
            descriptorType = types[i],
            descriptorCount = counts[i],
            stageFlags = stage_flags[i]
        ))

    create_info = VkDescriptorSetLayoutCreateInfo(
        bindingCount = len(layout_bindings),
        pBindings    = layout_bindings
    )

    try:
        return vkCreateDescriptorSetLayout(device, create_info, None)
    except (VkError, VkException):
        logging.error("Failed to create the descriptor set layout")
        return None

def make_descriptor_pool(
    device: VkDevice,
    size: int,
    types: List[VkDescriptorType],
) -> Optional[VkDescriptorPool]:
    pool_sizes = []

    for _type in types:
        pool_sizes.append(VkDescriptorPoolSize(
            type            = _type,
            descriptorCount = size
        ))

    create_info = VkDescriptorPoolCreateInfo(
        poolSizeCount = len(pool_sizes),
        pPoolSizes = pool_sizes,
        maxSets = size
    )

    try:
        return vkCreateDescriptorPool(device, create_info, None)
    except (VkError, VkException):
        logging.error("Failed to create the descriptor pool")
        return None

def allocate_descriptor_set(
    device: VkDevice,
    descriptor_pool: VkDescriptorPool,
    descriptor_set_layout: VkDescriptorSetLayout
) -> Optional[VkDescriptorSet]:
    alloc_info = VkDescriptorSetAllocateInfo(
        descriptorPool = descriptor_pool,
        descriptorSetCount = 1,
        pSetLayouts = [descriptor_set_layout]
    )

    try:
        return vkAllocateDescriptorSets(device, alloc_info)[0]
    except (VkError, VkException):
        logging.error("Failed to allocate the descriptor set")
        return None
