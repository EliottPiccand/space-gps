from PIL import Image as PILImage
from vulkan import (
    VK_ACCESS_SHADER_READ_BIT,
    VK_ACCESS_TRANSFER_WRITE_BIT,
    VK_BORDER_COLOR_INT_OPAQUE_BLACK,
    VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
    VK_COMPARE_OP_ALWAYS,
    VK_COMPONENT_SWIZZLE_IDENTITY,
    VK_FALSE,
    VK_FILTER_LINEAR,
    VK_FILTER_NEAREST,
    VK_FORMAT_R8G8B8A8_UNORM,
    VK_IMAGE_ASPECT_COLOR_BIT,
    VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VkWriteDescriptorSet,
    VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
    VK_IMAGE_LAYOUT_UNDEFINED,
    VK_IMAGE_TILING_OPTIMAL,
    VK_IMAGE_TYPE_2D, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
    VK_IMAGE_USAGE_SAMPLED_BIT, VkDescriptorImageInfo,
    VK_IMAGE_USAGE_TRANSFER_DST_BIT,
    VK_IMAGE_VIEW_TYPE_2D, vkUpdateDescriptorSets,
    VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
    VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT,
    VK_PIPELINE_BIND_POINT_GRAPHICS,
    VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
    VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
    VK_PIPELINE_STAGE_TRANSFER_BIT,
    VK_QUEUE_FAMILY_IGNORED,
    VK_SAMPLE_COUNT_1_BIT,
    VK_SAMPLER_ADDRESS_MODE_REPEAT,
    VK_SAMPLER_MIPMAP_MODE_LINEAR,
    VK_SHARING_MODE_EXCLUSIVE,
    VkBufferImageCopy,
    VkComponentMapping,
    VkExtent3D,
    VkImageCreateInfo,
    VkImageMemoryBarrier,
    VkImageSubresourceLayers,
    VkImageSubresourceRange,
    VkImageViewCreateInfo,
    VkOffset3D,
    VkSamplerCreateInfo,
    vkCmdBindDescriptorSets,
    vkCmdCopyBufferToImage,
    vkCmdPipelineBarrier,
    vkCreateImage,
    vkCreateImageView,
    vkCreateSampler,
    vkDestroyBuffer,
    vkDestroyImage,
    vkDestroyImageView,
    vkDestroySampler,
    vkFreeMemory,
    vkMapMemory,
    vkUnmapMemory,
)
from vulkan import ffi as c_link

from .commands import SimpleCommandBufferManager
from .descriptors import allocate_descriptor_set
from .hinting import (
    VkBuffer,
    VkCommandBuffer,
    VkDescriptorPool,
    VkDescriptorSet,
    VkDescriptorSetLayout,
    VkDevice,
    VkFormat,
    VkGraphicsQueue,
    VkImage,
    VkImageLayout,
    VkImageTiling,
    VkImageUsageFlags,
    VkImageView,
    VkPhysicalDevice,
    VkPipelineLayout,
    VkSampler,
)
from .memory import allocate_image_memory, create_buffer


