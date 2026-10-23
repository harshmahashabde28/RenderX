"""Projectile motion and render transform."""

import math

import glm


class Projectile:
    def __init__(self, start_x, start_z, angle, speed=40.0, team="player"):
        self.x = start_x
        self.z = start_z
        self.angle = angle
        self.speed = speed
        self.lifespan = 2.0
        self.age = 0.0
        self.team = team
        self.radius = 0.8
        self.vel_x = math.sin(angle) * speed
        self.vel_z = math.cos(angle) * speed

    def update(self, delta_time):
        self.x += self.vel_x * delta_time
        self.z += self.vel_z * delta_time
        self.age += delta_time

    def get_model_matrix(self):
        model = glm.translate(glm.mat4(1.0), glm.vec3(self.x, 1.0, self.z))
        model = glm.rotate(model, self.angle + math.pi, glm.vec3(0.0, 1.0, 0.0))
        return glm.scale(model, glm.vec3(4.0))
