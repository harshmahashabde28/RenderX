"""Initialise once, then input -> update -> draw -> display at up to 60 FPS."""
import pygame
from renderx import config
from renderx.camera import Camera
from renderx.axes import draw_axes
from renderx.obj_loader import SAMPLE_OBJ, load_obj
from renderx.input import Controls
from renderx.models import make_models
from renderx.learning import LearningState
from renderx.pipeline import snapshot_vertex
from renderx.renderer import draw_wireframe, draw_selected_vertex
from renderx.scene import Scene
from renderx.screenshots import save_screenshot
from renderx.ui import Panel


def load_sample(scene, models, path=SAMPLE_OBJ):
    try:
        mesh = load_obj(path)
    except (OSError, ValueError, UnicodeError) as error:
        return f"OBJ load failed: {error}"
    models["OBJ house"] = mesh
    scene.select("OBJ house")
    return "Loaded OBJ house (O reloads assets/models/house.obj)"


def export_frame(screen, panel):
    try:
        path = save_screenshot(screen)
    except (OSError, pygame.error) as error:
        panel.notify(f"Screenshot failed: {error}")
    else:
        panel.notify(f"Saved screenshots/{path.name}")


def run():
    try:
        # No audio is used, so only initialise the modules we need.
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("RenderX | Learning Laboratory - Checkpoint 3")
        clock = pygame.time.Clock()
        models, scene, camera = make_models(), Scene(), Camera()
        controls, panel = Controls(), Panel()
        learning = LearningState()
        previous_mesh = models[scene.shape]
        running = True
        while running:
            dt = clock.tick(config.FPS) / 1000.0  # milliseconds -> seconds
            events = pygame.event.get()  # Also pumps the current input state.
            running = controls.update(
                scene, events, pygame.key.get_pressed(), dt, panel,
                pygame.mouse.get_pos(), pygame.key.get_mods(),
                learning=learning,
            )
            if not running:
                break
            if controls.load_requested:
                panel.notify(load_sample(scene, models))
            mesh = models[scene.shape]
            if mesh is not previous_mesh:
                learning.selected_vertex = 0
                previous_mesh = mesh
            learning.select_vertex(controls.vertex_step, len(mesh.vertices))
            panel_width = (config.INSPECTOR_WIDTH if learning.mode == "Pipeline"
                           else config.PANEL_WIDTH)
            window_size = (config.VIEW_WIDTH + panel_width, config.HEIGHT)
            if screen.get_size() != window_size:
                screen = pygame.display.set_mode(window_size)
            draw_wireframe(screen, mesh, scene, camera)
            if scene.axes_visible:
                draw_axes(screen, camera, scene.projection, panel.small)
            snapshots = None
            if learning.mode == "Pipeline":
                snapshots = snapshot_vertex(mesh.vertices[learning.selected_vertex],
                                            scene, camera)
                draw_selected_vertex(screen, snapshots[-1].coordinates,
                                     learning.selected_vertex, panel.normal)
            panel.draw(screen, scene, mesh, clock.get_fps(), learning, snapshots)
            if controls.screenshot_requested:
                export_frame(screen, panel)
            pygame.display.flip()
    finally:
        pygame.quit()
