"""Combat unit movement and damage response."""

import math
import random

import glm

from ..logic import aabb_overlap


_VEHICLE_PRESENTATION = {
    "scout": (1.6, 1.6, .78, (.76, .72, .92), (0.55, 0.86, 1.0), 12.0),
    "striker": (2.0, 2.0, 1.0, (1.0, 1.0, 1.0), (1.0, 0.78, 0.42), 14.0),
    "bulwark": (3.2, 3.2, 1.48, (1.42, 1.16, 1.5), (1.0, 0.48, 0.34), 19.0),
    "wraith": (1.8, 1.8, .92, (.86, .84, 1.34), (0.72, 0.62, 1.0), 11.0),
    "boss": (5.4, 5.4, 2.25, (2.15, 1.7, 2.35), (1.0, 0.28, 0.34), 25.0),
}


class Enemy:
    def __init__(self, x, z, health=3, speed=2.8, fire_interval=1.75,
                 elite=False, kind=None):
        self.x, self.z = float(x), float(z)
        self.kind = kind or ("bulwark" if elite else "striker")
        (width, depth, self.model_scale, self.shape_scale, self.base_color,
         self.preferred_range) = (
            _VEHICLE_PRESENTATION.get(self.kind, _VEHICLE_PRESENTATION["striker"]))
        self.is_boss = self.kind == "boss"
        self.elite = elite or self.is_boss
        self.width, self.depth = width, depth
        self.health = int(health)
        self.max_health = max(1, self.health)
        self.color = self.base_color
        self.speed = float(speed)
        self.base_speed = self.speed
        self.fire_interval = float(fire_interval)
        self.base_fire_interval = self.fire_interval
        self.shoot_timer = random.uniform(0.7, self.fire_interval)
        self.flash_timer = 0.0
        self.rotation_y = 0.0
        self.phase = 1

    def update(self, delta_time, player_x, player_z, obstacles, arena_size):
        dx, dz = player_x - self.x, player_z - self.z
        distance = max(0.001, math.hypot(dx, dz))
        self.rotation_y = math.atan2(dx, dz)

        # Approach to firing range, steering away from cover before it blocks movement.
        if distance > self.preferred_range:
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
        else:
            self.color = self.base_color

    def update_boss_phase(self):
        """Increase pressure as the boss chassis loses armor."""
        if not self.is_boss:
            return None
        health_ratio = self.health / self.max_health
        next_phase = 3 if health_ratio <= .32 else 2 if health_ratio <= .66 else 1
        if next_phase == self.phase:
            return None
        self.phase = next_phase
        self.speed = self.base_speed * (1.0 + .16 * (next_phase - 1))
        self.fire_interval = max(.8, self.base_fire_interval *
                                 (1.0 - .2 * (next_phase - 1)))
        self.shoot_timer = min(self.shoot_timer, .45)
        self.base_color = ((1.0, .58, .24) if next_phase == 2 else
                           (1.0, .18, .24))
        self.color = self.base_color
        self.flash_timer = .32
        return next_phase

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
        if not any(aabb_overlap(nx, nz, self.width * .85, self.depth * .85, box.x, box.z,
                                box.width, box.depth) for box in obstacles):
            self.x, self.z = nx, nz

    def get_model_matrix(self):
        model = glm.translate(glm.mat4(1.0), glm.vec3(self.x, 0.0, self.z))
        model = glm.rotate(model, self.rotation_y, glm.vec3(0.0, 1.0, 0.0))
        return glm.scale(model, glm.vec3(*self.shape_scale))
