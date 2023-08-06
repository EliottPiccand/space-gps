"""
Contain all functions to load the shaders
"""

import logging

from vulkan import VkShaderModuleCreateInfo, vkCreateShaderModule

from .hinting import VkDevice, VkShaderModule


def create_shader_module(device: VkDevice, filename: str) -> VkShaderModule:
    """Load a shader file

    Args:
        device (VkDevice): the device to which the shader will be linked
        filename (str): the shader file

    Returns:
        VkShaderModule: the created shader module
    """

    logging.debug("Loading shader module : %s", filename)

    with open(filename, "rb") as file:
        code = file.read()

    create_info = VkShaderModuleCreateInfo(
        codeSize = len(code),
        pCode    = code
    )

    return vkCreateShaderModule(device, create_info, None)
