"""Player movement, dash, aim, and model transform."""

import math

import glm
import pygame

from renderx.input_map import SHOOTER_KEYS

from ..logic import aabb_overlap


class Player:
    def __init__(self, start_x=0.0, start_z=0.0):
        self.x, self.z = float(start_x), float(start_z)
        self.width = self.depth = 2.0
        self.speed = 8.5
        self.rotation_y = 0.0
        self.fire_rate = 0.17
        self.fire_timer = 0.0
        self.dash_cooldown = 0.0
        self.dash_duration = 0.0
        self.dash_vector = (0.0, 0.0)
        self.invulnerable = 0.0

    def aim_at(self, x, z):
        self.rotation_y = math.atan2(x - self.x, z - self.z)

    def move(self, keys, delta_time, obstacles, arena_size):
        x_dir = float(any(keys[key] for key in SHOOTER_KEYS["move_right"])) - float(
            any(keys[key] for key in SHOOTER_KEYS["move_left"]))
        z_dir = float(any(keys[key] for key in SHOOTER_KEYS["move_backward"])) - float(
            any(keys[key] for key in SHOOTER_KEYS["move_forward"]))
        length = math.hypot(x_dir, z_dir)
        if length:
            x_dir, z_dir = x_dir / length, z_dir / length

        if self.dash_duration > 0:
            x_dir, z_dir = self.dash_vector
            self.dash_duration = max(0.0, self.dash_duration - delta_time)
            speed = self.speed * 4.0
        else:
            speed = self.speed

        dx, dz = x_dir * speed * delta_time, z_dir * speed * delta_time
        nx = max(-arena_size, min(arena_size, self.x + dx))
        if not self._blocked(nx, self.z, obstacles):
            self.x = nx
        nz = max(-arena_size, min(arena_size, self.z + dz))
        if not self._blocked(self.x, nz, obstacles):
            self.z = nz
        self.fire_timer += delta_time
        self.dash_cooldown = max(0.0, self.dash_cooldown - delta_time)
        self.invulnerable = max(0.0, self.invulnerable - delta_time)

    def dash(self, keys, aim_x=None, aim_z=None):
        if self.dash_cooldown > 0:
            return False
        x_dir = float(any(keys[key] for key in SHOOTER_KEYS["move_right"])) - float(
            any(keys[key] for key in SHOOTER_KEYS["move_left"]))
        z_dir = float(any(keys[key] for key in SHOOTER_KEYS["move_backward"])) - float(
            any(keys[key] for key in SHOOTER_KEYS["move_forward"]))
        length = math.hypot(x_dir, z_dir)
        if length:
            x_dir, z_dir = x_dir / length, z_dir / length
        elif aim_x is not None and aim_z is not None:
            dx, dz = self.x - aim_x, self.z - aim_z
            length = math.hypot(dx, dz) or 1.0
            x_dir, z_dir = dx / length, dz / length
        else:
            x_dir, z_dir = -math.sin(self.rotation_y), -math.cos(self.rotation_y)
        self.dash_vector = x_dir, z_dir
        self.dash_duration = 0.16
        self.dash_cooldown = 2.4
        self.invulnerable = 0.2
        return True

    def can_shoot(self):
        if self.fire_timer < self.fire_rate:
            return False
        self.fire_timer = 0.0
        return True

    @staticmethod
    def _blocked(x, z, obstacles):
        return any(aabb_overlap(x, z, 1.7, 1.7, box.x, box.z,
                                box.width, box.depth) for box in obstacles)

    def get_model_matrix(self):
        model = glm.translate(glm.mat4(1.0), glm.vec3(self.x, 0.5, self.z))
        model = glm.rotate(model, self.rotation_y, glm.vec3(0.0, 1.0, 0.0))
        return glm.scale(model, glm.vec3(1.0))
