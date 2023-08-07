set glslc = E:\VulkanSDK\1.3.224.1\Bin\glslc.exe

set shaderDirectory=src/display/shaders/
set spvDirectory=src/display/shaders/

glslc %shaderDirectory%shader.vert -o %spvDirectory%vert.spv
glslc %shaderDirectory%shader.frag -o %spvDirectory%frag.spv
