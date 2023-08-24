"""The display engine.

Classes:
    Engine(width: int, height: iny, title: str)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from glfw import (
    create_window,
    destroy_window,
    get_window_size,
    get_window_user_pointer,
    set_framebuffer_size_callback,
    set_window_user_pointer,
    wait_events,
    window_hint,
)
from glfw import init as glfw_init
from glfw import terminate as glfw_terminate
from glfw.GLFW import GLFW_CLIENT_API, GLFW_NO_API, GLFW_RESIZABLE, GLFW_TRUE
from glm import vec2, vec3  # pylint: disable=no-name-in-module
from numpy import array, float32, uint32
from vulkan import (
    VK_INDEX_TYPE_UINT32,
    VK_NULL_HANDLE,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_TRUE,
    VkError,
    VkErrorOutOfDateKhr,
    VkException,
    VkExtent2D,
    VkPresentInfoKHR,
    VkRect2D,
    VkSubmitInfo,
    VkSuboptimalKhr,
    VkViewport,
    vkCmdBindIndexBuffer,
    vkCmdBindPipeline,
    vkCmdBindVertexBuffers,
    vkCmdDrawIndexed,
    vkCmdSetScissor,
    vkCmdSetViewport,
    vkDestroyBuffer,
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
    vkFreeCommandBuffers,
    vkFreeMemory,
    vkGetDeviceProcAddr,
    vkQueueSubmit,
    vkResetCommandBuffer,
    vkResetFences,
    vkWaitForFences,
)

from ._commands import (
    CommandBufferManager,
    create_command_buffers,
    create_command_pool,
)
from ._consts import RENDER_FENCE_TIMEOUT, VALIDATION_LAYERS_ENABLED
from ._device import create_logical_device, pick_physical_device
from ._graphics_pipeline import (
    RenderPassManager,
    create_graphics_pipeline,
    create_pipeline_layout,
    create_render_pass,
)
from ._images import create_frame_buffers, create_image_views
from ._instance import create_instance, create_surface, destroy_surface
from ._queues import get_queues
from ._swapchain import create_swapchain, destroy_swapchain
from ._sync import create_fences, create_semaphores
from ._validation_layers import destroy_debug_messenger, setup_debug_messenger
from ._vertex import Vertex, create_index_buffer, create_vertex_buffer
from .errors import QueueSubmitError

if TYPE_CHECKING:
    from .hinting import (
        GLFWWindow,
        VkBuffer,
        VkCommandBuffer,
        VkCommandPool,
        VkDebugUtilsMessengerEXT,
        VkDevice,
        VkDeviceMemory,
        VkFence,
        VkFormat,
        VkFramebuffer,
        VkGraphicsQueue,
        VkImage,
        VkImageView,
        VkInstance,
        VkPhysicalDevice,
        VkPipeline,
        VkPipelineLayout,
        VkPresentQueue,
        VkRenderPass,
        VkSemaphore,
        VkSurfaceKHR,
        VkSwapchainKHR,
    )

vertices = array([
    *Vertex(vec2(-0.5, -0.5), vec3(1, 0, 0)),
    *Vertex(vec2( 0.5, -0.5), vec3(0, 1, 0)),
    *Vertex(vec2( 0.5,  0.5), vec3(0, 0, 1)),
    *Vertex(vec2(-0.5,  0.5), vec3(1, 1, 1)),
], dtype=float32)

indices = array([
    0, 1, 2,
    2, 3, 0,
], dtype=uint32)

class Engine:
    """Handle a GLFW window with vulkan.

    Attributes:
        title: str
        window: GLFWWindow

    Methods:
        cleanup()
    """

    def __init__(self, width: int, height: int, title: str):
        self.__width = width
        self.__height = height
        self.title = title

        self.__cleaned_up = False
        self.frame_buffer_resized = False

        self.window: GLFWWindow = None

        self.__instance: VkInstance = None
        self.__callback: VkDebugUtilsMessengerEXT = None
        self.__surface: VkSurfaceKHR = None

        self.__physical_device: VkPhysicalDevice = None
        self.__device: VkDevice = None
        self.__graphics_queue: VkGraphicsQueue = None
        self.__present_queue: VkPresentQueue = None
        self.__swapchain: VkSwapchainKHR = None
        self.__swapchain_images: list[VkImage] = None
        self.__swapchain_image_format: VkFormat = None
        self.__swapchain_extent: VkExtent2D = None
        self.__max_frames_in_flight: int = None
        self.__current_frame: int = None
        self.__swapchain_image_views: list[VkImageView] = None
        self.__pipeline_layout: VkPipelineLayout = None
        self.__render_pass: VkRenderPass = None
        self.__graphics_pipeline: VkPipeline = None
        self.__swapchain_frame_buffers: list[VkFramebuffer] = None
        self.__command_pool: VkCommandPool = None
        self.__vertex_buffer: VkBuffer = None
        self.__vertex_buffer_memory: VkDeviceMemory = None
        self.__index_buffer: VkBuffer = None
        self.__index_buffer_memory: VkDeviceMemory = None
        self.__command_buffers: list[VkCommandBuffer] = None
        self.__image_available_semaphores: list[VkSemaphore] = None
        self.__render_finished_semaphores: list[VkSemaphore] = None
        self.__in_flight_fences: list[VkFence] = None
        self.__images_in_flight: list[VkFence] = None

        self.__init_window()
        self.__init_vulkan()

    @staticmethod
    def __frame_buffer_resize_callback(
        window: GLFWWindow,
        width: int,  # pylint: disable=unused-argument # noqa: ARG004
        height: int,  # pylint: disable=unused-argument # noqa: ARG004
    ) -> None:
        self = get_window_user_pointer(window)[0]
        self.frame_buffer_resized = True

    def __init_window(self) -> None:
        glfw_init()

        window_hint(GLFW_CLIENT_API, GLFW_NO_API)
        window_hint(GLFW_RESIZABLE, GLFW_TRUE)

        self.window = create_window(
            self.__width, self.__height,
            self.title,
            None,
            None,
        )

        if self.window:
            logging.debug(
                "Successfully open a GLFW window : %s (w: %s, h: %s)",
                self.title, self.__width, self.__height,
            )
        else:
            logging.error("Failed to create the GLFW window")

        set_window_user_pointer(self.window, [self])
        set_framebuffer_size_callback(
            self.window, self.__frame_buffer_resize_callback)

    def __init_vulkan(self) -> None:
        # Instance
        self.__instance = create_instance(
            application_name = self.title,
        )

        if VALIDATION_LAYERS_ENABLED:
            self.__callback = setup_debug_messenger(
                instance = self.__instance,
            )

        self.__surface = create_surface(
            instance = self.__instance,
            window   = self.window,
        )

        # Device
        self.__physical_device = pick_physical_device(
            instance = self.__instance,
            surface  = self.__surface,
        )

        self.__device = create_logical_device(
            instance        = self.__instance,
            surface         = self.__surface,
            physical_device = self.__physical_device,
        )

        self.__graphics_queue, self.__present_queue = get_queues(
            instance        = self.__instance,
            surface         = self.__surface,
            physical_device = self.__physical_device,
            device          = self.__device,
        )

        (
            self.__swapchain,
            self.__swapchain_images,
            self.__swapchain_image_format,
            self.__swapchain_extent,
        ) = create_swapchain(
            instance        = self.__instance,
            surface         = self.__surface,
            physical_device = self.__physical_device,
            device          = self.__device,
            width           = self.__width,
            height          = self.__height,
        )

        self.__max_frames_in_flight = len(self.__swapchain_images)
        self.__current_frame = 0

        self.__swapchain_image_views = create_image_views(
            device                 = self.__device,
            swapchain_images       = self.__swapchain_images,
            swapchain_image_format = self.__swapchain_image_format,
        )

        self.__pipeline_layout = create_pipeline_layout(
            device = self.__device,
        )
        self.__render_pass = create_render_pass(
            device       = self.__device,
            image_format = self.__swapchain_image_format,
        )
        self.__graphics_pipeline = create_graphics_pipeline(
            device          = self.__device,
            extent          = self.__swapchain_extent,
            pipeline_layout = self.__pipeline_layout,
            render_pass     = self.__render_pass,
        )

        self.__swapchain_frame_buffers = create_frame_buffers(
            device      = self.__device,
            extent      = self.__swapchain_extent,
            image_views = self.__swapchain_image_views,
            render_pass = self.__render_pass,
        )

        self.__command_pool = create_command_pool(
            instance        = self.__instance,
            surface         = self.__surface,
            physical_device = self.__physical_device,
            device          = self.__device,
        )

        (
            self.__vertex_buffer,
            self.__vertex_buffer_memory,
        ) = create_vertex_buffer(
            physical_device = self.__physical_device,
            device          = self.__device,
            queue           = self.__graphics_queue,
            command_pool    = self.__command_pool,
            vertices        = vertices,
        )

        (
            self.__index_buffer,
            self.__index_buffer_memory,
        ) = create_index_buffer(
            physical_device = self.__physical_device,
            device          = self.__device,
            queue           = self.__graphics_queue,
            command_pool    = self.__command_pool,
            indices        = indices,
        )

        self.__command_buffers = create_command_buffers(
            device        = self.__device,
            frame_buffers = self.__swapchain_frame_buffers,
            command_pool  = self.__command_pool,
        )

        self.__image_available_semaphores = create_semaphores(
            device = self.__device,
            n      = self.__max_frames_in_flight,
        )
        self.__render_finished_semaphores = create_semaphores(
            device = self.__device,
            n      = self.__max_frames_in_flight,
        )
        self.__in_flight_fences = create_fences(
            device = self.__device,
            n      = self.__max_frames_in_flight,
        )
        self.__images_in_flight = [
            VK_NULL_HANDLE
            for _ in range(self.__max_frames_in_flight)
        ]

    def __recreate_swapchain(self) -> None:
        self.__width, self.__height = 0, 0
        while self.__width * self.__height == 0:
            self.__width, self.__height = get_window_size(self.window)
            wait_events()

        vkDeviceWaitIdle(self.__device)

        self.__cleanup_swapchain()

        (
            self.__swapchain,
            self.__swapchain_images,
            self.__swapchain_image_format,
            self.__swapchain_extent,
        ) = create_swapchain(
            instance        = self.__instance,
            surface         = self.__surface,
            physical_device = self.__physical_device,
            device          = self.__device,
            width           = self.__width,
            height          = self.__height,
        )

        self.__swapchain_image_views = create_image_views(
            device                 = self.__device,
            swapchain_images       = self.__swapchain_images,
            swapchain_image_format = self.__swapchain_image_format,
        )

        self.__pipeline_layout = create_pipeline_layout(
            device = self.__device,
        )
        self.__render_pass = create_render_pass(
            device       = self.__device,
            image_format = self.__swapchain_image_format,
        )
        self.__graphics_pipeline = create_graphics_pipeline(
            device          = self.__device,
            extent          = self.__swapchain_extent,
            pipeline_layout = self.__pipeline_layout,
            render_pass     = self.__render_pass,
        )

        self.__swapchain_frame_buffers = create_frame_buffers(
            device      = self.__device,
            extent      = self.__swapchain_extent,
            image_views = self.__swapchain_image_views,
            render_pass = self.__render_pass,
        )

        self.__command_buffers = create_command_buffers(
            device        = self.__device,
            frame_buffers = self.__swapchain_frame_buffers,
            command_pool  = self.__command_pool,
        )

        self.frame_buffer_resized = False

    def __record_command_buffer(
        self,
        command_buffer: VkCommandBuffer,
        image_index: int,
    ) -> None:
        with CommandBufferManager(command_buffer), RenderPassManager(
            extent         = self.__swapchain_extent,
            render_pass    = self.__render_pass,
            frame_buffer   = self.__swapchain_frame_buffers[image_index],
            command_buffer = command_buffer,
        ):
            vkCmdBindPipeline(
                commandBuffer     = command_buffer,
                pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS,
                pipeline          = self.__graphics_pipeline,
            )

            # Dynamic viewport
            viewport = VkViewport(
                x = 0,
                y = 0,
                width = self.__swapchain_extent.width,
                height = self.__swapchain_extent.height,
                minDepth = 0,
                maxDepth = 1,
            )
            vkCmdSetViewport(command_buffer, 0, 1, viewport)

            scissor = VkRect2D(
                offset = [0, 0],
                extent = self.__swapchain_extent,
            )
            vkCmdSetScissor(command_buffer, 0, 1, scissor)

            # Vertices
            vkCmdBindVertexBuffers(
                commandBuffer = command_buffer,
                firstBinding  = 0,
                bindingCount  = 1,
                pBuffers      = [self.__vertex_buffer],
                pOffsets      = [0],
            )

            vkCmdBindIndexBuffer(
                commandBuffer = command_buffer,
                buffer        = self.__index_buffer,
                offset        = 0,
                indexType     = VK_INDEX_TYPE_UINT32,
            )

            vkCmdDrawIndexed(command_buffer, len(indices), 1, 0, 0, 0)

    def render(self) -> None:
        """Render the scene to the screen.

        Raises:
            QueueSubmitError: The command submition to the graphics
                queue failed.
        """
        vkAcquireNextImageKHR = vkGetDeviceProcAddr(
            self.__device, "vkAcquireNextImageKHR")
        vkQueuePresentKHR = vkGetDeviceProcAddr(
            self.__device, "vkQueuePresentKHR")

        in_flight_fence = self.__in_flight_fences[self.__current_frame]
        image_available_semaphore = \
            self.__image_available_semaphores[self.__current_frame]
        render_finished_semaphore = \
            self.__render_finished_semaphores[self.__current_frame]

        vkWaitForFences(
            device     = self.__device,
            fenceCount = 1,
            pFences    = [in_flight_fence],
            waitAll    = VK_TRUE,
            timeout    = RENDER_FENCE_TIMEOUT,
        )

        try:
            image_index = vkAcquireNextImageKHR(
                device    = self.__device,
                swapchain = self.__swapchain,
                timeout   = RENDER_FENCE_TIMEOUT,
                semaphore = image_available_semaphore,
                fence     = VK_NULL_HANDLE,
            )
        except VkErrorOutOfDateKhr:
            self.__recreate_swapchain()
            return

        image_in_flight = self.__images_in_flight[image_index]
        if image_in_flight != VK_NULL_HANDLE:
            vkWaitForFences(
                device     = self.__device,
                fenceCount = 1,
                pFences    = [image_in_flight],
                waitAll    = VK_TRUE,
                timeout    = RENDER_FENCE_TIMEOUT,
            )

        self.__images_in_flight[image_index] = in_flight_fence

        command_buffer = self.__command_buffers[image_index]
        vkResetCommandBuffer(command_buffer, 0)
        self.__record_command_buffer(command_buffer, image_index)

        submit_info = VkSubmitInfo(
            waitSemaphoreCount   = 1,
            pWaitSemaphores      = [image_available_semaphore],
            pWaitDstStageMask    = [
                VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT],
            commandBufferCount   = 1,
            pCommandBuffers      = [command_buffer],
            signalSemaphoreCount = 1,
            pSignalSemaphores    = [render_finished_semaphore],
        )

        vkResetFences(self.__device, 1, [in_flight_fence])

        try:
            vkQueueSubmit(
                queue       = self.__graphics_queue,
                submitCount = 1,
                pSubmits    = submit_info,
                fence       = in_flight_fence,
            )
        except (VkError, VkException) as e:
            logging.exception("Failed to submit the command !")
            raise QueueSubmitError from e

        present_info = VkPresentInfoKHR(
            waitSemaphoreCount = 1,
            pWaitSemaphores    = [render_finished_semaphore],
            swapchainCount     = 1,
            pSwapchains        = [self.__swapchain],
            pImageIndices      = [image_index],
        )

        try:
            vkQueuePresentKHR(self.__present_queue, present_info)
        except (VkErrorOutOfDateKhr, VkSuboptimalKhr):
            self.__recreate_swapchain()


        if self.frame_buffer_resized:
            self.__recreate_swapchain()

        self.__current_frame += 1
        self.__current_frame %= self.__max_frames_in_flight

    def cleanup(self) -> None:
        """Close the GLFW window and clean Vulkan objects."""
        self.__cleaned_up = True

        logging.info("Cleaning up")

        self.__cleanup_glfw()
        self.__cleanup_vulkan()

    def __del__(self):
        if not self.__cleaned_up:
            self.cleanup()

    def __cleanup_glfw(self) -> None:
        destroy_window(self.window)
        glfw_terminate()

    def __cleanup_swapchain(self) -> None:
        for frame_buffer in self.__swapchain_frame_buffers:
            vkDestroyFramebuffer(self.__device, frame_buffer, None)

        vkFreeCommandBuffers(
            self.__device, self.__command_pool,
            len(self.__command_buffers), self.__command_buffers)

        vkDestroyPipeline(self.__device, self.__graphics_pipeline, None)
        vkDestroyRenderPass(self.__device, self.__render_pass, None)
        vkDestroyPipelineLayout(
            self.__device, self.__pipeline_layout, None)

        for image_view in self.__swapchain_image_views:
            vkDestroyImageView(self.__device, image_view, None)

        destroy_swapchain(self.__device, self.__swapchain)

    def __cleanup_vulkan(self) -> None:
        vkDeviceWaitIdle(self.__device)

        # Device
        self.__cleanup_swapchain()

        vkDestroyBuffer(self.__device, self.__index_buffer, None)
        vkFreeMemory(self.__device, self.__index_buffer_memory, None)

        vkDestroyBuffer(self.__device, self.__vertex_buffer, None)
        vkFreeMemory(self.__device, self.__vertex_buffer_memory, None)

        for i in range(self.__max_frames_in_flight):
            vkDestroySemaphore(
                self.__device, self.__image_available_semaphores[i], None)
            vkDestroySemaphore(
                self.__device, self.__render_finished_semaphores[i], None)
            vkDestroyFence(
                self.__device, self.__in_flight_fences[i], None)

        vkDestroyCommandPool(self.__device, self.__command_pool, None)

        vkDestroyDevice(self.__device, None)

        # Instance
        destroy_surface(self.__instance, self.__surface)

        if VALIDATION_LAYERS_ENABLED:
            destroy_debug_messenger(self.__instance, self.__callback)

        vkDestroyInstance(self.__instance, None)
