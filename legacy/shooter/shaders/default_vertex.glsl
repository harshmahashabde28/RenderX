#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;
layout (location = 2) in vec3 aNormal;

out vec3 WorldPos;
out vec2 TexCoord;
out vec3 Normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform bool isShadow;   
uniform vec3 lightDir;   

void main() {
    vec4 worldPosition = model * vec4(aPos, 1.0);
    
    // --- SHADOW PROJECTION MATH ---
    if (isShadow) {
        float h = worldPosition.y; 
        
        // Place shadow slightly above the floor plane (-0.1) to prevent flickering
        worldPosition.y = -0.095; 
        
        // Project shadow stretched along the ground based on sun angle
        worldPosition.x = worldPosition.x - h * (lightDir.x / lightDir.y);
        worldPosition.z = worldPosition.z - h * (lightDir.z / lightDir.y);
    }
    
    WorldPos = worldPosition.xyz;
    TexCoord = aTexCoord;
    
    // Calculate how the normal arrows rotate with the models for accurate lighting
    Normal = mat3(transpose(inverse(model))) * aNormal;
    
    gl_Position = projection * view * worldPosition;
}