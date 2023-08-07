"""
Module providing the display engine class
"""

import logging
from typing import List

from glfw import create_window, window_hint
from glfw import init as glfw_init
from glfw import terminate as glfw_terminate
from glfw.GLFW import GLFW_CLIENT_API, GLFW_FALSE, GLFW_NO_API, GLFW_RESIZABLE
from vulkan import (
    VK_NULL_HANDLE,
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_TRUE,
    VkError,
    VkException,
    VkExtent2D,
    VkPresentInfoKHR,
    VkSubmitInfo,
    vkDestroyCommandPool,
    vkDestroyDevice,
    vkDestroyFence,
    vkDestroyFramebuffer,
    vkDestroyImageView,
    vkDestroyInstance,
    vkDestroyPipeline,
    vkDestroyPipelineLayout,
    vkDestroyRenderPass,
    vkDestroySemaphore,
    vkDeviceWaitIdle,
    vkGetDeviceProcAddr,
    vkQueueSubmit,
    vkResetCommandBuffer,
    vkResetFences,
    vkWaitForFences,
)

from src.consts import BASE_DIR, DEBUG

from .commands import make_command_buffers, make_command_pool, record_draw_command
from .consts import FRAG_SHADER_PATH, RENDER_FENCE_TIMEOUT, VERT_SHADER_PATH
from .device import chose_physical_device, make_logical_device
from .frame_buffer import make_frame_buffers
from .graphics_pipeline import make_graphics_pipeline
from .hinting import (
    VkCommandBuffer,
    VkCommandPool,
    VkDebugReportCallbackEXT,
    VkDevice,
    VkGraphicsQueue,
    VkInstance,
    VkPhysicalDevice,
    VkPipeline,
    VkPipelineLayout,
    VkPresentQueue,
    VkRenderPass,
    VkSurface,
    VkSurfaceFormatKHR,
    VkSwapchainKHR,
    Window,
)
from .instance import destroy_surface, make_instance, make_surface
from .queue_families import QueueFamilyIndices, get_queues
from .swapchain import SwapChainFrame, destroy_swapchain, make_swapchain
from .sync import make_fence, make_semaphore
from .validation_layers import destroy_debug_messenger, make_debug_messenger
from .scene import Scene


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
        self.__swapchain_frames: List[SwapChainFrame] = None
        self.__swapchain_format: VkSurfaceFormatKHR = None
        self.__swapchain_extent: VkExtent2D = None
        self.__max_frames_in_flight: int = None
        self.__current_frame_number = 0
        self.__make_swapchain()

        # Graphics pipeline
        self.__pipeline_layout: VkPipelineLayout = None
        self.__render_pass: VkRenderPass = None
        self.__graphics_pipeline: VkPipeline = None
        self.__make_graphics_pipeline()

        # Frame buffers
        self.__make_frame_buffers()

        # Commands
        self.__command_pool: VkCommandPool = None
        self.__command_buffer: VkCommandBuffer = None
        self.__make_commands()

        # Semaphores & Fences
        self.__make_frame_sync()

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

        self.__max_frames_in_flight = len(self.__swapchain_frames)

    def __make_graphics_pipeline(self):
        self.__pipeline_layout, self.__render_pass, self.__graphics_pipeline = \
        make_graphics_pipeline(
            self.__device,
            self.__swapchain_extent,
            self.__swapchain_format,
            BASE_DIR / VERT_SHADER_PATH,
            BASE_DIR / FRAG_SHADER_PATH
        )

    def __make_frame_buffers(self):
        make_frame_buffers(
            self.__device,
            self.__render_pass,
            self.__swapchain_extent,
            self.__swapchain_frames
        )

    def __make_commands(self):
        self.__command_pool = make_command_pool(
            self.__device,
            self.__queue_families_indices
        )

        self.__command_buffer = make_command_buffers(
            self.__device,
            self.__command_pool,
            self.__swapchain_frames
        )

    def __make_frame_sync(self):
        for frame in self.__swapchain_frames:
            frame.in_flight_fence = make_fence(self.__device)
            frame.image_available_semaphore = make_semaphore(self.__device)
            frame.render_finished_semaphore = make_semaphore(self.__device)

    def render(self, scene: Scene):
        """
        Render the scene to the screen
        """

        vkAcquireNextImageKHR = vkGetDeviceProcAddr(
            self.__device, "vkAcquireNextImageKHR")
        vkQueuePresentKHR = vkGetDeviceProcAddr(
            self.__device, "vkQueuePresentKHR")

        in_flight_fence = \
            self.__swapchain_frames[self.__current_frame_number].in_flight_fence
        image_available_semaphore = \
            self.__swapchain_frames[self.__current_frame_number].image_available_semaphore
        render_finished_semaphore = \
            self.__swapchain_frames[self.__current_frame_number].render_finished_semaphore

        vkWaitForFences(
            device     = self.__device,
            fenceCount = 1,
            pFences    = [in_flight_fence],
            waitAll    = VK_TRUE,
            timeout    = RENDER_FENCE_TIMEOUT
        )
        vkResetFences(self.__device, 1, [in_flight_fence])


        frame_index = vkAcquireNextImageKHR(
            device    = self.__device,
            swapchain = self.__swapchain,
            timeout   = RENDER_FENCE_TIMEOUT,
            semaphore = image_available_semaphore,
            fence     = VK_NULL_HANDLE
        )

        command_buffer = self.__swapchain_frames[frame_index].command_buffer
        vkResetCommandBuffer(command_buffer, 0)

        record_draw_command(
            pipeline_layout   = self.__pipeline_layout,
            render_pass       = self.__render_pass,
            frame_buffer      = self.__swapchain_frames[frame_index].frame_buffer,
            swapchain_extent  = self.__swapchain_extent,
            graphics_pipeline = self.__graphics_pipeline,
            command_buffer    = command_buffer,
            scene             = scene
        )

        submit_info = VkSubmitInfo(
            waitSemaphoreCount   = 1,
            pWaitSemaphores      = [image_available_semaphore],
            pWaitDstStageMask    = [VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT],
            commandBufferCount   = 1,
            pCommandBuffers      = [command_buffer],
            signalSemaphoreCount = 1,
            pSignalSemaphores    = [render_finished_semaphore]
        )

        try:
            vkQueueSubmit(self.__graphics_queue, 1, submit_info, in_flight_fence)
        except (VkError, VkException):
            logging.error("Failed to submit draw commands")

        present_info = VkPresentInfoKHR(
            waitSemaphoreCount = 1,
            pWaitSemaphores    = [render_finished_semaphore],
            swapchainCount     = 1,
            pSwapchains        = [self.__swapchain],
            pImageIndices      = [frame_index]
        )

        vkQueuePresentKHR(self.__present_queue, present_info)

        self.__current_frame_number += 1
        self.__current_frame_number %= self.__max_frames_in_flight

    def close(self):
        """
        Close the GLFW window and clean Vulkan objects
        """
        logging.info("Waiting for device to cleanup")
        vkDeviceWaitIdle(self.__device)

        logging.debug("Destroying objects")

        # Commands
        vkDestroyCommandPool(self.__device, self.__command_pool, None)

        # Graphics pipeline
        vkDestroyPipeline(self.__device, self.__graphics_pipeline, None)
        vkDestroyRenderPass(self.__device, self.__render_pass, None)
        vkDestroyPipelineLayout(self.__device, self.__pipeline_layout, None)

        # Swapchain
        for frame in self.__swapchain_frames:
            vkDestroyImageView(self.__device, frame.image_view, None)
            vkDestroyFramebuffer(self.__device, frame.frame_buffer, None)

            vkDestroySemaphore(self.__device, frame.render_finished_semaphore, None)
            vkDestroySemaphore(self.__device, frame.image_available_semaphore, None)
            vkDestroyFence(self.__device, frame.in_flight_fence, None)

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
