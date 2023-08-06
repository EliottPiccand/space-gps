"""
Module providing the display engine class
"""

import logging

from glfw import create_window
from glfw import init as glfw_init
from glfw import terminate as glfw_terminate
from glfw import window_hint
from glfw.GLFW import GLFW_CLIENT_API, GLFW_NO_API, GLFW_RESIZABLE, GLFW_TRUE
from vulkan import vkDestroyInstance

from src.consts import DEBUG

from .hinting import VkInstance, Window, VkDebugReportCallbackEXT
from .instance import make_instance
from .validation_layers import make_debug_messenger, destroy_debug_messenger


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
        self.__make_instance()

    def __build_glfw_window(self):
        glfw_init()

        window_hint(GLFW_CLIENT_API, GLFW_NO_API)
        window_hint(GLFW_RESIZABLE, GLFW_TRUE)

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
            logging.debug("Failed to create the GLFW window")

    def __make_instance(self):
        self.__instance = make_instance(self.title)

        if DEBUG:
            self.__debug_messenger = make_debug_messenger(self.__instance)

    def close(self):
        """
        Close the GLFW window and clean Vulkan objects
        """
        logging.debug("Destroying objects")       

        # Instance
        destroy_debug_messenger(self.__instance, self.__debug_messenger)
        vkDestroyInstance(self.__instance, None)

        # Window
        logging.debug("Closing GLFW window")
        glfw_terminate()
