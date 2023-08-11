"""
Contains the all mesh class
"""

from typing import Tuple

from numpy import array, float32
from vulkan import (
    VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
    VK_BUFFER_USAGE_TRANSFER_DST_BIT,
    VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
    vkDestroyBuffer,
    vkFreeMemory,
    vkMapMemory,
    vkUnmapMemory,
)
from vulkan import ffi as c_link

from .hinting import VkDevice, VkPhysicalDevice, VkCommandBuffer, VkGraphicsQueue
from .memory import create_buffer, copy_buffer


class Mesh:
    """
    Represent a 2d polygon on screen
    """

    points: Tuple[Tuple[float, float]]
    color: Tuple[float, float, float]

    RADIUS = 0.05

    def __init__(
        self,
        device: VkDevice,
        physical_device: VkPhysicalDevice,
        command_buffer: VkCommandBuffer,
        queue: VkGraphicsQueue
    ):
        self.device = device

        # Build polygon
        np_vertices = []
        for x, y in self.points:
            np_vertices.append(x * self.RADIUS)
            np_vertices.append(y * self.RADIUS)
            np_vertices.append(self.color[0])
            np_vertices.append(self.color[1])
            np_vertices.append(self.color[2])

        self.vertices = array(np_vertices, dtype=float32)

        # Create vertex buffer
        staging_buffer, staging_buffer_memory = create_buffer(
            device               = device,
            physical_device      = physical_device,
            size                 = self.vertices.nbytes,
            usage                = VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
            requested_properties = VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
                                 | VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT
        )

        memory_location = vkMapMemory(
            device = device,
            memory = staging_buffer_memory,
            offset = 0,
            size   = self.vertices.nbytes,
            flags  = 0
        )

        c_link.memmove(
            dest = memory_location,
            src  = self.vertices,
            n    = self.vertices.nbytes
        )

        vkUnmapMemory(
            device = device,
            memory = staging_buffer_memory
        )

        self.vertex_buffer, self.__vertex_buffer_memory = create_buffer(
            device               = device,
            physical_device      = physical_device,
            size                 = self.vertices.nbytes,
            usage                = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT
                                 | VK_BUFFER_USAGE_TRANSFER_DST_BIT,
            requested_properties = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT
        )

        copy_buffer(
            src = staging_buffer,
            dst = self.vertex_buffer,
            size = self.vertices.nbytes,
            queue = queue,
            command_buffer = command_buffer
        )

        vkDestroyBuffer(self.device, staging_buffer, None)
        vkFreeMemory(self.device, staging_buffer_memory, None)

    def destroy(self):
        """
        Cleanup the vertex buffer and free its memory
        """

        vkDestroyBuffer(self.device, self.vertex_buffer, None)
        vkFreeMemory(self.device, self.__vertex_buffer_memory, None)

class TriangleMesh(Mesh):
    """
    Represent a triangle on screen
    """

    color = 0, 1, 0

    points = (
        ( 1  ,  0   ),
        (-0.5,  0.87),
        (-0.5, -0.87),
    )

class SquareMesh(Mesh):
    """
    Represent a square on screen
    """

    color = 1, 0, 0

    points = (
        ( 1,  0),
        ( 0,  1),
        (-1,  0),

        ( 1,  0),
        (-1,  0),
        ( 0, -1),
    )

class PentagonMesh(Mesh):
    """
    Represent a pentagon on screen
    """

    color = 0, 0, 1

    points = (
        ( 1   ,  0   ),
        ( 0.31,  0.95),
        (-0.81,  0.59),

        ( 1   ,  0   ),
        (-0.81,  0.59),
        (-0.81, -0.59),

        ( 1   ,  0   ),
        (-0.81, -0.59),
        ( 0.31, -0.95),
    )
