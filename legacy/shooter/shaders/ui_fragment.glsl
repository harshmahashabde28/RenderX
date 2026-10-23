#version 330 core
in vec2 TexCoord;
out vec4 FragColor;

uniform sampler2D uiTexture;

void main() {
    vec4 texColor = texture(uiTexture, TexCoord);
    
    // If the pixel is completely transparent, don't draw it (saves GPU power)
    if(texColor.a < 0.05) {
        discard;
    }
    FragColor = texColor;
}