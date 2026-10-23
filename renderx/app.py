"""Initialise once, then input -> update -> draw -> display at up to 60 FPS."""
from secrets import randbelow
from pathlib import Path

import pygame

from renderx import config
from renderx.audio import AudioManager
from renderx.camera import Camera
from renderx.dashboard import Dashboard
from renderx.file_dialog import FileDialogUnavailable, choose_obj_file
from renderx.input import Controls
from renderx.models import make_library
from renderx.obj_loader import SAMPLE_OBJ, load_obj
from renderx.quest import CHALLENGES, QuestState, clipped_edge_count, make_challenge_scene
from renderx.quest_ui import clear_font_cache
from renderx.maze import MazeState
from renderx.scene import Scene
from renderx.screenshots import save_screenshot
from renderx.shapes import update_signal_wave
from renderx.ui import Panel
from renderx.ui import fonts
from renderx.ui import brand as brand_assets
from renderx.ui.identity import set_window_identity
from renderx.ui.theme import METRICS
from renderx.window import WindowView, enable_dpi_awareness, initial_size
from renderx import theme


def load_sample(scene, models, path=SAMPLE_OBJ):
    try:
        mesh = load_obj(path)
    except (OSError, ValueError, UnicodeError) as error:
        return f"OBJ load failed: {error}"
    models["OBJ house"] = mesh
    scene.select("OBJ house")
    return "Loaded sample OBJ: house"


def load_obj_file(path, scene, models):
    """Load an OBJ under a unique scene name and remember its source path."""
    path = Path(path)
    try:
        mesh = load_obj(path)
    except (OSError, ValueError, UnicodeError) as error:
        return f"Could not open {path.name}: {error}"
    base = path.stem.strip() or "Model"
    name = base
    suffix = 2
    while name in models:
        name = f"{base} ({suffix})"
        suffix += 1
    models[name] = mesh
    scene.select(name)
    theme.remember_file(path)
    return f"Opened {path.name}"


def export_frame(screen, panel):
    try:
        path = save_screenshot(screen)
    except (OSError, pygame.error) as error:
        panel.notify(f"Screenshot failed: {error}")
    else:
        panel.notify(f"Saved screenshots/{path.name}")


def _initial_destination(*, skip_landing=False, mode=None):
    """Choose the explicit launch destination, defaulting to the landing page."""
    mode_destinations = {
        "explore": "Explore", "challenge": "Challenges",
        "maze": "Maze", "shooter": "Shooter",
    }
    if mode:
        return mode_destinations[mode]
    return "Explore" if skip_landing else "Landing"


