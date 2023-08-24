"""Classes and functions related to vertices.

Classes:
    Vertex(pos: vec2, color: vec3)

Functions:
    create_vertex_buffer(physical_device: VkPhysicalDevice,
        device: VkDevice, queue: VkGraphicsQueue,
        command_pool: VkCommandPool, vertices: array,
        ) -> tuple[VkBuffer, VkDeviceMemory]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from glm import sizeof, vec2, vec3  # pylint: disable=no-name-in-module
from vulkan import (
    VK_BUFFER_USAGE_INDEX_BUFFER_BIT,
    VK_BUFFER_USAGE_TRANSFER_DST_BIT,
    VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
    VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
    VK_FORMAT_R32G32_SFLOAT,
    VK_FORMAT_R32G32B32_SFLOAT,
    VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_VERTEX_INPUT_RATE_VERTEX,
    VkVertexInputAttributeDescription,
    VkVertexInputBindingDescription,
    ffi,
    vkDestroyBuffer,
    vkFreeMemory,
    vkMapMemory,
    vkUnmapMemory,
)

from ._buffers import copy_buffer, create_buffer

if TYPE_CHECKING:
    from numpy import array

    from .hinting import (
        VkBuffer,
        VkCommandPool,
        VkDevice,
        VkDeviceMemory,
        VkGraphicsQueue,
        VkPhysicalDevice,
    )


class _VertexMeta(type):

    @property
    def size(cls) -> int:
        """The size of the structure."""
        return sizeof(type(cls.pos)) + sizeof(type(cls.color))

@dataclass
class Vertex(metaclass=_VertexMeta):
    """A vertex to display on screen.

    Attributes:
        pos: vec2
        color: vec3
        size: int

    Class methods:
        get_binding_description(cls) -> VkVertexInputBindingDescription
        get_attribut_descriptions(cls)-> tuple[
            VkVertexInputAttributeDescription,
            VkVertexInputAttributeDescription,
        ]
    """
    pos: vec2 = vec2()  # noqa: RUF009
    color: vec3 = vec3()  # noqa: RUF009

    POS_NUMBERS = 2
    COLOR_NUMBERS = 3

    def __iter__(self):
        self.__i = -1 # pylint: disable=attribute-defined-outside-init
        return self

    def __next__(self):
        self.__i += 1
        if self.__i < self.POS_NUMBERS:
            return self.pos[self.__i]
        if self.__i == self.POS_NUMBERS + self.COLOR_NUMBERS:
            raise StopIteration

        return self.color[self.__i-self.POS_NUMBERS]

    @classmethod
    def get_binding_description(cls) -> VkVertexInputBindingDescription:
        """Populate a VkVertexInputBindingDescription structure."""
        return VkVertexInputBindingDescription(
            binding   = 0,
            stride    = cls.size,
            inputRate = VK_VERTEX_INPUT_RATE_VERTEX,
        )

    @classmethod
    def get_attribut_descriptions(cls)-> tuple[
        VkVertexInputAttributeDescription,
        VkVertexInputAttributeDescription,
    ]:
        """Populate a tuple of VkVertexInputAttributeDescription structure."""
        return (
            VkVertexInputAttributeDescription(
                binding  = 0,
                location = 0,
                format   = VK_FORMAT_R32G32_SFLOAT,
                offset   = 0,
            ),
            VkVertexInputAttributeDescription(
                binding  = 0,
                location = 1,
                format   = VK_FORMAT_R32G32B32_SFLOAT,
                offset   = sizeof(type(cls.pos)),
            ),
        )

def create_vertex_buffer(
    physical_device: VkPhysicalDevice,
    device: VkDevice,
    queue: VkGraphicsQueue,
    command_pool: VkCommandPool,
    vertices: array,
) -> tuple[VkBuffer, VkDeviceMemory]:
    """Creates and returns the vertex buffer.

    Args:
        physical_device (VkPhysicalDevice): The physical device to
            which the buffer will be linked.
        device (VkDevice): The logical device to which the buffer
            will be linked.
        queue (VkGraphicsQueue): The queue to use.
        command_pool (VkCommandPool): The command pool to use.
        vertices (array): The vertices to write in the buffer.

    Returns:
        tuple[VkBuffer, VkDeviceMemory]: The created buffer and its memory.
    """
    staging_buffer, staging_buffer_memory = create_buffer(
        physical_device = physical_device,
        device          = device,
        size            = Vertex.size * len(vertices),
        usage           = VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
        properties      = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
                        | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    )

    staging_buffer_memory_location = vkMapMemory(
        device = device,
        memory = staging_buffer_memory,
        offset = 0,
        size   = Vertex.size * len(vertices),
        flags  = 0,
    )
    ffi.memmove(
        dest = staging_buffer_memory_location,
        src  = vertices,
        n    = vertices.nbytes,
    )
    vkUnmapMemory(
        device = device,
        memory = staging_buffer_memory,
    )

    vertex_buffer, vertex_buffer_memory = create_buffer(
        physical_device = physical_device,
        device          = device,
        size            = Vertex.size * len(vertices),
        usage           = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT
                        | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
        properties      = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
    )

    copy_buffer(
        device       = device,
        queue        = queue,
        command_pool = command_pool,
        src          = staging_buffer,
        dst          = vertex_buffer,
        size         = vertices.nbytes,
    )

    vkDestroyBuffer(device, staging_buffer, None)
    vkFreeMemory(device, staging_buffer_memory, None)

    return vertex_buffer, vertex_buffer_memory

def create_index_buffer(
    physical_device: VkPhysicalDevice,
    device: VkDevice,
    queue: VkGraphicsQueue,
    command_pool: VkCommandPool,
    indices: list[int],
) -> tuple[VkBuffer, VkDeviceMemory]:
    """Creates and returns the index buffer.

    Args:
        physical_device (VkPhysicalDevice): The physical device to
            which the buffer will be linked.
        device (VkDevice): The logical device to which the buffer
            will be linked.
        queue (VkGraphicsQueue): The queue to use.
        command_pool (VkCommandPool): The command pool to use.
        indices (array): The indices to write in the buffer.

    Returns:
        tuple[VkBuffer, VkDeviceMemory]: The created buffer and its memory.
    """
    staging_buffer, staging_buffer_memory = create_buffer(
        physical_device = physical_device,
        device          = device,
        size            = indices.nbytes,
        usage           = VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
        properties      = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
                        | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    )

    staging_buffer_memory_location = vkMapMemory(
        device = device,
        memory = staging_buffer_memory,
        offset = 0,
        size   = indices.nbytes,
        flags  = 0,
    )
    ffi.memmove(
        dest = staging_buffer_memory_location,
        src  = indices,
        n    = indices.nbytes,
    )
    vkUnmapMemory(
        device = device,
        memory = staging_buffer_memory,
    )

    index_buffer, index_buffer_memory = create_buffer(
        physical_device = physical_device,
        device          = device,
        size            = indices.nbytes,
        usage           = VK_BUFFER_USAGE_INDEX_BUFFER_BIT
                        | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
        properties      = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
    )

    copy_buffer(
        device       = device,
        queue        = queue,
        command_pool = command_pool,
        src          = staging_buffer,
        dst          = index_buffer,
        size         = indices.nbytes,
    )

    vkDestroyBuffer(device, staging_buffer, None)
    vkFreeMemory(device, staging_buffer_memory, None)

    return index_buffer, index_buffer_memory
