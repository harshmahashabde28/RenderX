"""Initialise once, then input -> update -> draw -> display at up to 60 FPS."""
import pygame
from renderx import config
from renderx.camera import Camera
from renderx.input import Controls
from renderx.models import make_models
from renderx.renderer import draw_wireframe
from renderx.scene import Scene
from renderx.ui import Panel


def run():
    try:
        # No audio is used, so only initialise the modules we need.
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("RenderX | 3D Wireframe Explorer")
        clock = pygame.time.Clock()
        models, scene, camera = make_models(), Scene(), Camera()
        controls, panel = Controls(), Panel()
        running = True
        while running:
            dt = clock.tick(config.FPS) / 1000.0  # milliseconds -> seconds
            events = pygame.event.get()  # Also pumps the current input state.
            running = controls.update(
                scene, events, pygame.key.get_pressed(), dt, panel,
                pygame.mouse.get_pos(), pygame.key.get_mods(),
            )
            if not running:
                break
            mesh = models[scene.shape]
            draw_wireframe(screen, mesh, scene, camera)
            panel.draw(screen, scene, mesh, clock.get_fps())
            pygame.display.flip()
    finally:
        pygame.quit()
