"""Orthographic follow camera for the top-down combat view."""

from math import copysign

import glm


class Camera:
    def __init__(self, screen_width, screen_height):
        self.position = glm.vec3(0.0, 14.0, 14.0)
        self.target = glm.vec3(0.0, 0.0, 0.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.zoom = 19.0
        self.deadzone = 2.0
        self.smooth_speed = 5.0
        self.update_projection(screen_width, screen_height)

    def get_view_matrix(self):
        return glm.lookAt(self.position, self.target, self.up)

    def update_projection(self, width, height):
        aspect = max(1, width) / max(1, height)
        self.projection_matrix = glm.ortho(
            -self.zoom * aspect, self.zoom * aspect,
            -self.zoom, self.zoom, 0.1, 500.0)

    def get_projection_matrix(self):
        return self.projection_matrix

    def follow_target(self, player_x, player_z, delta_time):
        dx, dz = player_x - self.target.x, player_z - self.target.z
        ideal_x, ideal_z = self.target.x, self.target.z
        if abs(dx) > self.deadzone:
            ideal_x = player_x - copysign(self.deadzone, dx)
        if abs(dz) > self.deadzone:
            ideal_z = player_z - copysign(self.deadzone, dz)

        factor = min(1.0, self.smooth_speed * delta_time)
        self.target.x += (ideal_x - self.target.x) * factor
        self.target.z += (ideal_z - self.target.z) * factor
        self.position.x = self.target.x
        self.position.y = 14.0
        self.position.z = self.target.z + 14.0