def run(*, skip_landing=False, mode=None):
    try:
        enable_dpi_awareness()
        pygame.display.init()
        pygame.font.init()
        theme.load()
        display = pygame.display.set_mode(
            initial_size(pygame.display.get_desktop_sizes()[0]), pygame.RESIZABLE)
        windowed_size = display.get_size()
        is_fullscreen = False
        window = WindowView(display.get_size(), display.get_size())
        canvas = pygame.Surface(display.get_size())
        set_window_identity("RenderX")
        clock = pygame.time.Clock()
        models, explore_scene, camera = make_library(), Scene(), Camera()
        quest = QuestState()
        maze = MazeState(seed=randbelow(1_000_000))
        quest_scene = make_challenge_scene(CHALLENGES[0])
        loaded_challenge = 0
        wave_time = 0.0
        controls, panel = Controls(), Panel()
        dashboard = Dashboard(panel)
        audio = AudioManager()
        dashboard.set_audio(audio)
        dashboard.maze_state = maze
        dashboard.active_destination = _initial_destination(
            skip_landing=skip_landing, mode=mode)
        pygame.display.set_caption(_window_title(dashboard.active_destination))
        dashboard.draw(canvas, models['Cube'], explore_scene, models, camera,
                       0, pygame.mouse.get_pos(), quest, maze)
        running = True

        while running:
            dt = clock.tick(config.FPS) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    requested_size = (max(METRICS["min_width"], event.w),
                                      max(METRICS["min_height"], event.h))
                    display = pygame.display.set_mode(
                        requested_size, pygame.FULLSCREEN if is_fullscreen
                        else pygame.RESIZABLE)
                    if not is_fullscreen:
                        windowed_size = display.get_size()
                    canvas = pygame.Surface(display.get_size())
                    controls.cancel_drag()
                    dashboard.canvas_size = display.get_size()
            window.resize(display.get_size(), display.get_size())
            events = [window.event(event) for event in events]
            maze_events = events
            mouse = window.point(pygame.mouse.get_pos())
            prior_destination = dashboard.active_destination
            dashboard.destination_changed = False
            prior_maze = (maze.steps, maze.scans_used, len(maze.keys_found),
                          maze.won, maze.message)
            active_scene = (quest_scene if dashboard.active_destination == 'Challenges'
                            else explore_scene)
            events = dashboard.events(events, active_scene, models, quest, controls, maze)
            if dashboard.fullscreen_requested != is_fullscreen:
                is_fullscreen = dashboard.fullscreen_requested
                if is_fullscreen:
                    windowed_size = display.get_size()
                    target_size = pygame.display.get_desktop_sizes()[0]
                    display = pygame.display.set_mode(target_size, pygame.FULLSCREEN)
                else:
                    display = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                canvas = pygame.Surface(display.get_size())
                window = WindowView(display.get_size(), display.get_size())
                dashboard.canvas_size = display.get_size()
                controls.cancel_drag()
            selected_path = dashboard.requested_path
            dashboard.requested_path = None
            if dashboard.open_file_requested:
                dashboard.open_file_requested = False
                try:
                    selected_path = choose_obj_file()
                except FileDialogUnavailable as error:
                    panel.notify(f"Could not open the file chooser: {error}")
            if selected_path:
                active_scene = explore_scene
                result = load_obj_file(selected_path, active_scene, models)
                panel.notify(result)
                if result.startswith("Opened "):
                    dashboard._set_destination("Explore")
            if dashboard.active_destination != prior_destination:
                audio.switch_music("maze" if dashboard.active_destination == "Maze"
                                   else None)
            if dashboard.shooter_requested:
                dashboard.shooter_requested = False
                return_destination = dashboard.previous_destination
                host_size = display.get_size()
                controls.cancel_drag()
                launch_error = None
                keep_host_open = True
                try:
                    from renderx.shooter import run_shooter
                    audio.switch_music("shooter")
                    keep_host_open = run_shooter(audio=audio)
                except Exception as error:
                    # Breakpoint needs optional graphics drivers and packages.
                    # Keep the renderer usable when that runtime is unavailable.
                    detail = str(error).splitlines()[0].strip()
                    launch_error = (f"Breakpoint could not start: {detail}"
                                    if detail else
                                    f"Breakpoint could not start ({type(error).__name__}).")
                finally:
                    restore_size = (pygame.display.get_desktop_sizes()[0]
                                    if is_fullscreen else host_size)
                    display = pygame.display.set_mode(
                        restore_size, pygame.FULLSCREEN if is_fullscreen
                        else pygame.RESIZABLE)
                    set_window_identity("RenderX")
                    dashboard._cursor_kind = None
                    dashboard._set_cursor("arrow")
                    window = WindowView(pygame.display.get_surface().get_size())
                    canvas = pygame.Surface(display.get_size())
                    window.resize(display.get_size(), display.get_size())
                    dashboard._set_destination(return_destination)
                    dashboard.music_muted = audio.music_muted
                    dashboard.audio_volume = audio.volume
                    audio.switch_music("maze" if return_destination == "Maze"
                                       else None)
                if not keep_host_open:
                    break
                if launch_error:
                    panel.notify(launch_error)

            if quest.current != loaded_challenge:
                if not quest.done:
                    quest_scene = make_challenge_scene(CHALLENGES[quest.current])
                else:
                    # Leave a readable final model in view after the close-up
                    # clipping experiment, which may have crossed the camera.
                    quest_scene = make_challenge_scene(CHALLENGES[-1])
                    quest_scene.position = (0.0, 0.0, 5.0)
                loaded_challenge = quest.current
            active_scene = (quest_scene if dashboard.active_destination == 'Challenges'
                            else explore_scene)
            allowed_controls = None
            if dashboard.active_destination == 'Challenges':
                challenge = quest.challenge
                allowed_controls = () if challenge is None else challenge.allowed_controls
                maze.look_drag = False
            elif dashboard.active_destination == 'Maze':
                allowed_controls = ()
                maze.handle_mouse(maze_events, viewport=dashboard.view_rect)
            elif dashboard.active_destination == 'Shooter':
                allowed_controls = ()
                maze.look_drag = False
            elif dashboard.active_destination == 'Landing':
                allowed_controls = ()
            else:
                maze.look_drag = False

            if dashboard.destination_changed:
                allowed_controls = ()

            running = controls.update(
                active_scene, events, pygame.key.get_pressed(), dt, panel,
                dashboard.map_position(mouse), pygame.key.get_mods(),
                allowed_controls=allowed_controls)
            if not running:
                break
            dashboard.destination_changed = False
            if dashboard.active_destination == 'Maze' and controls.focused:
                maze.update(pygame.key.get_pressed(), dt)
            if dashboard.active_destination == "Maze":
                old_steps, old_scans, old_keys, old_won, old_message = prior_maze
                if maze.scans_used > old_scans:
                    audio.play("scan")
                if len(maze.keys_found) > old_keys:
                    audio.play("confirm")
                if maze.steps > old_steps:
                    audio.play("footstep", cooldown=0.14)
                if not old_won and maze.won:
                    audio.play("confirm")
                if maze.message != old_message and maze.message.startswith(
                        "The exit is locked"):
                    audio.play("locked")
            if (dashboard.active_destination == 'Explore' and
                    active_scene.shape == 'Signal wave' and dashboard.wave_playing):
                wave_time += min(max(dt, 0.0), config.MAX_DT)
                update_signal_wave(models['Signal wave'], wave_time)
            if controls.load_requested:
                panel.notify(load_sample(active_scene, models))

            mesh = models[active_scene.shape]
            if dashboard.active_destination == 'Challenges' and not quest.done:
                challenge = quest.challenge
                if challenge.kind == 'align':
                    quest.observe_alignment(active_scene.angles)
                elif challenge.kind == 'choice':
                    quest.observe_depth(active_scene.position[2])
                elif challenge.kind == 'choice_gated':
                    quest.observe_clipping(clipped_edge_count(mesh, active_scene, camera))

            dashboard.draw(canvas, mesh, active_scene, models, camera,
                           clock.get_fps(), mouse, quest, maze, dt)
            title = _window_title(dashboard.active_destination)
            if pygame.display.get_caption()[0] != title:
                pygame.display.set_caption(title)
            window.draw(display, canvas)
            if controls.screenshot_requested:
                export_frame(canvas, panel)
            pygame.display.flip()
    finally:
        if "audio" in locals():
            audio.switch_music(None)
        clear_font_cache()
        fonts.clear_cache()
        brand_assets.clear_cache()
        pygame.quit()


def _window_title(destination):
    """Keep the native title synchronized with the visible destination."""
    label = {"Landing": "Welcome", "Explore": "Explore",
             "Challenges": "Challenge", "Maze": "Maze",
             "Shooter": "Breakpoint"}.get(destination, "RenderX")
    return f"RenderX · {label}"