class Texture:

    def __init__(
        self,
        device: VkDevice,
        physical_device: VkPhysicalDevice,
        command_buffer: VkCommandBuffer,
        queue: VkGraphicsQueue,
        descriptor_set_layout: VkDescriptorSetLayout,
        descriptor_pool: VkDescriptorPool,
        filename: str
    ):

        self.__device = device
        self.__physical_device = physical_device
        self.__command_buffer = command_buffer
        self.__queue = queue
        self.__descriptor_set_layout = descriptor_set_layout
        self.__descriptor_pool = descriptor_pool
        self.__filename = filename

        # Load image
        self.__width: int = None
        self.__height: int = None
        self.__raw_image_data: bytes = None
        self.__load()

        self.__image = make_image(
            device = device,
            width  = self.__width,
            height = self.__height,
            tiling = VK_IMAGE_TILING_OPTIMAL,
            usage  = VK_IMAGE_USAGE_SAMPLED_BIT
                   | VK_IMAGE_USAGE_TRANSFER_DST_BIT
        )
        self.__image_memory = allocate_image_memory(
            device            = device,
            physical_device   = physical_device,
            image             = self.__image,
            memory_properties = VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT
        )

        self.__populate()

        self.__image_view: VkImageView = None
        self.__make_view()

        self.__sampler: VkSampler = None
        self.__make_sampler()

        self.__descriptor_set: VkDescriptorSet = None
        self.__make_descriptor_set()

    def __load(self):
        with PILImage.open(self.__filename) as raw_image:
            self.__width, self.__height = raw_image.size
            raw_img = raw_image.convert("RGBA")
            self.__raw_image_data = raw_img.tobytes()

    def __populate(self):
        size = self.__width * self.__height * 4 # float32

        staging_buffer, staging_buffer_memory = create_buffer(
            device               = self.__device,
            physical_device      = self.__physical_device,
            size                 = size,
            usage                = VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
            requested_properties = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT
                                 | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
        )

        write_location = vkMapMemory(
            device = self.__device,
            memory = staging_buffer_memory,
            offset = 0,
            size   = size,
            flags  = 0
        )

        c_link.memmove(
            dest = write_location,
            src  = self.__raw_image_data,
            n    = size
        )

        vkUnmapMemory(self.__device, staging_buffer_memory)
        del self.__raw_image_data

        transition_image_layout(
            command_buffer = self.__command_buffer,
            queue          = self.__queue,
            old_layout     = VK_IMAGE_LAYOUT_UNDEFINED,
            new_layout     = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            image          = self.__image
        )

        copy_buffer_to_image(
            command_buffer = self.__command_buffer,
            queue          = self.__queue,
            buffer         = staging_buffer,
            image          = self.__image,
            width          = self.__width,
            height         = self.__height
        )

        transition_image_layout(
            command_buffer = self.__command_buffer,
            queue          = self.__queue,
            old_layout     = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            new_layout     = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
            image          = self.__image
        )

        vkDestroyBuffer(self.__device, staging_buffer, None)
        vkFreeMemory(self.__device, staging_buffer_memory, None)

    def __make_view(self):
        self.__image_view = make_image_view(
            device = self.__device,
            image  = self.__image,
            fmt    = VK_FORMAT_R8G8B8A8_UNORM
        )

    def __make_sampler(self):
        create_info = VkSamplerCreateInfo(
            magFilter = VK_FILTER_LINEAR,
            minFilter = VK_FILTER_NEAREST,
            addressModeU = VK_SAMPLER_ADDRESS_MODE_REPEAT,
            addressModeV = VK_SAMPLER_ADDRESS_MODE_REPEAT,
            addressModeW = VK_SAMPLER_ADDRESS_MODE_REPEAT,
            anisotropyEnable = VK_FALSE,
            maxAnisotropy = 1.0,
            borderColor = VK_BORDER_COLOR_INT_OPAQUE_BLACK,
            unnormalizedCoordinates = VK_FALSE,
            compareEnable = VK_FALSE,
            compareOp = VK_COMPARE_OP_ALWAYS,
            mipmapMode = VK_SAMPLER_MIPMAP_MODE_LINEAR,
            mipLodBias = 0,
            minLod = 0,
            maxLod = 0
        )

        self.__sampler = vkCreateSampler(self.__device, create_info, None)

    def __make_descriptor_set(self):
        self.__descriptor_set = allocate_descriptor_set(
            device                = self.__device,
            descriptor_pool       = self.__descriptor_pool,
            descriptor_set_layout = self.__descriptor_set_layout
        )

        descriptor = VkDescriptorImageInfo(
            sampler     = self.__sampler,
            imageView   = self.__image_view,
            imageLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL
        )

        descriptor_write = VkWriteDescriptorSet(
            dstSet          = self.__descriptor_set,
            dstBinding      = 0,
            dstArrayElement = 0,
            descriptorType  = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,
            descriptorCount = 1,
            pImageInfo      = descriptor
        )

        vkUpdateDescriptorSets(
            device               = self.__device,
            descriptorWriteCount = 1,
            pDescriptorWrites    = descriptor_write,
            descriptorCopyCount  = 0,
            pDescriptorCopies    = None
        )

    def use(self, command_buffer: VkCommandBuffer, pipeline_layout: VkPipelineLayout):
        vkCmdBindDescriptorSets(
            commandBuffer      = command_buffer,
            pipelineBindPoint  = VK_PIPELINE_BIND_POINT_GRAPHICS,
            layout             = pipeline_layout,
            firstSet           = 1,
            descriptorSetCount = 1,
            pDescriptorSets    = [self.__descriptor_set],
            dynamicOffsetCount = 0,
            pDynamicOffsets    = [0],
        )

    def destroy(self):
        vkFreeMemory(self.__device, self.__image_memory, None)
        vkDestroyImage(self.__device, self.__image, None)
        vkDestroyImageView(self.__device, self.__image_view, None)
        vkDestroySampler(self.__device, self.__sampler, None)

