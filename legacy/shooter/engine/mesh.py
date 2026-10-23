"""Upload a triangulated glTF mesh with position, UV, and normal attributes."""

import ctypes
from pathlib import Path

import numpy as np
import OpenGL.GL as gl
import trimesh


class Mesh:
    def __init__(self, filepath):
        source = trimesh.load(Path(filepath), force="mesh")
        vertices = np.asarray(source.vertices, dtype=np.float32)
        faces = np.asarray(source.faces, dtype=np.int64)
        triangle_vertices = vertices[faces].reshape(-1, 3)

        uv = getattr(source.visual, "uv", None)
        if uv is None or len(uv) == 0:
            triangle_uvs = np.zeros((len(triangle_vertices), 2), dtype=np.float32)
        else:
            triangle_uvs = np.asarray(uv, dtype=np.float32)[faces].reshape(-1, 2)

        face_normals = np.asarray(source.face_normals, dtype=np.float32)
        vertex_normals = np.zeros_like(vertices)
        np.add.at(vertex_normals, faces.reshape(-1),
                  np.repeat(face_normals, 3, axis=0))
        lengths = np.linalg.norm(vertex_normals, axis=1)
        valid = lengths > 1e-8
        vertex_normals[valid] /= lengths[valid, None]
        vertex_normals[~valid, 1] = 1.0
        triangle_normals = vertex_normals[faces].reshape(-1, 3)

        vertex_data = np.column_stack((triangle_vertices, triangle_uvs,
                                       triangle_normals)).astype(np.float32)
        self.vertex_count = len(vertex_data)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertex_data.nbytes,
                        vertex_data, gl.GL_STATIC_DRAW)
        stride = 8 * vertex_data.itemsize
        for location, size, offset in ((0, 3, 0), (1, 2, 12), (2, 3, 20)):
            gl.glVertexAttribPointer(location, size, gl.GL_FLOAT, gl.GL_FALSE,
                                     stride, ctypes.c_void_p(offset))
            gl.glEnableVertexAttribArray(location)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

    def close(self):
        gl.glDeleteBuffers(1, [self.vbo])
        gl.glDeleteVertexArrays(1, [self.vao])
