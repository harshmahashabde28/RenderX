"""Application lifecycle and frame loop."""
import pygame
from renderx import config


def run():
    try:
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("RenderX | 3D Wireframe Explorer")
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(config.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            screen.fill(config.BACKGROUND)
            pygame.display.flip()
    finally:
        pygame.quit()
