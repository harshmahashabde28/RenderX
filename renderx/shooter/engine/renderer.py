"""OpenGL scene renderer for the shooter world and its textured models."""

import ctypes
from pathlib import Path

import glm
import numpy as np
import OpenGL.GL as gl
import OpenGL.GL.shaders
import pygame


class Renderer:
    def __init__(self, shader_dir):
        self.shader_dir = Path(shader_dir)
        self.shader_program = self._compile_shaders()
        self.vao, self.vbo, self.vertex_count = self._setup_floor()
        self.textures = []
        self.model_loc = gl.glGetUniformLocation(self.shader_program, "model")
        self.view_loc = gl.glGetUniformLocation(self.shader_program, "view")
        self.proj_loc = gl.glGetUniformLocation(self.shader_program, "projection")
        self.color_loc = gl.glGetUniformLocation(self.shader_program, "objectColor")
        self.is_floor_loc = gl.glGetUniformLocation(self.shader_program, "isFloor")
        self.use_tex_loc = gl.glGetUniformLocation(self.shader_program, "useTexture")
        self.light_dir_loc = gl.glGetUniformLocation(self.shader_program, "lightDir")
        self.light_color_loc = gl.glGetUniformLocation(self.shader_program, "lightColor")
        self.view_pos_loc = gl.glGetUniformLocation(self.shader_program, "viewPos")
        self.is_shadow_loc = gl.glGetUniformLocation(self.shader_program, "isShadow")
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def load_texture(self, filepath):
        surface = pygame.image.load(filepath).convert_alpha()
        data = pygame.image.tobytes(surface, "RGBA", True)
        texture = gl.glGenTextures(1)
        self.textures.append(texture)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                        surface.get_width(), surface.get_height(), 0,
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_LINEAR_MIPMAP_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)
        return texture

    def _compile_shaders(self):
        vertex_path = self.shader_dir / "default_vertex.glsl"
        fragment_path = self.shader_dir / "default_fragment.glsl"
        vertex = vertex_path.read_text(encoding="utf-8")
        fragment = fragment_path.read_text(encoding="utf-8")
        return OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(vertex, gl.GL_VERTEX_SHADER),
            OpenGL.GL.shaders.compileShader(fragment, gl.GL_FRAGMENT_SHADER))

    def _setup_floor(self):
        vertices = np.array([
            -0.5, 0.0, -0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
             0.5, 0.0, -0.5, 1.0, 0.0, 0.0, 1.0, 0.0,
             0.5, 0.0,  0.5, 1.0, 1.0, 0.0, 1.0, 0.0,
             0.5, 0.0,  0.5, 1.0, 1.0, 0.0, 1.0, 0.0,
            -0.5, 0.0,  0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
            -0.5, 0.0, -0.5, 0.0, 0.0, 0.0, 1.0, 0.0,
        ], dtype=np.float32)
        vao = gl.glGenVertexArrays(1)
        vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices,
                        gl.GL_STATIC_DRAW)
        stride = 8 * vertices.itemsize
        for location, size, offset in ((0, 3, 0), (1, 2, 12), (2, 3, 20)):
            gl.glVertexAttribPointer(location, size, gl.GL_FLOAT, gl.GL_FALSE,
                                     stride, ctypes.c_void_p(offset))
            gl.glEnableVertexAttribArray(location)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
        return vao, vbo, len(vertices) // 8

    def render(self, camera, model_matrix, color=(1.0, 1.0, 1.0),
               is_floor=False, custom_mesh=None, texture_id=None,
               is_shadow=False):
        gl.glUseProgram(self.shader_program)
        view = np.asarray(camera.get_view_matrix(), dtype=np.float32)
        projection = np.asarray(camera.get_projection_matrix(), dtype=np.float32)
        model = np.asarray(model_matrix, dtype=np.float32)
        gl.glUniformMatrix4fv(self.view_loc, 1, gl.GL_TRUE, view)
        gl.glUniformMatrix4fv(self.proj_loc, 1, gl.GL_TRUE, projection)
        gl.glUniformMatrix4fv(self.model_loc, 1, gl.GL_TRUE, model)
        gl.glUniform3f(self.color_loc, *color)
        gl.glUniform1i(self.is_floor_loc, int(is_floor))
        gl.glUniform1i(self.is_shadow_loc, int(is_shadow))
        gl.glUniform3f(self.light_dir_loc, -0.5, -1.0, -0.5)
        gl.glUniform3f(self.light_color_loc, 1.0, 1.0, 1.0)
        camera_position = glm.inverse(camera.get_view_matrix())[3]
        gl.glUniform3f(self.view_pos_loc, camera_position.x,
                       camera_position.y, camera_position.z)

        use_texture = custom_mesh is not None and texture_id is not None and not is_shadow
        gl.glUniform1i(self.use_tex_loc, int(use_texture))
        if use_texture:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)

        vao = custom_mesh.vao if custom_mesh is not None else self.vao
        count = custom_mesh.vertex_count if custom_mesh is not None else self.vertex_count
        gl.glBindVertexArray(vao)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, count)
        gl.glBindVertexArray(0)

    def close(self):
        for texture in self.textures:
            gl.glDeleteTextures([texture])
        gl.glDeleteBuffers(1, [self.vbo])
        gl.glDeleteVertexArrays(1, [self.vao])
        gl.glDeleteProgram(self.shader_program)
