"""
Contains the TriangleMesh class
"""

from numpy import array, float32
from vulkan import (
    VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,
    vkDestroyBuffer,
    vkFreeMemory,
    vkMapMemory,
    vkUnmapMemory,
)
from vulkan import ffi as c_link

from .hinting import VkDevice, VkPhysicalDevice
from .memory import create_buffer


class TriangleMesh:
    """
    Represent a triangle on screen
    """

    def __init__(self, device: VkDevice, physical_device: VkPhysicalDevice):

        self.device = device

        vertices = array(
            (
                 0.00, -0.05, 0.00, 1.0, 0.0,
                 0.05,  0.05, 0.00, 1.0, 0.0,
                -0.05,  0.05, 0.00, 1.0, 0.0,
            ),
            dtype = float32
        )

        self.vertex_buffer, self.__vertex_buffer_memory = create_buffer(
            device = device,
            physical_device = physical_device,
            size = vertices.nbytes,
            usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT
        )

        memory_location = vkMapMemory(
            device = device,
            memory = self.__vertex_buffer_memory,
            offset = 0,
            size   = vertices.nbytes,
            flags  = 0
        )

        c_link.memmove(
            dest = memory_location,
            src  = vertices,
            n    = vertices.nbytes
        )

        vkUnmapMemory(
            device = device,
            memory = self.__vertex_buffer_memory
        )

    def destroy(self):
        """
        Cleanup the vertex buffer and free its memory
        """

        vkDestroyBuffer(self.device, self.vertex_buffer, None)
        vkFreeMemory(self.device, self.__vertex_buffer_memory, None)
