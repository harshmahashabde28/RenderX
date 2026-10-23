#version 330 core

in vec3 WorldPos;
in vec2 TexCoord;
in vec3 Normal;

out vec4 FragColor;

uniform sampler2D texture1;
uniform bool useTexture;
uniform vec3 objectColor;
uniform bool isFloor;
uniform bool isShadow;

uniform vec3 lightDir;
uniform vec3 lightColor;
uniform vec3 viewPos;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.7, 7.8))) * 437.5);
}

void main() {
    // If it's a shadow pass, draw transparent black and skip lighting
    if (isShadow) {
        FragColor = vec4(0.0, 0.0, 0.0, 0.5); 
        return;
    }

    vec4 baseColor;
    if (isFloor) {
        float gridSize = 10.0; 
        vec2 coord = WorldPos.xz / gridSize;
        vec2 gridPos = abs(fract(coord - 0.5) - 0.5) / fwidth(coord);
        float line = min(gridPos.x, gridPos.y);
        
        // 1. THICKNESS CONTROL: Higher number = thicker lines
        float thickness = 2.0; 
        float lineMask = 1.0 - min(line / thickness, 1.0);
        
        // 2. DISTANCE FADE: Smoothly fade the grid far away to stop flickering!
        float dist = length(viewPos - WorldPos);
        float fade = 1.0 - smoothstep(60.0, 140.0, dist);
        
        // Dark, low-contrast arena floor keeps the combat space legible.
        vec3 concrete = vec3(0.035, 0.052, 0.064);
        concrete += hash(WorldPos.xz * 10.0) * 0.03;
        
        // Restrained teal grid marks preserve depth without overpowering models.
        vec3 lineCol = vec3(0.10, 0.23, 0.23);
        
        // Combine it all (multiply lineMask by fade)
        baseColor = vec4(mix(concrete, lineCol, lineMask * 0.58 * fade), 1.0);
    } else if (useTexture) {
        baseColor = texture(texture1, TexCoord) * vec4(objectColor, 1.0);
    } else {
        baseColor = vec4(objectColor, 1.0);
    }

    // Standard Shading
    vec3 norm = normalize(Normal);
    vec3 lDir = normalize(-lightDir);
    float diff = max(dot(norm, lDir), 0.0);
    vec3 lighting = (0.68 + diff * 0.32) * lightColor;
    
    FragColor = vec4(baseColor.rgb * lighting, baseColor.a);
}
