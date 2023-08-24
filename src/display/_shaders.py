"""Functions about shaders.

Functions:
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vulkan import (
    VkError,
    VkException,
    VkShaderModuleCreateInfo,
    vkCreateShaderModule,
)

from .errors import VulkanCreationError

if TYPE_CHECKING:
    from pathlib import Path

    from .hinting import VkDevice, VkShaderModule


def create_shader_module(device: VkDevice, filename: Path) -> VkShaderModule:
    """Load a shader.

    Args:
        device (VkDevice): The logical device to whick the shader will
        be linked.
        filename (Path): The shader filename.

    Raises:
        VulkanCreationError: The shader module creation failed.

    Returns:
        VkShaderModule: The created shader module.
    """
    logging.debug("Loading file %s", filename)

    with filename.open("rb") as file:
        code = file.read()

    create_info = VkShaderModuleCreateInfo(
        codeSize = len(code),
        pCode    = code,
    )

    try:
        return vkCreateShaderModule(device, create_info, None)
    except (VkError, VkException) as e:
        logging.exception("Failed to create the shader module !")
        raise VulkanCreationError from e
