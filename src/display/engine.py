"""
Module providing the display engine class
"""

import logging
from typing import List

from glfw import create_window, get_window_size, wait_events, window_hint
from glfw import init as glfw_init
from glfw import terminate as glfw_terminate
from glfw.GLFW import GLFW_CLIENT_API, GLFW_NO_API, GLFW_RESIZABLE, GLFW_TRUE
from numpy import array, float32
from pyrr import matrix44
from vulkan import (
    VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
    VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
    VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
    VK_NULL_HANDLE,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
    VK_SHADER_STAGE_FRAGMENT_BIT,
    VK_SHADER_STAGE_VERTEX_BIT,
    VK_SUBPASS_CONTENTS_INLINE,
    VK_TRUE,
    VkClearValue,
    VkError,
    VkErrorOutOfDateKhr,
    VkException,
    VkExtent2D,
    VkPresentInfoKHR,
    VkRenderPassBeginInfo,
    VkSubmitInfo,
    vkCmdBindDescriptorSets,
    vkCmdBindPipeline,
    vkCmdBindVertexBuffers,
    vkCmdDraw,
    vkDestroyBuffer,
    vkDestroyCommandPool,
    vkDestroyDescriptorPool,
    vkDestroyDescriptorSetLayout,
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
    vkFreeMemory,
    vkGetDeviceProcAddr,
    vkQueueSubmit,
    vkResetCommandBuffer,
    vkResetFences,
    vkUnmapMemory,
    vkWaitForFences,
)
from vulkan import ffi as c_link

from src.consts import BASE_DIR, DEBUG

