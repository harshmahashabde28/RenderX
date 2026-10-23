"""Destructible cover placement and transform."""

import math
import random

import glm


class Box:
    def __init__(self, start_x, start_z):
        self.x = start_x
        self.z = start_z
        self.width = 2.0
        self.depth = 2.0
        self.health = 3
        self.color = (1.0, 1.0, 1.0)
        self.rotation_y = random.uniform(0.0, math.tau)

    def get_model_matrix(self):
        model = glm.translate(glm.mat4(1.0), glm.vec3(self.x, 0.5, self.z))
        model = glm.rotate(model, self.rotation_y, glm.vec3(0.0, 1.0, 0.0))
        return glm.scale(model, glm.vec3(self.width, self.width, self.depth))
