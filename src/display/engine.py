"""
Module providing the display engine class
"""

import logging
from typing import List

from glfw import create_window, window_hint
from glfw import init as glfw_init
from glfw import terminate as glfw_terminate
from glfw.GLFW import GLFW_CLIENT_API, GLFW_NO_API, GLFW_RESIZABLE, GLFW_FALSE
from vulkan import VkExtent2D, vkDestroyDevice, vkDestroyInstance, vkDestroyImageView

from src.consts import DEBUG

from .device import chose_physical_device, make_logical_device
from .hinting import (
    VkDebugReportCallbackEXT,
    VkDevice,
    VkGraphicsQueue,
    VkInstance,
    VkPhysicalDevice,
    VkPresentQueue,
    VkSurface,
    VkSurfaceFormatKHR,
    VkSwapchainKHR,
    Window,
)
from .instance import destroy_surface, make_instance, make_surface
from .queue_families import QueueFamilyIndices, get_queues
from .swapchain import SwapChainFrame, make_swapchain, destroy_swapchain
from .validation_layers import destroy_debug_messenger, make_debug_messenger


class Engine:
    """
    Handle a glfw window with vulkan
    """

    def __init__(self, width: int, height: int, title: str):

        self.width = width
        self.height = height
        self.title = title

        # Window
        self.window: Window = None
        self.__build_glfw_window()

        # Instance
        self.__instance: VkInstance = None
        self.__debug_messenger: VkDebugReportCallbackEXT = None
        self.__surface: VkSurface = None
        self.__make_instance()

        # Devices
        self.__physical_device: VkPhysicalDevice = None
        self.__device: VkDevice = None
        self.__queue_families_indices: QueueFamilyIndices = None
        self.__graphics_queue: VkGraphicsQueue = None
        self.__present_queue: VkPresentQueue = None
        self.__make_devices()

        # Swapchain
        self.__swapchain: VkSwapchainKHR = None
        self.__swapchain_frames: List[SwapChainFrame] = []
        self.__swapchain_format: VkSurfaceFormatKHR = None
        self.__swapchain_extent: VkExtent2D = None
        self.__make_swapchain()

    def __build_glfw_window(self):
        glfw_init()

        window_hint(GLFW_CLIENT_API, GLFW_NO_API)
        window_hint(GLFW_RESIZABLE, GLFW_FALSE)

        self.window = create_window(
            self.width,self.height,
            self.title,
            None,
            None
        )

        if self.window:
            logging.debug(
                "Successfully open a GLFW window : %s (w: %s, h: %s)",
                self.title, self.width, self.height
            )
        else:
            logging.error("Failed to create the GLFW window")

    def __make_instance(self):
        self.__instance = make_instance(self.title)

        if DEBUG:
            self.__debug_messenger = make_debug_messenger(self.__instance)

        self.__surface = make_surface(self.__instance, self.window)

    def __make_devices(self):
        self.__physical_device = chose_physical_device(self.__instance)
        self.__device, self.__queue_families_indices = make_logical_device(
            self.__instance,
            self.__physical_device,
            self.__surface
        )
        self.__graphics_queue, self.__present_queue = get_queues(
            self.__device,
            self.__queue_families_indices
        )

    def __make_swapchain(self):
        self.__swapchain, self.__swapchain_frames, \
        self.__swapchain_format, self.__swapchain_extent = make_swapchain(
            self.__instance,
            self.__device,
            self.__physical_device,
            self.__surface,
            self.width,
            self.height,
            self.__queue_families_indices
        )

    def close(self):
        """
        Close the GLFW window and clean Vulkan objects
        """
        logging.debug("Destroying objects")

        # Swapchain
        for frame in self.__swapchain_frames:
            vkDestroyImageView(self.__device, frame.image_view, None)
        destroy_swapchain(self.__device, self.__swapchain)

        # Device
        vkDestroyDevice(self.__device, None)

        # Instance
        destroy_surface(self.__instance, self.__surface)
        destroy_debug_messenger(self.__instance, self.__debug_messenger)
        vkDestroyInstance(self.__instance, None)

        # Window
        logging.debug("Closing GLFW window")
        glfw_terminate()