from .commands import (
    CommandBufferManager,
    RenderPassManager,
    make_command_buffer,
    make_command_pool,
)
from .consts import FRAG_SHADER_PATH, RENDER_FENCE_TIMEOUT, VERT_SHADER_PATH
from .descriptors import (
    allocate_descriptor_set,
    make_descriptor_pool,
    make_descriptor_set_layout,
)
from .device import chose_physical_device, make_logical_device
from .frame_buffer import make_frame_buffers
from .graphics_pipeline import make_graphics_pipeline
from .hinting import (
    VkCommandBuffer,
    VkCommandPool,
    VkDebugReportCallbackEXT,
    VkDescriptorPool,
    VkDescriptorSet,
    VkDescriptorSetLayout,
    VkDevice,
    VkFrameBuffer,
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
from .image import Texture
from .instance import destroy_surface, make_instance, make_surface
from .mesh import Mesh, PentagonMesh, SquareMesh, TriangleMesh
from .queue_families import QueueFamilyIndices, get_queues
from .scene import Scene
from .swapchain import SwapChainFrame, destroy_swapchain, make_swapchain
from .sync import make_fence, make_semaphore
from .validation_layers import destroy_debug_messenger, make_debug_messenger


class Engine:
    """
    Handle a glfw window with vulkan
    """

    # Init
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

        # Descriptor sets
        self.__frame_descriptor_set_layout: VkDescriptorSetLayout = None
        self.__material_descriptor_set_layout: VkDescriptorSetLayout = None
        self.__make_descriptor_set_layouts()

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

        # Frame resources
        self.__descriptor_pool: VkDescriptorPool = None
        self.__make_frame_resources()

        # Assets
        self.__triangle_mesh: TriangleMesh = None
        self.__square_mesh: SquareMesh = None
        self.__pentagon_mesh: PentagonMesh = None
        self.__material_descriptor_pool: VkDescriptorPool = None
        self.__make_assets()

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

    def __make_descriptor_set_layouts(self):

        # frame
        types = [
            VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
            VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
        ]

        stage_flags = [
            VK_SHADER_STAGE_VERTEX_BIT,
            VK_SHADER_STAGE_VERTEX_BIT,
        ]

        count = len(types)

        self.__frame_descriptor_set_layout = make_descriptor_set_layout(
            device      = self.__device,
            count       = count,
            indices     = list(range(count)),
            types       = types,
            counts      = [1] * count,
            stage_flags = stage_flags
        )

        # Material
        types = [
            VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
        ]

        stage_flags = [
            VK_SHADER_STAGE_FRAGMENT_BIT
        ]

        count = len(types)

        self.__material_descriptor_set_layout = make_descriptor_set_layout(
            device      = self.__device,
            count       = count,
            indices     = list(range(count)),
            types       = types,
            counts      = [1] * count,
            stage_flags = stage_flags
        )

    def __make_graphics_pipeline(self):
        self.__pipeline_layout, self.__render_pass, self.__graphics_pipeline = \
        make_graphics_pipeline(
            device                 = self.__device,
            swapchain_extent       = self.__swapchain_extent,
            swapchain_format       = self.__swapchain_format,
            descriptor_set_layouts = [
                                        self.__frame_descriptor_set_layout,
                                        self.__material_descriptor_set_layout,
                                    ],
            vertex_filepath        = BASE_DIR / VERT_SHADER_PATH,
            fragment_filepath      = BASE_DIR / FRAG_SHADER_PATH
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

        for frame in self.__swapchain_frames:
            frame.command_buffer = make_command_buffer(
                self.__device,
                self.__command_pool
            )

        self.__command_buffer = make_command_buffer(
            self.__device,
            self.__command_pool
        )

    def __make_frame_resources(self):

        self.__descriptor_pool = make_descriptor_pool(
            device = self.__device,
            size = len(self.__swapchain_frames),
            types = [
                VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
                VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
            ]
        )

        for frame in self.__swapchain_frames:
            frame.in_flight_fence = make_fence(self.__device)
            frame.image_available_semaphore = make_semaphore(self.__device)
            frame.render_finished_semaphore = make_semaphore(self.__device)

            frame.make_descriptor_resources(
                device          = self.__device,
                physical_device = self.__physical_device
            )

            frame.descriptor_set = allocate_descriptor_set(
                device = self.__device,
                descriptor_pool = self.__descriptor_pool,
                descriptor_set_layout = self.__frame_descriptor_set_layout
            )

    def __make_assets(self):
        self.__triangle_mesh = TriangleMesh(
            device          = self.__device,
            physical_device = self.__physical_device,
            command_buffer  = self.__command_buffer,
            queue           = self.__graphics_queue
        )

        self.__square_mesh = SquareMesh(
            device          = self.__device,
            physical_device = self.__physical_device,
            command_buffer  = self.__command_buffer,
            queue           = self.__graphics_queue
        )

        self.__pentagon_mesh = PentagonMesh(
            device          = self.__device,
            physical_device = self.__physical_device,
            command_buffer  = self.__command_buffer,
            queue           = self.__graphics_queue
        )

        meshs = [
            self.__triangle_mesh,
            self.__square_mesh,
            self.__pentagon_mesh
        ]

        self.__material_descriptor_pool = make_descriptor_pool(
            device = self.__device,
            size   = len(meshs),
            types  = [VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER]
        )

        self.__triangle_mesh.material = Texture(
            device                = self.__device,
            physical_device       = self.__physical_device,
            command_buffer        = self.__command_buffer,
            queue                 = self.__graphics_queue,
            descriptor_set_layout = self.__material_descriptor_set_layout,
            descriptor_pool       = self.__material_descriptor_pool,
            filename              = BASE_DIR / "assets" / "textures" / "face.jpg"
        )

        self.__square_mesh.material = Texture(
            device                = self.__device,
            physical_device       = self.__physical_device,
            command_buffer        = self.__command_buffer,
            queue                 = self.__graphics_queue,
            descriptor_set_layout = self.__material_descriptor_set_layout,
            descriptor_pool       = self.__material_descriptor_pool,
            filename              = BASE_DIR / "assets" / "textures" / "haus.jpg"
        )

        self.__pentagon_mesh.material = Texture(
            device                = self.__device,
            physical_device       = self.__physical_device,
            command_buffer        = self.__command_buffer,
            queue                 = self.__graphics_queue,
            descriptor_set_layout = self.__material_descriptor_set_layout,
            descriptor_pool       = self.__material_descriptor_pool,
            filename              = BASE_DIR / "assets" / "textures" / "noroi.png"
        )

    # Render
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

        try:
            frame_index = vkAcquireNextImageKHR(
                device    = self.__device,
                swapchain = self.__swapchain,
                timeout   = RENDER_FENCE_TIMEOUT,
                semaphore = image_available_semaphore,
                fence     = VK_NULL_HANDLE
            )
        except VkErrorOutOfDateKhr:
            self.__recreate_swapchain()

        frame = self.__swapchain_frames[frame_index]

        command_buffer = frame.command_buffer
        vkResetCommandBuffer(command_buffer, 0)

        self.__prepare_frame(frame_index, scene)
        self.__record_draw_command(
            frame_buffer   = frame.frame_buffer,
            command_buffer = command_buffer,
            descriptor_set = frame.descriptor_set,
            scene          = scene
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

        try:
            vkQueuePresentKHR(self.__present_queue, present_info)
        except VkErrorOutOfDateKhr:
            self.__recreate_swapchain()

        self.__current_frame_number += 1
        self.__current_frame_number %= self.__max_frames_in_flight

    def __record_draw_command(
        self,
        command_buffer: VkCommandBuffer,
        frame_buffer: VkFrameBuffer,
        descriptor_set: VkDescriptorSet,
        scene: Scene
    ):
        with CommandBufferManager(command_buffer):

            vkCmdBindDescriptorSets(
                commandBuffer      = command_buffer,
                pipelineBindPoint  = VK_PIPELINE_BIND_POINT_GRAPHICS,
                layout             = self.__pipeline_layout,
                firstSet           = 0,
                descriptorSetCount = 1,
                pDescriptorSets    = [descriptor_set],
                dynamicOffsetCount = 0,
                pDynamicOffsets    = [0],
            )

            clear_color = VkClearValue([[1.0, 0.5, 0.25, 1.0]])
            render_pass_begin_info = VkRenderPassBeginInfo(
                renderPass = self.__render_pass,
                framebuffer = frame_buffer,
                renderArea = [[0, 0], self.__swapchain_extent],
                clearValueCount = 1,
                pClearValues = c_link.addressof(clear_color)
            )

            with RenderPassManager(
                command_buffer,
                render_pass_begin_info,
                VK_SUBPASS_CONTENTS_INLINE
            ):
                vkCmdBindPipeline(
                    command_buffer,
                    VK_PIPELINE_BIND_POINT_GRAPHICS,
                    self.__graphics_pipeline
                )

                # self.__prepare_scene(command_buffer, scene)

                # Triangles
                first_instance = 0
                instance_count = len(scene.triangle_positions)
                first_instance = self.__render_mesh(
                    mesh           = self.__triangle_mesh,
                    command_buffer = command_buffer,
                    first_instance = first_instance,
                    instance_count = instance_count
                )

                # Squares
                instance_count = len(scene.square_positions)
                first_instance = self.__render_mesh(
                    mesh           = self.__square_mesh,
                    command_buffer = command_buffer,
                    first_instance = first_instance,
                    instance_count = instance_count
                )

                # Pentagons
                instance_count = len(scene.pentagon_positions)
                first_instance = self.__render_mesh(
                    mesh           = self.__pentagon_mesh,
                    command_buffer = command_buffer,
                    first_instance = first_instance,
                    instance_count = instance_count
                )

    def __render_mesh(
        self,
        mesh: Mesh,
        command_buffer: VkCommandBuffer,
        first_instance: int,
        instance_count: int
    ) -> int:
        mesh.material.use(
            command_buffer  = command_buffer,
            pipeline_layout = self.__pipeline_layout
        )

        vkCmdBindVertexBuffers(
            commandBuffer = command_buffer,
            firstBinding = 0,
            bindingCount = 1,
            pBuffers     = [mesh.vertex_buffer],
            pOffsets     = [0]
        )

        vkCmdDraw(
            commandBuffer = command_buffer,
            vertexCount   = len(mesh.points),
            instanceCount = instance_count,
            firstVertex   = 0,
            firstInstance = first_instance
        )

        return first_instance + instance_count

    def __prepare_frame(self, frame_index: int, scene: Scene):
        frame = self.__swapchain_frames[frame_index]

        position = array([1, 0, -1], dtype=float32)
        target = array([0, 0, 0], dtype=float32)
        up = array([0, 0, -1], dtype=float32)

        frame.camera_data.view = matrix44.create_look_at(
            position, target, up, dtype=float32)

        fov = 45
        aspect = self.__swapchain_extent.width / self.__swapchain_extent.height
        near = 0.1
        far = 10
        frame.camera_data.projection = matrix44.create_perspective_projection(
            fov, aspect, near, far, dtype=float32
        )

        frame.camera_data.projection[1][1] *= -1 # OpenGL -> Vulkan

        frame.camera_data.view_projection = matrix44.multiply(
            frame.camera_data.view,
            frame.camera_data.projection
        )

        flattended_data = (
              frame.camera_data.view.astype("f").tobytes()
            + frame.camera_data.projection.astype("f").tobytes()
            + frame.camera_data.view_projection.astype("f").tobytes()
        )

        size = 3 * (4 * 4) * 4 # nb of * mat4 * float32

        c_link.memmove(
            src = flattended_data,
            dest = frame.uniform_buffer_write_location,
            n = size
        )

        # Triangles
        i = 0
        for pos in scene.triangle_positions:
            frame.model_transforms[i] = matrix44.create_from_translation(
                vec   = pos,
                dtype = float32
            )

            i += 1

        # Squares
        for pos in scene.square_positions:
            frame.model_transforms[i] = matrix44.create_from_translation(
                vec   = pos,
                dtype = float32
            )

            i += 1

        # Pentagons
        for pos in scene.pentagon_positions:
            frame.model_transforms[i] = matrix44.create_from_translation(
                vec   = pos,
                dtype = float32
            )

            i += 1

        flattended_data = frame.model_transforms.astype("f").tobytes()

        size = i * (4 * 4) * 4 # nb of * mat4 * float32

        c_link.memmove(
            src = flattended_data,
            dest = frame.model_buffer_write_location,
            n = size
        )

        frame.write_descriptor_set(self.__device)

    def __prepare_scene(self, command_buffer: VkCommandBuffer, scene: Scene):
        pass

    def __recreate_swapchain(self):

        # Don't recreate the swapchain if the window is mimnimized
        self.width = 0
        self.height = 0
        while (self.width == 0 or self.height == 0):
            self.width, self.height = get_window_size(self.window)
            wait_events()

        logging.debug("Waiting for device to recreate the swapchain")
        vkDeviceWaitIdle(self.__device)

        logging.debug("Recreating the swapchain")

        self.__cleanup_swapchain()

        self.__make_swapchain()
        self.__make_frame_buffers()

        for frame in self.__swapchain_frames:
            frame.command_buffer = make_command_buffer(
                self.__device,
                self.__command_pool
            )

        self.__make_frame_resources()

    # Cleanup
    def cleanup(self):
        """
        Close the GLFW window and clean Vulkan objects
        """

        logging.info("Waiting for device to cleanup")
        vkDeviceWaitIdle(self.__device)

        logging.debug("Destroying objects")

        # Commands
        vkDestroyCommandPool(self.__device, self.__command_pool, None)

        # Assets
        vkDestroyDescriptorPool(self.__device, self.__material_descriptor_pool, None)

        self.__triangle_mesh.material.destroy()
        self.__square_mesh.material.destroy()
        self.__pentagon_mesh.material.destroy()

        # Graphics pipeline
        vkDestroyPipeline(self.__device, self.__graphics_pipeline, None)
        vkDestroyRenderPass(self.__device, self.__render_pass, None)
        vkDestroyPipelineLayout(self.__device, self.__pipeline_layout, None)

        # Descriptor Sets
        vkDestroyDescriptorSetLayout(
            self.__device, self.__frame_descriptor_set_layout, None)
        vkDestroyDescriptorSetLayout(
            self.__device, self.__material_descriptor_set_layout, None)

        # Swapchain
        self.__cleanup_swapchain()

        # Assets
        self.__triangle_mesh.destroy()
        self.__square_mesh.destroy()
        self.__pentagon_mesh.destroy()

        # Device
        vkDestroyDevice(self.__device, None)

        # Instance
        destroy_surface(self.__instance, self.__surface)
        if DEBUG:
            destroy_debug_messenger(self.__instance, self.__debug_messenger)
        vkDestroyInstance(self.__instance, None)

        # Window
        glfw_terminate()

        logging.info("Cleanup done !")

    def __cleanup_swapchain(self):
        for frame in self.__swapchain_frames:
            vkDestroyImageView(self.__device, frame.image_view, None)
            vkDestroyFramebuffer(self.__device, frame.frame_buffer, None)

            vkUnmapMemory(self.__device, frame.model_buffer_memory)
            vkFreeMemory(self.__device, frame.model_buffer_memory, None)
            vkDestroyBuffer(self.__device, frame.model_buffer, None)

            vkUnmapMemory(self.__device, frame.uniform_buffer_memory)
            vkFreeMemory(self.__device, frame.uniform_buffer_memory, None)
            vkDestroyBuffer(self.__device, frame.uniform_buffer, None)

            vkDestroySemaphore(self.__device, frame.render_finished_semaphore, None)
            vkDestroySemaphore(self.__device, frame.image_available_semaphore, None)
            vkDestroyFence(self.__device, frame.in_flight_fence, None)

        vkDestroyDescriptorPool(self.__device, self.__descriptor_pool, None)

        destroy_swapchain(self.__device, self.__swapchain)