def make_image(
    device: VkDevice,
    width: int,
    height: int,
    tiling: VkImageTiling,
    usage: VkImageUsageFlags
) -> VkImage:
    create_info = VkImageCreateInfo(
        imageType     = VK_IMAGE_TYPE_2D,
        extent        = VkExtent3D(width, height, 1),
        mipLevels     = 1,
        arrayLayers   = 1,
        format        = VK_FORMAT_R8G8B8A8_UNORM,
        tiling        = tiling,
        initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
        usage         = usage,
        sharingMode   = VK_SHARING_MODE_EXCLUSIVE,
        samples       = VK_SAMPLE_COUNT_1_BIT
    )

    return vkCreateImage(device, create_info, None)

def transition_image_layout(
    command_buffer: VkCommandBuffer,
    queue: VkGraphicsQueue,
    old_layout: VkImageLayout,
    new_layout: VkImageLayout,
    image: VkImage
):
    with SimpleCommandBufferManager(
        command_buffer = command_buffer,
        queue          = queue
    ):
        subresource_range = VkImageSubresourceRange(
            aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
            baseMipLevel   = 1,
            levelCount     = 1,
            baseArrayLayer = 0,
            layerCount     = 1
        )

        if old_layout == VK_IMAGE_LAYOUT_UNDEFINED:
            src_stage_mask = VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT
            src_access_mask = 0

            dst_stage_mask = VK_PIPELINE_STAGE_TRANSFER_BIT
            dst_access_mask = VK_ACCESS_TRANSFER_WRITE_BIT
        else:
            src_stage_mask = VK_PIPELINE_STAGE_TRANSFER_BIT
            src_access_mask = VK_ACCESS_TRANSFER_WRITE_BIT

            dst_stage_mask = VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT
            dst_access_mask = VK_ACCESS_SHADER_READ_BIT

        image_memory_barrier = VkImageMemoryBarrier(
            srcAccessMask       = src_access_mask,
            dstAccessMask       = dst_access_mask,
            oldLayout           = old_layout,
            newLayout           = new_layout,
            srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
            image               = image,
            subresourceRange    = subresource_range
        )

        vkCmdPipelineBarrier(
            commandBuffer            = command_buffer,
            srcStageMask             = src_stage_mask,
            dstStageMask             = dst_stage_mask,
            dependencyFlags          = 0,
            memoryBarrierCount       = 0,
            pMemoryBarriers          = None,
            bufferMemoryBarrierCount = 0,
            pBufferMemoryBarriers    = None,
            imageMemoryBarrierCount  = 1,
            pImageMemoryBarriers     = image_memory_barrier
        )

def copy_buffer_to_image(
    command_buffer: VkCommandBuffer,
    queue: VkGraphicsQueue,
    buffer: VkBuffer,
    image: VkImage,
    width: int,
    height: int
):
    with SimpleCommandBufferManager(
        command_buffer = command_buffer,
        queue          = queue
    ):
        subresource = VkImageSubresourceLayers(
            aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
            mipLevel       = 0,
            baseArrayLayer = 0,
            layerCount     = 1
        )

        extent = VkExtent3D(width, height, 1)
        offset = VkOffset3D(0, 0, 0)

        region = VkBufferImageCopy(
            bufferOffset      = 0,
            bufferRowLength   = 0,
            bufferImageHeight = 0,
            imageSubresource  = subresource,
            imageOffset       = offset,
            imageExtent       = extent
        )

        vkCmdCopyBufferToImage(
            commandBuffer = command_buffer,
            srcBuffer = buffer,
            dstImage = image,
            dstImageLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            regionCount = 1,
            pRegions = [region]
        )

def make_image_view(device: VkDevice, image: VkImage, fmt: VkFormat) -> VkImageView:
    components = VkComponentMapping(
        r = VK_COMPONENT_SWIZZLE_IDENTITY,
        g = VK_COMPONENT_SWIZZLE_IDENTITY,
        b = VK_COMPONENT_SWIZZLE_IDENTITY,
        a = VK_COMPONENT_SWIZZLE_IDENTITY
    )

    subresource_range = VkImageSubresourceRange(
        aspectMask     = VK_IMAGE_ASPECT_COLOR_BIT,
        baseMipLevel   = 0,
        levelCount     = 1,
        baseArrayLayer = 0,
        layerCount     = 1
    )

    create_info = VkImageViewCreateInfo(
        image            = image,
        viewType         = VK_IMAGE_VIEW_TYPE_2D,
        format           = fmt,
        components       = components,
        subresourceRange = subresource_range
    )

    return vkCreateImageView(device, create_info, None)
