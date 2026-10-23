"""Timed field supplies dropped during a run."""

import glm


class Loot:
    def __init__(self, x, z, amount=25):
        self.x, self.z = float(x), float(z)
        self.amount = int(amount)
        self.age = 0.0
        self.lifespan = 18.0

    def update(self, delta_time):
        self.age += delta_time
        return self.age >= self.lifespan

    def get_model_matrix(self):
        bob = 0.42 + 0.08 * ((self.age * 2.0) % 1.0)
        model = glm.translate(glm.mat4(1.0), glm.vec3(self.x, bob, self.z))
        model = glm.rotate(model, self.age * 0.7, glm.vec3(0, 1, 0))
        return glm.scale(model, glm.vec3(0.42))
