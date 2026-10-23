"""Transient notification state shown in the renderer workspace."""

import pygame


class Panel:
    def __init__(self):
        self.message = ""
        self.message_until = 0

    def notify(self, message):
        self.message = str(message)
        self.message_until = pygame.time.get_ticks() + 6000
