"""Transient notification banner and legacy feedback panel."""
import pygame


class Panel:
    def __init__(self):
        self.message = ""
        self.message_until = 0

    def notify(self, message: str):
        self.message = str(message)
        self.message_until = pygame.time.get_ticks() + 6000
