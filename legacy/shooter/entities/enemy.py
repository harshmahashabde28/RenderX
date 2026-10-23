"""Combat unit movement and damage response."""

import math
import random

import glm

from ..logic import aabb_overlap


class Enemy:
    def __init__(self, x, z, health=3, speed=2.8, fire_interval=1.75,
                 elite=False):
        self.x, self.z = float(x), float(z)
        self.elite = elite
        self.width = self.depth = 3.2 if elite else 2.0
        self.model_scale = 1.45 if elite else 1.0
        self.health = int(health)
        self.color = (1.0, 1.0, 1.0)
        self.speed = float(speed)
        self.fire_interval = float(fire_interval)
        self.shoot_timer = random.uniform(0.7, self.fire_interval)
        self.flash_timer = 0.0
        self.rotation_y = 0.0

    def update(self, delta_time, player_x, player_z, obstacles, arena_size):
        dx, dz = player_x - self.x, player_z - self.z
        distance = max(0.001, math.hypot(dx, dz))
        self.rotation_y = math.atan2(dx, dz)

        # Approach to firing range, steering away from cover before it blocks movement.
        if distance > 14.0:
            vx, vz = dx / distance, dz / distance
            for box in obstacles:
                ox, oz = self.x - box.x, self.z - box.z
                separation = math.hypot(ox, oz)
                if 0.001 < separation < 5.5:
                    force = (5.5 - separation) / 5.5 * 1.7
                    vx += ox / separation * force
                    vz += oz / separation * force
            length = math.hypot(vx, vz) or 1.0
            vx, vz = vx / length, vz / length
            self._try_move(vx * self.speed * delta_time, 0, obstacles, arena_size)
            self._try_move(0, vz * self.speed * delta_time, obstacles, arena_size)

        self.shoot_timer -= delta_time
        self.flash_timer = max(0.0, self.flash_timer - delta_time)
        if self.flash_timer:
            self.color = (1.0, 0.42, 0.34)
        elif self.elite:
            self.color = (1.0, .74, .34)
        else:
            self.color = (1.0, 1.0, 1.0)

    def hit(self):
        self.health -= 1
        self.flash_timer = 0.11
        self.color = (1.0, 0.42, 0.34)
        return self.health <= 0

    def can_shoot(self):
        if self.shoot_timer > 0:
            return False
        self.shoot_timer = self.fire_interval * random.uniform(0.84, 1.16)
        return True

    def _try_move(self, dx, dz, obstacles, arena_size):
        nx = max(-arena_size, min(arena_size, self.x + dx))
        nz = max(-arena_size, min(arena_size, self.z + dz))
        if not any(aabb_overlap(nx, nz, 1.7, 1.7, box.x, box.z,
                                box.width, box.depth) for box in obstacles):
            self.x, self.z = nx, nz

    def get_model_matrix(self):
        model = glm.translate(glm.mat4(1.0), glm.vec3(self.x, 0.0, self.z))
        model = glm.rotate(model, self.rotation_y, glm.vec3(0.0, 1.0, 0.0))
        return glm.scale(model, glm.vec3(self.model_scale))
