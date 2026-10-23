"""Responsive editor shell for RenderX's renderer, challenges, and games."""

from math import cos, degrees, pi, radians, sin

import pygame

from renderx import config, theme as appearance
from renderx.input_map import (EDITOR_KEYS, GLOBAL_KEYS, MAZE_KEYS,
                               MOUSE_BUTTONS, has_primary_modifier, help_rows,
                               modifier_name, navigation_status, view_shortcut)
from renderx.axes import draw_axes
from renderx.camera import Camera
from renderx.maze import MazeState
from renderx.maze_ui import draw_maze_view
from renderx.quest import CHALLENGES, QuestState, clipped_edge_count
from renderx.quest_ui import draw_comparison_challenge, draw_near_plane_guide
from renderx.rasterizer import RENDER_MODES, draw_render_mode
from renderx.renderer import draw_wireframe
from renderx.scene import Scene
from renderx.ui import animation, fonts, icons, layout as layout_module
from renderx.ui import brand, landing as landing_page
from renderx.ui import theme as ui_theme
from renderx.ui.components import (draw_button, draw_overlay, draw_segmented,
                                   draw_slider, draw_splitter, draw_status,
                                   draw_tooltip, draw_preferences, draw_file_menu,
                                   draw_context_menu, draw_dropdown_options)
from renderx.ui.components.button import icon_button_rect
from renderx.ui.components import draw_welcome
from renderx.ui.panels import (ScenePanel, draw_challenge_panel,
                               draw_inspector_panel, draw_maze_panel,
                               draw_shooter_panel)
from renderx.ui.panels.common import draw_panel


# Kept as a conventional first-frame size; the live canvas follows the window.
SIZE = (1360, 900)
VIEW = pygame.Rect(0, 0, 820, 740)
_DESTINATIONS = ("Explore", "Challenges", "Maze", "Shooter")
_TAB_ORDER = ("Explore", "Challenges", "Maze", "Shooter")


def _event_modifiers(event):
    """Read event modifiers without querying an uninitialised SDL video device."""
    if hasattr(event, "mod"):
        return event.mod
    try:
        return pygame.key.get_mods()
    except pygame.error:
        return 0


class _PanelUI:
    """Small adapter that lets panel renderers share Dashboard actions."""

    def __init__(self, dashboard):
        self.dashboard = dashboard

    @property
    def buttons(self):
        return self.dashboard.buttons

    @property
    def focused_field(self):
        return self.dashboard.focused_field

    @property
    def render_mode(self):
        return self.dashboard.render_mode

    def button(self, action, label, rect, active=False):
        self.dashboard.button(action, label, rect, active)

    def paint_button(self, surface, action, *, mode="dark", state=None,
                     shortcut=None, icon=None, align="center"):
        return self.dashboard.paint_button(surface, action, mode=mode,
                                           state=state, shortcut=shortcut,
                                           icon=icon, align=align)

    def state(self, action):
        return self.dashboard.state(action)

    def section_open(self, name):
        return name in self.dashboard.open_sections

    def segmented(self, surface, action, options, selected, rect, *, mode="dark"):
        items = draw_segmented(surface, rect, options, selected, mode=mode)
        for value, item in items.items():
            key = (*action, value)
            self.button(key, value, item, active=value == selected)
            if key == self.dashboard.focused_action:
                colors = ui_theme.palette(mode)
                pygame.draw.rect(surface, colors["FOCUS"], item, 1,
                                 border_radius=ui_theme.METRICS["radius"])
        return items

    def field_text(self, action, value):
        if action == self.focused_field:
            return self.dashboard.field_buffer
        return str(value)


class Dashboard:
    """Route input and layout between existing RenderX destinations."""

    def __init__(self, panel):
        self.panel = panel
        self.buttons = {}
        self.labels = {}
        self.active = set()
        self.hover = None
        self.pressed = None
        self._cursor_kind = None
        self.animator = animation.Animator()
        self.scene_panel = ScenePanel()
        self.ui = _PanelUI(self)
        self.open_sections = {"transform", "display"}
        self.active_destination = "Explore"
        self.landing_focus = ("landing", "explore")
        self.confirm_home_open = False
        self.confirm_home_rect = None
        self.icon_placements = {}
        self._page_states = {}
        self._controls = None
        self.destination_changed = False
        self._transition_elapsed = None
        self._transition_surface = None
        self._transition_surface_size = None
        self.maze_state = None
        self.shape_menu_open = False
        self.focused = True
        self.left_collapsed = False
        self.right_collapsed = False
        self.focused_action = None
        self.field_replace = False
        self.view_rect = VIEW.copy()
        self.maze_controls_rect = None
        self.app_layout = None
        self.render_mode = "Wireframe"
        self.wave_playing = True
        self.theme_mode = appearance.mode()
        self.audio = None
        self.audio_volume = 0.66
        self.music_muted = False
        self.shooter_requested = False
        self.previous_destination = "Explore"
        self.help_open = False
        self.help_rect = None
        self.about_open = False
        self.about_rect = None
        self.preferences_open = False
        self.preferences_rect = None
        self.file_menu_open = False
        self.file_menu_rect = None
        self.context_menu_open = False
        self.context_menu_rect = None
        self.context_menu_position = (0, 0)
        self.context_menu_target = None
        self.context_menu_actions = []
        self.context_menu_index = 0
        self._context_press = None
        self._context_buffer = []
        self.render_mode_open = False
        self.render_mode_menu_rect = None
        self.render_mode_index = 0
        self.welcome_open = False
        self.welcome_rect = None
        self.open_file_requested = False
        self.fullscreen_requested = False
        self.requested_path = None
        self.focused_field = None
        self.field_buffer = ""
        self.drag_action = None
        self._slider_last_x = None
        self.drag_splitter = None
        self.left_width = None
        self.right_width = None
        self.canvas_size = SIZE
        self._dt = 1 / config.FPS
        self._hover_started = 0
        self._last_hover = None
        for destination in _DESTINATIONS:
            self._page_states[destination] = {
                "left_collapsed": self.left_collapsed,
                "right_collapsed": self.right_collapsed,
                "left_width": self.left_width,
                "right_width": self.right_width,
                "open_sections": set(self.open_sections),
                "scene_scroll": self.scene_panel.scroll,
                "objects_open": self.scene_panel.objects_open,
                "render_mode": self.render_mode,
            }

    def button(self, action, label, rect, active=False):
        self.buttons[action] = pygame.Rect(rect)
        self.labels[action] = str(label)
        if active:
            self.active.add(action)

    def set_audio(self, audio):
        """Attach the shared audio service used by the app and shooter."""
        self.audio = audio
        if audio is not None:
            self.audio_volume = audio.volume
            self.music_muted = audio.music_muted

    def _play_ui_click(self):
        if self.audio is not None:
            self.audio.play("ui_click")

    def _save_audio_preferences(self):
        if self.audio is not None:
            self.audio.save_settings()

    def layout(self, scene, models, quest_state=None, maze_state=None, size=None,
               prime=True):
        """Refresh responsive canvas geometry and the global toolbar actions."""
        self.canvas_size = tuple(size or self.canvas_size or SIZE)
        if maze_state is not None:
            self.maze_state = maze_state
        self.app_layout = layout_module.build_layout(
            self.canvas_size, self.left_width, self.right_width,
            self.left_collapsed, self.right_collapsed)
        self.view_rect = self.app_layout.viewport.copy()
        self.maze_controls_rect = None
        if self.active_destination == "Maze":
            strip_h = ui_theme.METRICS["control_height"] + ui_theme.SPACE["xl"]
            self.view_rect.height = max(1, self.view_rect.height - strip_h)
            self.maze_controls_rect = pygame.Rect(
                self.app_layout.viewport.x, self.view_rect.bottom,
                self.app_layout.viewport.width, strip_h)
        self.buttons.clear()
        self.labels.clear()
        self.active.clear()
        self.icon_placements.clear()
        if self.active_destination != "Landing":
            self._register_toolbar(scene)
        if prime and self.active_destination != "Landing":
            scratch = pygame.Surface(self.canvas_size)
            self._draw_panels(scratch, scene, models, quest_state, maze_state,
                              ui_theme.palette(self.theme_mode))
            if self.active_destination == "Maze" and self.maze_controls_rect:
                self._draw_maze_action_bar(scratch, self.maze_controls_rect,
                                           maze_state or MazeState())
        return self.app_layout

    def _register_toolbar(self, scene):
        layout = self.app_layout
        for name, rect in layout.navigation.items():
            label = layout_module.DESTINATION_LABELS[name]
            self.button(("destination", name), label, rect,
                        active=self.active_destination == name)
        self.button(("home",), f"Return to landing · {modifier_name()}+Shift+H",
                    layout.brand)
        if self.active_destination == "Explore":
            # Individual segments are added while drawing. Keep a broad fallback
            # so tests and the first interactive frame can still toggle projection.
            self.button(("projection", "toggle"), "Projection", layout.projection)
            self.button(("render_menu",), self.render_mode, layout.render_mode)
        elif self.active_destination == "Maze":
            self.button(("maze_projection_toolbar",), "Projection",
                        layout.projection)
        if self.active_destination == "Explore":
            self.button(("toolbar_open_obj",),
                        f"Open OBJ · {modifier_name()}+O", layout.import_obj)
        self.button(("screenshot",),
                    f"Export screenshot · {modifier_name()}+S / F12",
                    layout.screenshot)
        self.button(("theme",), "Toggle light and dark theme", layout.theme_toggle)
        self.button(("help",), "Keyboard shortcuts · F1", layout.help_button)
        self.button(("music_toggle",),
                    "Unmute music" if self.music_muted else "Mute music",
                    layout.music_toggle)
        self.button(("audio_volume",), "Master volume", layout.audio_slider)
        splitter_hit = ui_theme.SPACE["sm"]
        self.button(("splitter", "left"), "Resize scene dock",
                    layout.left_splitter.inflate(splitter_hit, 0))
        self.button(("splitter", "right"), "Resize inspector dock",
                    layout.right_splitter.inflate(splitter_hit, 0))

    def map_position(self, position):
        """Map the current 3D view into the engine's stable input coordinate space."""
        if self.view_rect.collidepoint(position):
            return ((position[0] - self.view_rect.x) * config.VIEW_WIDTH /
                    max(1, self.view_rect.w),
                    (position[1] - self.view_rect.y) * config.HEIGHT /
                    max(1, self.view_rect.h))
        return (-100, -100)

    def _map_pointer_event(self, event):
        """Convert a pointer event to the stable renderer coordinate space."""
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                              pygame.MOUSEMOTION):
            return event
        values = event.dict.copy()
        values["pos"] = self.map_position(event.pos)
        if "rel" in values:
            values["rel"] = (
                event.rel[0] * config.VIEW_WIDTH / max(1, self.view_rect.w),
                event.rel[1] * config.HEIGHT / max(1, self.view_rect.h),
            )
        return pygame.event.Event(event.type, values)

    def _context_items(self, scene):
        if self.context_menu_target is not None:
            target = self.context_menu_target
            items = [(("shape", target), "Select / frame object")]
            if target == scene.shape:
                items.append((("reset",), "Reset transform"))
            return items
        return [
            (("reset",), "Reset transform"),
            (("view_axis", "Z", 1), "Front view"),
            (("view_axis", "X", 1), "Right view"),
            (("view_axis", "Y", 1), "Top view"),
            (("projection", "toggle"), "Toggle projection"),
        ]

    def _open_context_menu(self, position, target, scene, controls):
        self.context_menu_open = True
        self.context_menu_rect = None
        self.context_menu_position = tuple(position)
        self.context_menu_target = target
        self.context_menu_actions = [action for action, _ in
                                     self._context_items(scene)]
        self.context_menu_index = 0
        self.hover = None
        self.pressed = None
        controls.cancel_drag()
        controls.focused = False

    def _close_context_menu(self, controls):
        self.context_menu_open = False
        self.context_menu_rect = None
        self.context_menu_target = None
        self.context_menu_actions = []
        self.context_menu_index = 0
        self.hover = None
        controls.cancel_drag()
        controls.focused = self.focused

    def _modal_open(self):
        return any((self.help_open, self.about_open, self.preferences_open,
                    self.file_menu_open, self.context_menu_open,
                    self.render_mode_open, self.welcome_open,
                    self.confirm_home_open))

    def events(self, events, scene, models, quest_state, controls, maze_state=None):
        """Handle dashboard controls; forward only canvas input to the engine."""
        self._controls = controls
        controls.observe_events(events)
        maze_state = maze_state or self.maze_state
        controls.navigation_preset = appearance.navigation_preset()
        if self.help_open:
            controls.focused = False
            controls.cancel_drag()
        if self.about_open:
            controls.focused = False
            controls.cancel_drag()
        if self.preferences_open:
            controls.focused = False
            controls.cancel_drag()
        if self.file_menu_open:
            controls.focused = False
            controls.cancel_drag()
        if self.context_menu_open:
            controls.focused = False
            controls.cancel_drag()
        if self.render_mode_open:
            controls.focused = False
            controls.cancel_drag()
        if self.welcome_open:
            controls.focused = False
            controls.cancel_drag()
        if self.confirm_home_open:
            controls.focused = False
            controls.cancel_drag()
        output = []
        for event in events:
            if (self._transition_elapsed is not None and
                    event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)):
                self._transition_elapsed = None
            if event.type == pygame.MOUSEBUTTONUP:
                # Release visual button state even when an overlay consumes the
                # pointer event before it reaches the regular control branch.
                self.pressed = None
            if event.type == getattr(pygame, "DROPFILE", -1):
                self.requested_path = getattr(event, "file", None)
                controls.focused = self.focused
                continue
            if event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
                self.focused = False
                self.drag_action = self.drag_splitter = None
                self._context_press = None
                self._context_buffer.clear()
                self.hover = self.pressed = None
                self.context_menu_open = False
                self.context_menu_rect = None
                self.about_open = False
                self.about_rect = None
                self.confirm_home_open = False
                self.confirm_home_rect = None
                controls.cancel_drag()
                self._set_cursor("arrow")
                self._save_audio_preferences()
                if self.active_destination == "Maze" and maze_state and not maze_state.won:
                    maze_state.paused = True
                    maze_state.message = "Run paused while the window was inactive."
                    maze_state.message_time = 60.0
                continue
            if event.type == pygame.WINDOWFOCUSGAINED:
                self.focused = True
                controls.cancel_drag()
                continue
            if event.type == pygame.WINDOWLEAVE:
                self.hover = None
                self.pressed = None
                self._set_cursor("arrow")
            if (event.type == pygame.MOUSEBUTTONDOWN and
                    event.button == MOUSE_BUTTONS["secondary"] and
                    self.active_destination == "Explore" and self.focused and
                    not self._modal_open()):
                action = self._action_at(event.pos)
                if self.view_rect.collidepoint(event.pos):
                    self._context_press = {
                        "position": tuple(event.pos), "target": None,
                        "moved": False,
                    }
                    self._context_buffer = [event]
                    controls.focused = False
                    continue
                if action and action[0] == "shape":
                    self._context_press = {
                        "position": tuple(event.pos), "target": action[1],
                        "moved": False,
                    }
                    self._context_buffer.clear()
                    controls.focused = False
                    continue
            if self._context_press and event.type == pygame.MOUSEMOTION:
                press = self._context_press
                if not press["moved"] and press["target"] is None:
                    self._context_buffer.append(event)
                    dx = event.pos[0] - press["position"][0]
                    dy = event.pos[1] - press["position"][1]
                    if max(abs(dx), abs(dy)) >= 4:
                        press["moved"] = True
                        controls.focused = self.focused
                        output.extend(self._map_pointer_event(item)
                                      for item in self._context_buffer)
                        self._context_buffer.clear()
                        continue
                    continue
                elif not press["moved"]:
                    dx = event.pos[0] - press["position"][0]
                    dy = event.pos[1] - press["position"][1]
                    if max(abs(dx), abs(dy)) >= 4:
                        self._context_press = None
                        controls.focused = self.focused
                    continue
            if (self._context_press and event.type == pygame.MOUSEBUTTONUP and
                    event.button == MOUSE_BUTTONS["secondary"]):
                press = self._context_press
                self._context_press = None
                self._context_buffer.clear()
                if not press["moved"]:
                    self._open_context_menu(event.pos, press["target"], scene,
                                            controls)
                    continue
            if event.type == pygame.KEYDOWN and self._key_event(
                    event, scene, models, quest_state, maze_state, controls, output):
                continue
            if self.confirm_home_open:
                if (event.type == pygame.MOUSEBUTTONDOWN and
                        event.button == MOUSE_BUTTONS["primary"]):
                    action = self._action_at(event.pos)
                    if action in (("home_confirmation", "cancel"),
                                  ("home_confirmation", "leave")):
                        self._perform(action, scene, models, quest_state,
                                      maze_state, output)
                    continue
                if event.type == pygame.MOUSEMOTION:
                    self.hover = self._action_at(event.pos)
                    continue
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
                                  pygame.KEYUP, pygame.TEXTINPUT):
                    continue
            if self.context_menu_open:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    action = self._action_at(event.pos)
                    if (event.button == MOUSE_BUTTONS["primary"] and
                            action in self.context_menu_actions):
                        self._perform(action, scene, models, quest_state,
                                      maze_state, output)
                        self._close_context_menu(controls)
                    elif (self.context_menu_rect is None or
                          not self.context_menu_rect.collidepoint(event.pos)):
                        self._close_context_menu(controls)
                    continue
                if event.type == pygame.MOUSEMOTION:
                    self.hover = self._action_at(event.pos)
                    self._set_cursor("hand" if self.hover in self.context_menu_actions
                                      else "arrow")
                    continue
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
                                  pygame.KEYUP, pygame.TEXTINPUT):
                    continue
            if self.render_mode_open:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    action = self._action_at(event.pos)
                    if event.button != MOUSE_BUTTONS["primary"]:
                        continue
                    if action and action[0] == "render_mode_option":
                        self._perform(action, scene, models, quest_state,
                                      maze_state, output)
                        self.render_mode_open = False
                        self.render_mode_menu_rect = None
                        controls.focused = self.focused
                    elif (self.render_mode_menu_rect is None or
                          not self.render_mode_menu_rect.collidepoint(event.pos)):
                        self.render_mode_open = False
                        self.render_mode_menu_rect = None
                        controls.focused = self.focused
                    continue
                if event.type == pygame.MOUSEMOTION:
                    self.hover = self._action_at(event.pos)
                    self._set_cursor("hand" if self.hover and
                                      self.hover[0] == "render_mode_option"
                                      else "arrow")
                    continue
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
                                  pygame.KEYUP, pygame.TEXTINPUT):
                    continue
            if self.preferences_open:
                if event.type == pygame.KEYDOWN and event.key == GLOBAL_KEYS["cancel"]:
                    self.preferences_open = False
                    self.preferences_rect = None
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTONS["primary"]:
                    action = self._action_at(event.pos)
                    if action and action[0] == "preference":
                        self._perform(action, scene, models, quest_state,
                                      maze_state, output)
                    elif self.preferences_rect and not self.preferences_rect.collidepoint(event.pos):
                        self.preferences_open = False
                        self.preferences_rect = None
                        controls.focused = self.focused
                    controls.cancel_drag()
                    continue
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION,
                                  pygame.MOUSEWHEEL, pygame.KEYUP, pygame.TEXTINPUT):
                    if event.type == pygame.MOUSEMOTION:
                        self.hover = self._action_at(event.pos)
                        self._set_cursor(self._cursor_for_position(event.pos, controls))
                    continue
            if self.file_menu_open:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTONS["primary"]:
                    action = self._action_at(event.pos)
                    if action and action[0] == "file_menu":
                        if action[1] == "open":
                            self.open_file_requested = True
                        elif action[1] == "recent":
                            self.requested_path = action[2]
                        elif action[1] == "export":
                            output.append(pygame.event.Event(pygame.KEYDOWN,
                                                             key=EDITOR_KEYS["screenshot"]))
                        elif action[1] == "preferences":
                            self.preferences_open = True
                            self.preferences_rect = None
                            controls.focused = False
                        elif action[1] == "quit":
                            output.append(pygame.event.Event(pygame.QUIT))
                        self.file_menu_open = False
                        self.file_menu_rect = None
                        controls.focused = self.focused and not self._modal_open()
                    elif self.file_menu_rect and not self.file_menu_rect.collidepoint(event.pos):
                        self.file_menu_open = False
                        self.file_menu_rect = None
                        controls.focused = self.focused
                    continue
                if event.type == pygame.KEYDOWN and event.key == GLOBAL_KEYS["cancel"]:
                    self.file_menu_open = False
                    self.file_menu_rect = None
                    controls.focused = self.focused
                    continue
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION,
                                  pygame.MOUSEWHEEL, pygame.KEYUP, pygame.TEXTINPUT):
                    if event.type == pygame.MOUSEMOTION:
                        self.hover = self._action_at(event.pos)
                    continue
            if self.help_open:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    action = (self._action_at(event.pos)
                              if event.button == MOUSE_BUTTONS["primary"] else None)
                    if action == ("help", "getting_started"):
                        self.help_open = False
                        self.help_rect = None
                        self.welcome_open = True
                        controls.focused = False
                        continue
                    if action == ("help", "about"):
                        self.help_open = False
                        self.help_rect = None
                        self.about_open = True
                        self.about_rect = None
                        controls.focused = False
                        continue
                    if (event.button == MOUSE_BUTTONS["primary"] and self.help_rect is not None and
                            not self.help_rect.collidepoint(event.pos)):
                        self.help_open = False
                        self.help_rect = None
                        self.hover = None
                        controls.focused = self.focused
                        self._set_cursor("arrow")
                    controls.cancel_drag()
                    continue
            if self.about_open:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTONS["primary"]:
                    action = self._action_at(event.pos)
                    if action == ("about", "shortcuts"):
                        self.about_open = False
                        self.about_rect = None
                        self.help_open = True
                        controls.focused = False
                    elif self.about_rect and not self.about_rect.collidepoint(event.pos):
                        self.about_open = False
                        self.about_rect = None
                        controls.focused = self.focused
                    continue
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION,
                                  pygame.MOUSEWHEEL, pygame.KEYUP, pygame.TEXTINPUT):
                    if event.type == pygame.MOUSEMOTION:
                        self.hover = self._action_at(event.pos)
                    continue
            if self.welcome_open:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTONS["primary"]:
                    action = self._action_at(event.pos)
                    if action and action[0] == "welcome":
                        self._perform(action, scene, models, quest_state,
                                      maze_state, output)
                        controls.focused = self.focused
                    elif self.welcome_rect and not self.welcome_rect.collidepoint(event.pos):
                        self.welcome_open = False
                        appearance.mark_welcome_seen()
                        controls.focused = self.focused
                    continue
                if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION,
                                  pygame.MOUSEWHEEL, pygame.KEYUP, pygame.TEXTINPUT):
                    continue
                if event.type == pygame.MOUSEBUTTONUP:
                    self.pressed = None
                    continue
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEWHEEL,
                                  pygame.KEYUP, pygame.TEXTINPUT):
                    if event.type == pygame.MOUSEMOTION:
                        self.hover = None
                        self._set_cursor("arrow")
                    continue
            if event.type == pygame.MOUSEWHEEL:
                position = getattr(event, "pos", pygame.mouse.get_pos())
                if self.active_destination == "Explore" and self.scene_panel.list_rect.collidepoint(position):
                    self.scene_panel.scroll_by(event.y, models)
                    continue
                if not self.view_rect.collidepoint(position):
                    continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_BUTTONS["primary"]:
                action = self._action_at(event.pos)
                if (action is None and self.active_destination == "Explore" and
                        self.view_rect.collidepoint(event.pos) and
                        getattr(event, "clicks", 1) >= 2):
                    scene.reset()
                    controls.cancel_drag()
                    continue
                if action is not None:
                    if not self.focused:
                        continue
                    controls.cancel_drag()
                    self.pressed = action
                    if self.focused_field is not None and action != self.focused_field:
                        self._commit_field(scene)
                    self.focused_action = action
                    kind = action[0]
                    self._set_cursor(self._cursor_for_action(action, controls))
                    if kind == "splitter":
                        self._play_ui_click()
                        self.drag_splitter = action[1]
                    elif kind == "slider":
                        self._play_ui_click()
                        if getattr(event, "clicks", 1) >= 2:
                            self._reset_slider(action, scene)
                            self.drag_action = None
                            self._slider_last_x = None
                        else:
                            self.drag_action = action
                            self._slider_last_x = event.pos[0]
                            self._apply_slider(action, event.pos, scene,
                                               getattr(event, "mod", 0))
                    elif kind == "audio_volume":
                        self._play_ui_click()
                        self.drag_action = action
                        self._apply_audio_volume(event.pos, persist=False)
                    elif kind == "field":
                        self._play_ui_click()
                        self._focus_field(action, scene)
                    else:
                        self._perform(action, scene, models, quest_state,
                                      maze_state, output)
                        if self._modal_open():
                            controls.focused = False
                    continue
                if self._is_outside_view(event.pos):
                    controls.cancel_drag()
                    continue
            if event.type == pygame.MOUSEBUTTONUP:
                if self.drag_action and self.drag_action[0] == "audio_volume":
                    self._save_audio_preferences()
                self.drag_action = None
                self.drag_splitter = None
                self._slider_last_x = None
                self.pressed = None
                if event.button == controls.drag_button:
                    controls.cancel_drag()
                self._set_cursor(self._cursor_for_position(event.pos, controls))
            if event.type == pygame.MOUSEMOTION:
                self.hover = self._action_at(event.pos)
                self._set_cursor(self._cursor_for_position(event.pos, controls))
                if self.drag_action is not None:
                    if self.drag_action[0] == "audio_volume":
                        self._apply_audio_volume(event.pos, persist=False)
                    else:
                        modifiers = _event_modifiers(event)
                        dx = (event.pos[0] - self._slider_last_x
                              if self._slider_last_x is not None else 0)
                        if modifiers & pygame.KMOD_SHIFT:
                            self._adjust_slider_relative(self.drag_action, dx,
                                                         scene, modifiers)
                        else:
                            self._apply_slider(self.drag_action, event.pos,
                                               scene, modifiers)
                        self._slider_last_x = event.pos[0]
                    continue
                if self.drag_splitter is not None:
                    self._resize_splitter(self.drag_splitter, event.pos)
                    controls.cancel_drag()
                    continue
            output.append(self._map_pointer_event(event))
        return output

    def _key_event(self, event, scene, models, quest_state, maze_state,
                   controls, output):
        if not self.focused:
            return True
        unicode = getattr(event, "unicode", "")
        if event.key == GLOBAL_KEYS["help"][0] or unicode == "?":
            if self.help_open:
                self.help_open = False
                self.help_rect = None
                controls.focused = self.focused
            else:
                if self.context_menu_open:
                    self._close_context_menu(controls)
                if self.welcome_open:
                    appearance.mark_welcome_seen()
                self.about_open = False
                self.about_rect = None
                self.preferences_open = False
                self.preferences_rect = None
                self.file_menu_open = False
                self.file_menu_rect = None
                self.render_mode_open = False
                self.render_mode_menu_rect = None
                self.welcome_open = False
                self.welcome_rect = None
                self.help_open = True
                self.help_rect = None
                controls.cancel_drag()
                controls.focused = False
            self.focused_field = None
            self._set_cursor("arrow")
            return True
        if self.about_open:
            if event.key == GLOBAL_KEYS["cancel"]:
                self.about_open = False
                self.about_rect = None
                controls.focused = self.focused
            return True
        if self.context_menu_open:
            if event.key == GLOBAL_KEYS["cancel"]:
                self._close_context_menu(controls)
            elif event.key in (GLOBAL_KEYS["step_up"], GLOBAL_KEYS["step_down"]):
                direction = -1 if event.key == GLOBAL_KEYS["step_up"] else 1
                self.context_menu_index = (
                    self.context_menu_index + direction) % max(
                        1, len(self.context_menu_actions))
            elif event.key in GLOBAL_KEYS["activate"] and self.context_menu_actions:
                action = self.context_menu_actions[self.context_menu_index]
                self._perform(action, scene, models, quest_state,
                              maze_state, output)
                self._close_context_menu(controls)
            return True
        if self.render_mode_open:
            if event.key == GLOBAL_KEYS["cancel"]:
                self.render_mode_open = False
                self.render_mode_menu_rect = None
                controls.focused = self.focused
            elif event.key in (GLOBAL_KEYS["step_up"], GLOBAL_KEYS["step_down"]):
                direction = -1 if event.key == GLOBAL_KEYS["step_up"] else 1
                self.render_mode_index = (
                    self.render_mode_index + direction) % len(RENDER_MODES)
            elif event.key in GLOBAL_KEYS["activate"]:
                self._perform(("render_mode_option",
                               RENDER_MODES[self.render_mode_index]),
                              scene, models, quest_state, maze_state, output)
                self.render_mode_open = False
                self.render_mode_menu_rect = None
                controls.focused = self.focused
            return True
        if (self._context_press and event.key == GLOBAL_KEYS["cancel"]):
            self._context_press = None
            self._context_buffer.clear()
            controls.focused = self.focused
            return True
        modifiers = _event_modifiers(event)
        primary = has_primary_modifier(modifiers)
        if primary and modifiers & pygame.KMOD_ALT and event.key in (
                pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            index = event.key - pygame.K_1
            self._set_destination(_TAB_ORDER[index])
            controls.cancel_drag()
            return True
        if (primary and modifiers & pygame.KMOD_SHIFT and
                event.key == GLOBAL_KEYS["return_home"]):
            self._request_home(scene, models, quest_state, maze_state, output)
            controls.cancel_drag()
            return True
        if primary and event.key == GLOBAL_KEYS["preferences"]:
            self.preferences_open = not self.preferences_open
            self.preferences_rect = None if not self.preferences_open else self.preferences_rect
            if self.preferences_open:
                self.about_open = False
                self.about_rect = None
                self.help_open = False
                self.help_rect = None
                self.file_menu_open = False
                self.file_menu_rect = None
                self.render_mode_open = False
                self.render_mode_menu_rect = None
                self.welcome_open = False
                self.welcome_rect = None
            controls.cancel_drag()
            controls.focused = self.focused and not self._modal_open()
            self._set_cursor("arrow")
            return True
        if primary and event.key == GLOBAL_KEYS["open_file"]:
            self.help_open = False
            self.help_rect = None
            self.about_open = False
            self.about_rect = None
            self.preferences_open = False
            self.preferences_rect = None
            self.file_menu_open = False
            self.file_menu_rect = None
            self.render_mode_open = False
            self.render_mode_menu_rect = None
            self.welcome_open = False
            self.welcome_rect = None
            self.open_file_requested = True
            controls.cancel_drag()
            controls.focused = self.focused
            return True
        if primary and event.key == GLOBAL_KEYS["export_screenshot"]:
            output.append(pygame.event.Event(pygame.KEYDOWN,
                                             key=EDITOR_KEYS["screenshot"]))
            return True
        if (primary and event.key == GLOBAL_KEYS["quit"] or
                event.key == GLOBAL_KEYS["quit_alt"] and modifiers & pygame.KMOD_ALT):
            output.append(pygame.event.Event(pygame.QUIT))
            return True
        if event.key == GLOBAL_KEYS["fullscreen"]:
            self.fullscreen_requested = not self.fullscreen_requested
            controls.cancel_drag()
            return True
        if self.help_open:
            if event.key == GLOBAL_KEYS["cancel"]:
                self.help_open = False
                self.help_rect = None
                controls.focused = self.focused
                self._set_cursor("arrow")
            return True
        if self.welcome_open:
            if event.key == GLOBAL_KEYS["cancel"]:
                self.welcome_open = False
                self.welcome_rect = None
                controls.focused = self.focused
                appearance.mark_welcome_seen()
            return True
        if self.preferences_open:
            if event.key == GLOBAL_KEYS["cancel"]:
                self.preferences_open = False
                self.preferences_rect = None
                controls.focused = self.focused
                self._set_cursor("arrow")
            return True
        if self.file_menu_open and event.key == GLOBAL_KEYS["cancel"]:
            self.file_menu_open = False
            self.file_menu_rect = None
            controls.focused = self.focused
            return True
        if self.confirm_home_open and event.key == GLOBAL_KEYS["cancel"]:
            self.confirm_home_open = False
            self.confirm_home_rect = None
            controls.focused = self.focused
            return True
        if self.active_destination == "Landing":
            if event.key == GLOBAL_KEYS["cancel"]:
                return True
            if event.key == GLOBAL_KEYS["next_destination"]:
                actions = tuple(self._landing_action_order())
                direction = -1 if modifiers & pygame.KMOD_SHIFT else 1
                try:
                    index = actions.index(self.landing_focus)
                except ValueError:
                    index = -1 if direction > 0 else 0
                self.landing_focus = actions[(index + direction) % len(actions)]
                self.focused_action = self.landing_focus
                return True
            if event.key in (*GLOBAL_KEYS["activate"], pygame.K_SPACE):
                action = self.landing_focus or ("landing", "explore")
                self._perform(action, scene, models, quest_state,
                              maze_state, output)
                if self._modal_open():
                    controls.focused = False
                return True
            return True
        if self.focused_field is not None:
            if event.key == GLOBAL_KEYS["next_destination"]:
                previous = self.focused_field
                self._commit_field(scene)
                self._cycle_field(-1 if modifiers & pygame.KMOD_SHIFT else 1,
                                  scene, after=previous)
            elif event.key == GLOBAL_KEYS["cancel"]:
                self.focused_field = None
                self.field_buffer = ""
            elif event.key in GLOBAL_KEYS["activate"]:
                self._commit_field(scene)
            elif event.key == GLOBAL_KEYS["field_backspace"]:
                if self.field_replace:
                    self.field_buffer = ""
                    self.field_replace = False
                else:
                    self.field_buffer = self.field_buffer[:-1]
            elif primary and event.key == GLOBAL_KEYS["select_all"]:
                self.field_buffer = ""
                self.field_replace = False
            elif event.key in (GLOBAL_KEYS["step_up"], GLOBAL_KEYS["step_down"]):
                self._step_field(scene, 1 if event.key == GLOBAL_KEYS["step_up"] else -1)
            elif unicode and unicode in "0123456789.-":
                if self.field_replace:
                    self.field_buffer = ""
                    self.field_replace = False
                if (unicode == "-" and not self.field_buffer.startswith("-") or
                        unicode not in ("-", ".") or
                        unicode == "." and "." not in self.field_buffer):
                    self.field_buffer += unicode
            return True
        if event.key == GLOBAL_KEYS["focus_next"]:
            self._cycle_focus()
            return True
        if (event.key in GLOBAL_KEYS["reset_view"] and
                self.active_destination == "Explore"):
            scene.reset()
            controls.cancel_drag()
            return True
        if (self.active_destination == "Explore" and
                (event.key == GLOBAL_KEYS["projection_toggle"][0] or
                 primary and event.key == GLOBAL_KEYS["projection_toggle"][1])):
            scene.projection = ("Orthographic" if scene.projection == "Perspective"
                                else "Perspective")
            return True
        view = (view_shortcut(event.key, modifiers)
                if self.active_destination == "Explore" else None)
        if view is not None:
            self._set_standard_view(scene, *view)
            controls.cancel_drag()
            return True
        if event.key in GLOBAL_KEYS["activate"] and self.focused_action:
            action = self.focused_action
            if action[0] == "field":
                self._focus_field(action, scene)
            elif action[0] != "slider":
                self._perform(action, scene, models, quest_state, maze_state, output)
                if self._modal_open():
                    controls.focused = False
            return True
        if (event.key in (GLOBAL_KEYS["adjust_left"], GLOBAL_KEYS["adjust_right"]) and
                self.focused_action and self.focused_action[0] in
                ("slider", "audio_volume")):
            direction = -1 if event.key == GLOBAL_KEYS["adjust_left"] else 1
            if self.focused_action[0] == "audio_volume":
                value = self.audio_volume + direction * 0.02
                self._set_audio_volume(value, persist=True)
            else:
                self._step_slider(self.focused_action, direction, scene)
            self._play_ui_click()
            return True
        if event.key == GLOBAL_KEYS["next_destination"] and self.focused_field:
            previous = self.focused_field
            self._commit_field(scene)
            self._cycle_field(-1 if modifiers & pygame.KMOD_SHIFT else 1,
                              scene, after=previous)
            return True
        if event.key == GLOBAL_KEYS["next_destination"]:
            index = _TAB_ORDER.index(self.active_destination)
            destination = _TAB_ORDER[(index + 1) % len(_TAB_ORDER)]
            self._set_destination(destination)
            controls.cancel_drag()
            return True
        if not self.focused:
            return True
        if self.active_destination == "Explore" and event.key == EDITOR_KEYS["render_mode"]:
            self._cycle_render_mode()
            controls.cancel_drag()
            return True
        if (event.key == EDITOR_KEYS["play_pause"] and
                self.active_destination == "Explore" and scene.shape == "Signal wave"):
            self.wave_playing = not self.wave_playing
            return True
        if self.active_destination == "Maze" and maze_state is not None:
            if event.key == MAZE_KEYS["projection"]:
                maze_state.toggle_projection()
                return True
            if event.key == MAZE_KEYS["pause"]:
                if not maze_state.won:
                    maze_state.toggle_pause()
                return True
            if event.key == MAZE_KEYS["scan"]:
                maze_state.scan()
                return True
            if event.key == MAZE_KEYS["new_run"]:
                maze_state.new_maze()
                return True
            if event.key in MAZE_KEYS["continue"] and maze_state.won:
                if not maze_state.campaign_complete:
                    maze_state.advance_level()
                return True
        return False

    def _perform(self, action, scene, models, quest_state, maze_state, output):
        self._play_ui_click()
        kind = action[0]
        if kind == "destination":
            self._set_destination(action[1])
        elif kind == "home":
            self._request_home(scene, models, quest_state, maze_state, output)
        elif kind == "home_confirmation":
            self.confirm_home_open = False
            self.confirm_home_rect = None
            if action[1] == "leave":
                self._set_destination("Landing")
            if self._controls is not None:
                self._controls.focused = self.focused
        elif kind == "landing":
            if action[1] == "explore":
                self._set_destination("Explore")
            elif action[1] == "open_obj":
                self.open_file_requested = True
            elif action[1] == "shortcuts":
                self.help_open = True
                self.help_rect = None
            elif action[1] == "about":
                self.about_open = True
                self.about_rect = None
        elif kind == "theme":
            self.theme_mode = appearance.toggle()
        elif kind == "music_toggle":
            self.music_muted = (self.audio.toggle_music() if self.audio is not None
                                else not self.music_muted)
        elif kind == "help":
            if len(action) > 1 and action[1] == "getting_started":
                self.help_open = False
                self.welcome_open = True
            elif len(action) > 1 and action[1] == "about":
                self.help_open = False
                self.about_open = True
            else:
                self.help_open = True
        elif kind == "welcome":
            self.welcome_open = False
            appearance.mark_welcome_seen()
            if action[1] == "explore":
                self._set_destination("Explore")
        elif kind == "preference":
            appearance.set_navigation_preset(action[1])
        elif kind == "screenshot":
            output.append(pygame.event.Event(pygame.KEYDOWN,
                                             key=EDITOR_KEYS["screenshot"]))
        elif kind == "load_sample":
            output.append(pygame.event.Event(pygame.KEYDOWN,
                                             key=EDITOR_KEYS["open_sample"]))
        elif kind == "toolbar_open_obj":
            self.file_menu_open = True
        elif kind == "file_menu":
            if action[1] == "open":
                self.open_file_requested = True
            elif action[1] == "home":
                self._request_home(scene, models, quest_state, maze_state, output)
            elif action[1] == "recent":
                self.requested_path = action[2]
            elif action[1] == "export":
                output.append(pygame.event.Event(pygame.KEYDOWN,
                                                 key=EDITOR_KEYS["screenshot"]))
            elif action[1] == "preferences":
                self.preferences_open = True
                self.preferences_rect = None
            elif action[1] == "quit":
                output.append(pygame.event.Event(pygame.QUIT))
        elif kind == "projection":
            if action[1] == "toggle":
                scene.projection = ("Orthographic" if scene.projection == "Perspective"
                                    else "Perspective")
            else:
                scene.projection = action[1]
        elif kind == "render_menu":
            self._cycle_render_mode()
        elif kind == "render_mode_select":
            self.render_mode_open = not self.render_mode_open
            self.render_mode_menu_rect = None
            self.render_mode_index = RENDER_MODES.index(self.render_mode)
        elif kind == "render_mode_option":
            self._set_render_mode(action[1])
        elif kind == "projection_panel":
            scene.projection = action[1]
        elif kind == "maze_projection_toolbar" and maze_state is not None:
            maze_state.toggle_projection()
        elif kind == "reset":
            scene.reset()
            self.focused_field = None
        elif kind == "view_axis":
            self._set_standard_view(scene, action[1], action[2])
        elif kind == "axes":
            scene.axes_visible = not scene.axes_visible
        elif kind == "section":
            name = action[1]
            if name == "objects":
                self.scene_panel.objects_open = not self.scene_panel.objects_open
            elif name in self.open_sections:
                self.open_sections.remove(name)
            else:
                self.open_sections.add(name)
        elif kind == "dock_collapse":
            if action[1] == "left":
                self.left_collapsed = True
            else:
                self.right_collapsed = True
        elif kind == "dock":
            if action[1] == "left":
                self.left_collapsed = False
            else:
                self.right_collapsed = False
        elif kind == "shape":
            if action[1] == "OBJ house":
                output.append(pygame.event.Event(pygame.KEYDOWN,
                                                 key=EDITOR_KEYS["open_sample"]))
            else:
                scene.select(action[1])
                if action[1] == "Signal wave":
                    self.wave_playing = True
        elif kind == "shooter_launch":
            self.shooter_requested = True
        elif kind == "maze_action" and maze_state is not None:
            maze_state.apply_action(action[1])
        elif kind == "quest_rotate":
            delta = [0.0, 0.0, 0.0]
            delta[action[1]] = action[2] * radians(10)
            scene.rotate(*delta)
        elif kind == "quest_depth":
            scene.move(dz=action[1] * 0.35)
        elif kind == "quest_choice" and quest_state is not None:
            quest_state.select_answer(action[1])
        elif kind == "quest_check" and quest_state is not None:
            quest_state.check_answer()
        elif kind == "quest_next" and quest_state is not None:
            quest_state.advance()
        elif kind == "quest_back":
            self._set_destination("Explore")

    def _focus_field(self, action, scene):
        self.focused_field = action
        self.focused_action = action
        self.field_replace = True
        kind, field, axis = action
        if field == "rotation":
            self.field_buffer = f"{degrees(scene.angles[axis]) % 360:.1f}"
        elif field == "position":
            self.field_buffer = f"{scene.position[axis]:.2f}"
        else:
            self.field_buffer = f"{scene.scale:.2f}"

    def _commit_field(self, scene):
        if self.focused_field is None:
            return
        try:
            value = float(self.field_buffer)
        except ValueError:
            self.panel.notify("Enter a valid number. The previous value was kept.")
            self.focused_field = None
            self.field_buffer = ""
            self.field_replace = False
            return
        _, field, axis = self.focused_field
        if field == "rotation":
            self._set_angle(scene, axis, value)
        elif field == "position":
            position = list(scene.position)
            position[axis] = value
            scene.move(*(position[i] - scene.position[i] for i in range(3)))
        elif field == "scale":
            scene.resize(value - scene.scale)
        self.focused_field = None
        self.field_buffer = ""
        self.field_replace = False

    def _cycle_field(self, direction, scene, *, after=None):
        fields = [action for action in self.buttons if action[0] == "field"]
        if not fields:
            self.focused_field = None
            return
        try:
            index = fields.index(after if after is not None else self.focused_field)
        except ValueError:
            index = -1 if direction > 0 else 0
        self._focus_field(fields[(index + direction) % len(fields)], scene)

    def _step_field(self, scene, direction):
        if self.focused_field is None:
            return
        _, field, axis = self.focused_field
        try:
            value = float(self.field_buffer)
        except ValueError:
            self._focus_field(self.focused_field, scene)
            value = float(self.field_buffer)
        step = (1.0 if field == "rotation" else
                0.1 if field == "position" and axis == 2 else 0.01)
        value += direction * step
        self.field_buffer = f"{value:.1f}" if field == "rotation" else f"{value:.2f}"
        self.field_replace = False

    @staticmethod
    def _set_standard_view(scene, view, sign):
        view = {"X": "right", "Y": "top", "Z": "front"}.get(view, view)
        if view == "front":
            target = (0.0, 0.0 if sign > 0 else pi, 0.0)
        elif view == "right":
            target = (0.0, (pi / 2) * sign, 0.0)
        else:
            target = ((pi / 2) * sign, 0.0, 0.0)
        # Standard views have exact named orientations; assigning the canonical
        # values also avoids tiny negative deltas wrapping to a visible 2π value.
        scene.angles = tuple(value % (2 * pi) for value in target)

    def _apply_slider(self, action, position, scene, modifiers=0):
        rect = self.buttons.get(action)
        if rect is None:
            return
        ratio = max(0.0, min(1.0, (position[0] - rect.x) / max(1, rect.width)))
        _, field, axis = action
        if field == "rotation":
            low, high = 0.0, 360.0
        elif field == "position":
            low, high = ((config.MIN_DEPTH, config.MAX_DEPTH) if axis == 2 else
                         (-config.POSITION_LIMIT, config.POSITION_LIMIT))
        else:
            low, high = config.MIN_SCALE, config.MAX_SCALE
        value = low + ratio * (high - low)
        if has_primary_modifier(modifiers):
            value = self._snap_slider_value(field, axis, value)
        if field == "rotation":
            self._set_angle(scene, axis, value)
        elif field == "position":
            position_values = list(scene.position)
            position_values[axis] = value
            scene.move(*(position_values[i] - scene.position[i] for i in range(3)))
        else:
            scene.resize(value - scene.scale)

    def _reset_slider(self, action, scene):
        _, field, axis = action
        if field == "rotation":
            self._set_angle(scene, axis, degrees(config.DEFAULT_ANGLES[axis]))
        elif field == "position":
            defaults = (0.0, 0.0, config.DEFAULT_DEPTH)
            position = list(scene.position)
            position[axis] = defaults[axis]
            scene.move(*(position[index] - scene.position[index]
                         for index in range(3)))
        else:
            scene.resize(1.0 - scene.scale)

    @staticmethod
    def _snap_slider_value(field, axis, value):
        step = (5.0 if field == "rotation" else
                0.1 if field == "position" and axis == 2 else
                0.05)
        return round(value / step) * step

    def _adjust_slider_relative(self, action, dx, scene, modifiers):
        rect = self.buttons.get(action)
        if rect is None:
            return
        _, field, axis = action
        if field == "rotation":
            value, low, high = (degrees(scene.angles[axis]) % 360, 0.0, 360.0)
        elif field == "position":
            value = scene.position[axis]
            low, high = ((config.MIN_DEPTH, config.MAX_DEPTH) if axis == 2 else
                         (-config.POSITION_LIMIT, config.POSITION_LIMIT))
        else:
            value, low, high = scene.scale, config.MIN_SCALE, config.MAX_SCALE
        value += dx * (high - low) / max(1, rect.width) * 0.1
        value = max(low, min(high, value))
        if has_primary_modifier(modifiers):
            value = self._snap_slider_value(field, axis, value)
        if field == "rotation":
            self._set_angle(scene, axis, value)
        elif field == "position":
            position = list(scene.position)
            position[axis] = value
            scene.move(*(position[i] - scene.position[i] for i in range(3)))
        else:
            scene.resize(value - scene.scale)

    def _apply_audio_volume(self, position, *, persist):
        rect = self.buttons.get(("audio_volume",))
        if rect is None:
            return
        ratio = max(0.0, min(1.0, (position[0] - rect.x) / max(1, rect.width)))
        self._set_audio_volume(ratio, persist=persist)

    def _set_audio_volume(self, value, *, persist):
        self.audio_volume = max(0.0, min(1.0, float(value)))
        if self.audio is not None:
            self.audio.set_volume(self.audio_volume, persist=persist)

    def _step_slider(self, action, direction, scene):
        _, field, axis = action
        if field == "rotation":
            delta = [0.0, 0.0, 0.0]
            delta[axis] = radians(5 * direction)
            scene.rotate(*delta)
        elif field == "position":
            delta = [0.0, 0.0, 0.0]
            delta[axis] = direction * (0.05 if axis < 2 else 0.1)
            scene.move(*delta)
        else:
            scene.resize(direction * 0.02)

    def _cycle_focus(self):
        actions = [action for action in self.buttons if action[0] != "splitter"]
        if not actions:
            self.focused_action = None
            return
        try:
            index = actions.index(self.focused_action)
        except ValueError:
            index = -1
        self.focused_action = actions[(index + 1) % len(actions)]

    @staticmethod
    def _set_angle(scene, axis, value):
        angles = list(scene.angles)
        target = radians(float(value) % 360)
        change = (target - angles[axis] + pi) % (2 * pi) - pi
        delta = [0.0, 0.0, 0.0]
        delta[axis] = change
        scene.rotate(*delta)

    def _resize_splitter(self, side, position):
        metrics = ui_theme.METRICS
        if side == "left":
            self.left_width = max(metrics["dock_min"],
                                  min(metrics["dock_max"], position[0]))
        else:
            self.right_width = max(metrics["dock_min"],
                                   min(metrics["dock_max"],
                                       self.canvas_size[0] - position[0]))

    def _landing_action_order(self):
        return (("landing", "explore"), ("landing", "open_obj"),
                ("landing", "shortcuts"), ("landing", "about"))

    def _request_home(self, scene, models, quest_state, maze_state, output):
        """Return home, confirming first if a Maze campaign is still active."""
        if self.active_destination == "Landing":
            return
        self._close_navigation_overlays()
        if self.active_destination == "Maze" and maze_state is not None and not maze_state.won:
            self.confirm_home_open = True
            self.confirm_home_rect = None
            if self._controls is not None:
                self._controls.cancel_drag()
                self._controls.focused = False
            return
        self._set_destination("Landing")

    def _close_navigation_overlays(self):
        for name in ("help_open", "about_open", "preferences_open",
                     "file_menu_open", "context_menu_open",
                     "render_mode_open", "welcome_open", "confirm_home_open"):
            setattr(self, name, False)
        for name in ("help_rect", "about_rect", "preferences_rect",
                     "file_menu_rect", "context_menu_rect",
                     "render_mode_menu_rect", "welcome_rect",
                     "confirm_home_rect"):
            setattr(self, name, None)
        self.context_menu_target = None
        self.context_menu_actions = []
        self._context_press = None
        self._context_buffer.clear()
        self.render_mode_index = 0

    def _remember_page_state(self, destination):
        if destination == "Landing":
            return
        self._page_states[destination] = {
            "left_collapsed": self.left_collapsed,
            "right_collapsed": self.right_collapsed,
            "left_width": self.left_width,
            "right_width": self.right_width,
            "open_sections": set(self.open_sections),
            "scene_scroll": self.scene_panel.scroll,
            "objects_open": self.scene_panel.objects_open,
            "render_mode": self.render_mode,
        }

    def _restore_page_state(self, destination):
        state = self._page_states.get(destination)
        if state is None:
            return
        self.left_collapsed = state["left_collapsed"]
        self.right_collapsed = state["right_collapsed"]
        self.left_width = state["left_width"]
        self.right_width = state["right_width"]
        self.open_sections = set(state["open_sections"])
        self.scene_panel.scroll = state["scene_scroll"]
        self.scene_panel.objects_open = state["objects_open"]
        if destination == "Explore":
            self.render_mode = state["render_mode"]

    def _set_destination(self, destination):
        if destination == self.active_destination:
            return
        previous = self.active_destination
        self._remember_page_state(previous)
        self._close_navigation_overlays()
        self._restore_page_state(destination)
        if destination == "Shooter" and previous != "Shooter":
            self.previous_destination = previous
        elif previous == "Shooter" and destination != "Shooter":
            self.previous_destination = destination
        self.active_destination = destination
        self.shape_menu_open = False
        self.focused_field = None
        self.focused_action = ("landing", "explore") if destination == "Landing" else None
        self.landing_focus = ("landing", "explore")
        self.hover = self.pressed = None
        self.drag_action = self.drag_splitter = None
        self._slider_last_x = None
        self._last_hover = None
        self.animator.clear()
        self.destination_changed = True
        self._transition_elapsed = (0.0 if previous == "Landing" and
                                    destination == "Explore" else None)
        if self._controls is not None:
            self._controls.cancel_drag()
            self._controls.release_held_keys()
            self._controls.focused = self.focused
        self._cursor_kind = None
        self._set_cursor("arrow")
        try:
            pygame.mouse.set_visible(True)
        except pygame.error:
            pass

    def _is_outside_view(self, position):
        return not self.view_rect.collidepoint(position)

    def _action_at(self, position):
        return next((action for action, rect in reversed(tuple(self.buttons.items()))
                     if rect.collidepoint(position)), None)

    def _cursor_for_position(self, position, controls):
        if self.help_open:
            return "arrow"
        if self.drag_splitter is not None or self.drag_action is not None:
            return "size_we"
        if controls.drag is not None:
            return "size_all"
        action = self._action_at(position)
        return self._cursor_for_action(action, controls) if action else "arrow"

    @staticmethod
    def _cursor_for_action(action, controls):
        if action is None:
            return "size_all" if controls.drag is not None else "arrow"
        if action[0] == "field":
            return "ibeam"
        if action[0] in ("slider", "audio_volume", "splitter"):
            return "size_we"
        return "hand"

    def _set_cursor(self, kind):
        if kind == self._cursor_kind:
            return
        cursor_names = {
            "arrow": "SYSTEM_CURSOR_ARROW",
            "hand": "SYSTEM_CURSOR_HAND",
            "ibeam": "SYSTEM_CURSOR_IBEAM",
            "size_we": "SYSTEM_CURSOR_SIZEWE",
            "size_all": "SYSTEM_CURSOR_SIZEALL",
        }
        cursor = getattr(pygame, cursor_names[kind])
        try:
            pygame.mouse.set_cursor(cursor)
        except pygame.error:
            # SDL's dummy driver and some remote displays have no native cursor.
            pass
        self._cursor_kind = kind

    def state(self, action):
        if action == self.pressed:
            return "pressed"
        if action == self.focused_field:
            return "focused"
        if action == self.focused_action:
            return "focused"
        if action == self.hover:
            return "hover"
        if action in self.active:
            return "active"
        return "default"

    def paint_button(self, surface, action, *, mode="dark", state=None,
                     shortcut=None, icon=None, align="center"):
        rect = self.buttons[action]
        state = state or self.state(action)
        if icon:
            self.icon_placements[action] = {
                "button": rect.copy(),
                "icon": icon_button_rect(rect, self.labels[action], icon,
                                         align=align),
                "label": self.labels[action],
                "align": align,
            }
        transition = self.animator.value(action, 1.0 if state != "default" else 0.0,
                                         self._dt)
        return draw_button(surface, rect, self.labels[action], state=state,
                           mode=mode, shortcut=shortcut, icon=icon,
                           align=align, transition=transition)

    def draw(self, target, mesh, scene, models, camera, fps=0, mouse=(0, 0),
             quest_state=None, maze_state=None, dt=None):
        """Draw the live responsive workspace and the current destination."""
        self._dt = max(0.0, float(dt if dt is not None else 1 / config.FPS))
        self._last_scene_shape = scene.shape
        self._last_models = models
        maze_state = maze_state or self.maze_state
        self.maze_state = maze_state
        self.layout(scene, models, quest_state, maze_state, target.get_size(),
                    prime=False)
        colors = ui_theme.palette(self.theme_mode)
        if self.active_destination == "Landing":
            self._draw_landing(target, mouse)
            self._draw_notice(target, colors)
        else:
            target.fill(colors["CANVAS"])
            self._draw_topbar(target, scene, colors)
            self._draw_panels(target, scene, models, quest_state, maze_state, colors)
            self._draw_splitters(target, colors)
            self._draw_view(target, mesh, scene, models, camera,
                            quest_state, maze_state, fps, colors)
            self._last_quest = quest_state
            self._draw_status(target, scene, mesh, fps, colors)
            self._draw_notice(target, colors)
            self._draw_tooltip(target, mouse)
        if self.help_open:
            self.help_rect, footer_actions = draw_overlay(
                target, "Keyboard shortcuts", self._shortcut_rows(),
                mode=self.theme_mode,
                footer_actions=("Getting started", "About RenderX"))
            self.button(("help", "getting_started"), "Getting started",
                        footer_actions["Getting started"])
            self.button(("help", "about"), "About RenderX",
                        footer_actions["About RenderX"])
        else:
            self.help_rect = None
        if self.about_open:
            self.about_rect, back_action = draw_overlay(
                target, "About RenderX",
                (("Application", "RenderX"),
                 ("Engine", "Software-rendered 3D"),
                 ("Built with", "Python · Pygame"),
                 ("Destinations", "Explore + 3 modes")),
                mode=self.theme_mode, footer_action="Back to shortcuts", wide=False,
                hint="Esc closes · F1 opens shortcuts")
            self.button(("about", "shortcuts"), "Back to shortcuts", back_action)
        else:
            self.about_rect = None
        if self.preferences_open:
            self.preferences_rect, choices = draw_preferences(
                target, appearance.navigation_preset(),
                mode=self.theme_mode)
            for value, rect in choices.items():
                action = ("preference", value)
                self.button(action, f"Navigation preset: {value}", rect,
                            active=value == appearance.navigation_preset())
        else:
            self.preferences_rect = None
        if self.file_menu_open:
            self.file_menu_rect, items = draw_file_menu(
                target, appearance.recent_files(), mode=self.theme_mode,
                hovered=self.hover)
            for action, rect in items.items():
                self.button(action, "File menu action", rect)
        else:
            self.file_menu_rect = None
        if self.welcome_open:
            self.welcome_rect, actions = draw_welcome(
                target, appearance.navigation_preset(), mode=self.theme_mode)
            for key, rect in actions.items():
                self.button(("welcome", key), key.replace("_", " ").title(), rect)
        else:
            self.welcome_rect = None
        if self.render_mode_open:
            anchor = self.buttons.get(("render_mode_select",))
            if anchor is not None:
                focused = RENDER_MODES[self.render_mode_index]
                self.render_mode_menu_rect, choices = draw_dropdown_options(
                    target, anchor, RENDER_MODES, self.render_mode,
                    mode=self.theme_mode, focused=focused)
                for value, rect in choices.items():
                    action = ("render_mode_option", value)
                    self.button(action, f"Render mode: {value}", rect,
                                active=value == self.render_mode)
        else:
            self.render_mode_menu_rect = None
        if self.context_menu_open:
            items = self._context_items(scene)
            self.context_menu_actions = [action for action, _ in items]
            focused = (self.context_menu_actions[self.context_menu_index]
                       if self.context_menu_actions else None)
            self.context_menu_rect, rects = draw_context_menu(
                target, self.context_menu_position, items,
                mode=self.theme_mode, hovered=self.hover, focused=focused)
            for (action, label), rect in zip(items, rects.values()):
                self.button(action, label, rect,
                            active=action == focused)
        else:
            self.context_menu_rect = None
        if self.confirm_home_open:
            self.confirm_home_rect, choices = draw_overlay(
                target, "Leave the Maze?",
                (("Current campaign", "Your run will remain available in this session."),),
                mode=self.theme_mode, footer_actions=("Cancel", "Leave"),
                wide=False, hint="Choose Cancel to keep playing.")
            self.button(("home_confirmation", "cancel"), "Cancel",
                        choices["Cancel"])
            self.button(("home_confirmation", "leave"), "Leave",
                        choices["Leave"])
        else:
            self.confirm_home_rect = None
        self._draw_transition(target, colors)

    def _draw_landing(self, target, mouse):
        width, height = target.get_size()
        logo = brand.wordmark(round(width * .62),
                              min(250, round(height * .22),
                                  max(100, round(width * .13))))
        from renderx import __version__
        import sys
        version_text = (f"v{__version__}  ·  Python {sys.version_info.major}."
                        f"{sys.version_info.minor}  ·  Pygame {pygame.version.ver}")
        actions = landing_page.draw_landing(
            target, logo, mode=self.theme_mode, version_text=version_text,
            hover=self.hover, pressed=self.pressed, focused=self.landing_focus)
        labels = {
            ("landing", "explore"): "Open Explorer",
            ("landing", "open_obj"): "Open OBJ…",
            ("landing", "shortcuts"): "Shortcuts",
            ("landing", "about"): "About",
        }
        for action, rect in actions.items():
            self.button(action, labels[action], rect)
        self.hover = self._action_at(mouse) if not self.pressed else self.hover

    def _draw_transition(self, target, colors):
        if self._transition_elapsed is None:
            return
        if self.focused:
            self._transition_elapsed += self._dt
        progress = min(1.0, self._transition_elapsed / .24)
        if progress >= 1.0:
            self._transition_elapsed = None
            return
        if (self._transition_surface is None or
                self._transition_surface_size != target.get_size()):
            self._transition_surface = pygame.Surface(target.get_size(),
                                                       pygame.SRCALPHA)
            self._transition_surface_size = target.get_size()
        eased = 1 - (1 - progress) * (1 - progress)
        alpha = round(255 * (1 - eased))
        self._transition_surface.fill((*colors["CANVAS"], alpha))
        target.blit(self._transition_surface, (0, 0))

    def _draw_topbar(self, target, scene, colors):
        layout = self.app_layout
        pygame.draw.rect(target, colors["SURFACE_1"], layout.topbar)
        pygame.draw.line(target, colors["BORDER"], layout.topbar.bottomleft,
                         layout.topbar.bottomright, ui_theme.METRICS["border"])
        brand_action = ("home",)
        brand_state = self.state(brand_action)
        self.button(brand_action, f"Return to landing · {modifier_name()}+Shift+H",
                    layout.brand)
        if brand_state != "default":
            fill = colors["SURFACE_3"] if brand_state == "pressed" else colors["SURFACE_2"]
            pygame.draw.rect(target, fill, layout.brand,
                             border_radius=ui_theme.METRICS["radius"])
        if brand_state == "focused":
            pygame.draw.rect(target, colors["FOCUS"], layout.brand.inflate(-1, -1), 1,
                             border_radius=ui_theme.METRICS["radius"])
        mark = pygame.Rect(layout.brand.x + ui_theme.SPACE["xs"], 0,
                           ui_theme.METRICS["hit_target"] - ui_theme.SPACE["xs"],
                           ui_theme.METRICS["hit_target"] - ui_theme.SPACE["xs"])
        mark.centery = layout.brand.centery
        icons.draw_icon(target, "brand", mark, colors["ACCENT"])
        self.icon_placements[brand_action] = {
            "button": layout.brand.copy(), "icon": mark.copy(),
            "label": "RenderX", "align": "left",
        }
        fonts.draw_text(target, "RenderX", (mark.right + ui_theme.SPACE["sm"],
                                             layout.brand.centery), "body",
                        colors["TEXT"], anchor="midleft", bold=True)
        for name, rect in layout.navigation.items():
            self.paint_button(target, ("destination", name), mode=self.theme_mode,
                              state=self.state(("destination", name)), align="center")
        if self.active_destination == "Explore":
            self._draw_projection_toolbar(target, layout.projection, scene, colors)
            self.button(("render_menu",), self.render_mode, layout.render_mode)
            self.paint_button(target, ("render_menu",), mode=self.theme_mode,
                              icon="wireframe", align="left")
        elif self.active_destination == "Maze":
            action = ("maze_projection_toolbar",)
            projection = self.maze_state.projection if self.maze_state else "Perspective"
            label = "Persp." if projection == "Perspective" else "Ortho."
            self.button(action, label, layout.projection,
                        active=self.maze_state is not None and
                        self.maze_state.projection == "Orthographic")
            self.paint_button(target, action, mode=self.theme_mode,
                              icon="view", align="center")
        for action, rect, icon_name in (
            (("toolbar_open_obj",), layout.import_obj, "folder"),
            (("screenshot",), layout.screenshot, "camera"),
            (("theme",), layout.theme_toggle,
             "moon" if self.theme_mode == "dark" else "sun"),
            (("help",), layout.help_button, "help"),
            (("music_toggle",), layout.music_toggle,
             "music_off" if self.music_muted else "music_on"),
        ):
            if action == ("toolbar_open_obj",) and self.active_destination != "Explore":
                continue
            self.button(action, self.labels.get(action, action[0].replace("_", " ").title()), rect)
            state = self.state(action)
            if action == ("music_toggle",):
                colors_button = (colors["TEXT_MUTED"] if self.music_muted else
                                 colors["ACCENT"])
            else:
                colors_button = (colors["TEXT_MUTED"] if state == "default" else
                                 colors["ACCENT"])
            pygame.draw.rect(target, colors["SURFACE_1"], rect,
                             border_radius=ui_theme.METRICS["radius"])
            pygame.draw.rect(target, colors["BORDER"], rect,
                             ui_theme.METRICS["border"], border_radius=ui_theme.METRICS["radius"])
            icon_rect = rect.inflate(-ui_theme.SPACE["sm"],
                                     -ui_theme.SPACE["sm"])
            icons.draw_icon(target, icon_name, icon_rect, colors_button)
            self.icon_placements[action] = {
                "button": rect.copy(), "icon": icon_rect.copy(),
                "label": "", "align": "center",
            }

        volume_rect = layout.audio_slider
        slider_hit = draw_slider(
            target, volume_rect, "VOL", self.audio_volume, 0.0, 1.0,
            mode=self.theme_mode, value_text=f"{round(self.audio_volume * 100)}%",
            state=self.state(("audio_volume",)))
        self.button(("audio_volume",), "Master volume", slider_hit)

    def _draw_panels(self, target, scene, models, quest_state, maze_state, colors):
        left, right = self.app_layout.left_dock, self.app_layout.right_dock
        self.scene_panel.draw(target, left, models, scene, self.ui,
                              mode=self.theme_mode,
                              collapsed=self.left_collapsed,
                              destination=self.active_destination,
                              quest=quest_state or QuestState(), maze=maze_state)
        if self.right_collapsed and self.active_destination != "Explore":
            draw_panel(target, right, self.theme_mode)
            action = ("dock", "right")
            rect = pygame.Rect(right.centerx - ui_theme.METRICS["hit_target"] // 2,
                               right.y + ui_theme.SPACE["md"],
                               ui_theme.METRICS["hit_target"],
                               ui_theme.METRICS["hit_target"])
            self.button(action, "Expand inspector", rect)
            self.paint_button(target, action, mode=self.theme_mode,
                              icon="panel-right-open", align="center")
        elif self.active_destination == "Explore":
            draw_inspector_panel(target, right, scene, self.ui, mode=self.theme_mode,
                                 collapsed=self.right_collapsed)
        elif self.active_destination == "Challenges":
            state = quest_state or QuestState()
            mesh = models.get(scene.shape, models["Cube"])
            draw_challenge_panel(target, right, state, scene, models,
                                 Camera(), self.ui,
                                 clipped_edge_count(mesh, scene, Camera()),
                                 mode=self.theme_mode)
        elif self.active_destination == "Maze":
            draw_maze_panel(target, right, maze_state or MazeState(), self.ui,
                            mode=self.theme_mode)
        else:
            draw_shooter_panel(target, right, self.ui, mode=self.theme_mode)

    def _draw_projection_toolbar(self, target, rect, scene, colors):
        labels = ("Persp.", "Ortho.")
        selected = labels[0] if scene.projection == "Perspective" else labels[1]
        items = draw_segmented(target, rect, labels, selected,
                               mode=self.theme_mode)
        for value, label in zip(("Perspective", "Orthographic"), labels):
            action = ("projection", value)
            self.button(action, value, items[label], active=value == scene.projection)
            if action == self.focused_action:
                pygame.draw.rect(target, colors["FOCUS"], items[label], 1,
                                 border_radius=ui_theme.METRICS["radius"])

    def _draw_splitters(self, target, colors):
        draw_splitter(target, self.app_layout.left_splitter,
                      mode=self.theme_mode,
                      hover=self.hover == ("splitter", "left"))
        draw_splitter(target, self.app_layout.right_splitter,
                      mode=self.theme_mode,
                      hover=self.hover == ("splitter", "right"))

    def _draw_view(self, target, mesh, scene, models, camera, quest_state,
                   maze_state, fps, colors):
        frame = self.app_layout.viewport_frame
        viewport = self.view_rect
        pygame.draw.rect(target, colors["SURFACE_2"], frame)
        pygame.draw.rect(target, colors["VIEWPORT"], viewport)
        pygame.draw.rect(target, colors["BORDER"], viewport,
                         ui_theme.METRICS["border"])
        if self.active_destination == "Explore":
            focal_length = max(520, round(viewport.width * .68))
            draw_render_mode(target, mesh, scene, camera, mode=self.render_mode,
                             viewport=viewport, focal_length=focal_length)
            if scene.axes_visible:
                draw_axes(target, camera, scene.projection, fonts.font("hint"),
                          viewport=viewport, focal_length=focal_length)
            self._draw_orientation_gizmo(target, viewport, scene, colors)
        elif self.active_destination == "Challenges":
            state = quest_state or QuestState()
            challenge = state.challenge
            if challenge is None:
                draw_wireframe(target, mesh, scene, camera, viewport=viewport)
            elif challenge.use_comparison:
                draw_comparison_challenge(target, mesh, scene, camera,
                                          viewport, fonts.font("hint"))
            else:
                draw_wireframe(target, mesh, scene, camera, viewport=viewport,
                               focal_length=450)
                if scene.axes_visible:
                    draw_axes(target, camera, scene.projection,
                              fonts.font("hint"), viewport=viewport,
                              focal_length=450)
            if challenge is not None and challenge.kind == "choice_gated":
                draw_near_plane_guide(target, viewport, scene)
            self._draw_orientation_gizmo(target, viewport, scene, colors)
        elif self.active_destination == "Maze":
            maze_state = maze_state or MazeState()
            draw_maze_view(target, maze_state, viewport,
                           fonts.font("section"), fonts.font("hint"))
            self._draw_maze_action_bar(target, self.maze_controls_rect, maze_state)
        else:
            self._draw_shooter_view(target, viewport, models, camera, colors)

    def _draw_maze_action_bar(self, target, viewport, maze_state):
        height = ui_theme.METRICS["control_height"]
        gap = ui_theme.SPACE["xs"]
        width = min(viewport.width - ui_theme.SPACE["xl"],
                    ui_theme.METRICS["row_height"] * 13 + gap * 3)
        button_w = (width - gap * 3) // 4
        x = viewport.centerx - width // 2
        y = viewport.y + (viewport.height - height) // 2
        labels = (("turn-left", "Turn left"), ("forward", "Forward"),
                  ("backward", "Back"), ("turn-right", "Turn right"))
        for index, (name, label) in enumerate(labels):
            rect = pygame.Rect(x + index * (button_w + gap), y, button_w, height)
            action = ("maze_action", name)
            self.button(action, label, rect)
            state = "disabled" if maze_state.paused or maze_state.won else self.state(action)
            self.paint_button(target, action, mode=self.theme_mode, state=state,
                              align="center")

    def _draw_shooter_view(self, target, viewport, models, camera, colors):
        scene = Scene(shape="Torus", angles=(.48, .62, .1),
                      position=(0.0, 0.0, 4.5), scale=1.25,
                      axes_visible=False)
        draw_wireframe(target, models["Torus"], scene, camera,
                       viewport=viewport, line_color=colors["ACCENT"],
                       vertex_color=colors["ACCENT"], show_vertices=False)
        fonts.draw_text(target, "BREAKPOINT", (viewport.x + ui_theme.SPACE["xl"],
                                                viewport.y + ui_theme.SPACE["xl"]),
                        "title", colors["TEXT"], bold=True)
        fonts.draw_text(target, "3D SURVIVAL  ·  WIREFRAME DISPLAY",
                        (viewport.x + ui_theme.SPACE["xl"],
                         viewport.y + ui_theme.SPACE["xl"] + ui_theme.METRICS["title_height"]),
                        "hint", colors["TEXT_MUTED"])
        self._draw_orientation_gizmo(target, viewport, scene, colors)

    def _draw_orientation_gizmo(self, target, viewport, scene, colors):
        size = ui_theme.METRICS["gizmo_size"]
        margin = ui_theme.SPACE["lg"]
        center = (viewport.right - margin - size // 2,
                  viewport.y + margin + size // 2)
        pygame.draw.circle(target, colors["SURFACE_1"], center, size // 2)
        pygame.draw.circle(target, colors["BORDER"], center, size // 2, 1)
        ax, ay, az = scene.angles
        vectors = (
            ("X", cos(ay) * cos(az), sin(az), colors["AXIS_X"]),
            ("Y", -sin(ay), -cos(ax) * .65, colors["AXIS_Y"]),
            ("Z", sin(ay) * cos(az), -cos(az), colors["AXIS_Z"]),
        )
        for label, dx, dy, color in vectors:
            end = (round(center[0] + dx * size * .31),
                   round(center[1] + dy * size * .31))
            pygame.draw.line(target, color, center, end, 2)
            pygame.draw.circle(target, color, end, 3)
            fonts.draw_text(target, label, (end[0], end[1] - ui_theme.SPACE["xs"]),
                            "micro", color, anchor="center", bold=True)
            if self.active_destination == "Explore":
                self.button(("view_axis", label, 1), f"{label} view",
                            pygame.Rect(end[0] - 9, end[1] - 9, 18, 18))
                opposite = (round(center[0] - dx * size * .31),
                            round(center[1] - dy * size * .31))
                self.button(("view_axis", label, -1), f"Opposite {label} view",
                            pygame.Rect(opposite[0] - 9, opposite[1] - 9, 18, 18))
                fonts.draw_text(target, f"−{label}", opposite, "micro",
                                colors["TEXT_DIM"], anchor="center")

    def _draw_status(self, target, scene, mesh, fps, colors):
        if self.active_destination == "Maze" and self.maze_state is not None:
            items = (("STAGE", f"{self.maze_state.level}/3"),
                     ("KEYS", f"{len(self.maze_state.keys_found)}/2"),
                     ("TIME", f"{int(self.maze_state.elapsed)}s"),
                     ("SCORE", f"{self.maze_state.total_score:,}"))
        elif self.active_destination == "Challenges":
            quest = getattr(self, "_last_quest", None)
            items = (("STEP", f"{(quest.current + 1) if quest and not quest.done else 3}/3"),
                     ("OBJ", scene.shape), ("V", len(mesh.vertices)),
                     ("E", len(mesh.edges)), ("F", len(mesh.faces or ())),
                     ("P", scene.projection), ("MODE", "Wireframe"))
        elif self.active_destination == "Shooter":
            preview = self._last_models.get("Torus") if hasattr(self, "_last_models") else None
            if preview is None:
                items = (("PAGE", "Breakpoint"),)
            else:
                items = (("PAGE", "Breakpoint"), ("OBJ", "Torus"),
                         ("V", len(preview.vertices)), ("E", len(preview.edges)),
                         ("F", len(preview.faces or ())), ("P", "Perspective"),
                         ("MODE", "Wireframe"))
        else:
            items = (("OBJ", scene.shape), ("V", len(mesh.vertices)),
                     ("E", len(mesh.edges)), ("F", len(mesh.faces or ())),
                     ("P", "Persp." if scene.projection == "Perspective" else "Ortho."),
                     ("MODE", self.render_mode),
                     ("Z", f"{scene.position[2]:.1f}"),
                     ("S", f"{scene.scale:.2f}"))
        if self.active_destination == "Explore":
            hint = (f"{navigation_status(appearance.navigation_preset())}  ·  "
                    f"{fps:.0f} FPS  ·  F1")
        else:
            hint = f"{fps:.0f} FPS  ·  F1 shortcuts"
        draw_status(target, self.app_layout.statusbar, items, hint,
                    mode=self.theme_mode)

    def _draw_tooltip(self, target, mouse):
        action = self._action_at(mouse)
        if action is None:
            self._last_hover = None
            return
        now = pygame.time.get_ticks()
        if action != self._last_hover:
            self._last_hover = action
            self._hover_started = now
            return
        if now - self._hover_started < ui_theme.METRICS["tooltip_delay_ms"]:
            return
        text = self.labels.get(action, "")
        if action and action[0] == "destination":
            label = layout_module.DESTINATION_LABELS[action[1]]
            index = _TAB_ORDER.index(action[1]) + 1
            text = f"Open {label} · {modifier_name()}+Alt+{index}"
        if text:
            rect = self.buttons[action]
            draw_tooltip(target, (rect.x, rect.bottom + ui_theme.SPACE["xs"]),
                         text, mode=self.theme_mode)

    def _draw_notice(self, target, colors):
        message = getattr(self.panel, "message", "")
        if not message or pygame.time.get_ticks() >= getattr(self.panel, "message_until", 0):
            return
        width = min(ui_theme.METRICS["tooltip_width"],
                    target.get_width() - ui_theme.SPACE["xl"])
        notice = pygame.Rect(0, 0, width, ui_theme.METRICS["control_height"] +
                             ui_theme.SPACE["sm"])
        notice.midtop = (target.get_width() // 2,
                         self.app_layout.topbar.bottom + ui_theme.SPACE["sm"])
        pygame.draw.rect(target, colors["SURFACE_2"], notice,
                         border_radius=ui_theme.METRICS["radius"])
        pygame.draw.rect(target, colors["BORDER"], notice,
                         ui_theme.METRICS["border"],
                         border_radius=ui_theme.METRICS["radius"])
        fonts.draw_text(target, message, notice.center, "hint", colors["TEXT"],
                        anchor="center", max_width=notice.width - ui_theme.SPACE["lg"])

    def _shortcut_rows(self):
        return help_rows(self.active_destination,
                         getattr(self, "_last_scene_shape", "Cube"),
                         appearance.navigation_preset())

    def _cycle_render_mode(self):
        index = RENDER_MODES.index(self.render_mode)
        self._set_render_mode(RENDER_MODES[(index + 1) % len(RENDER_MODES)])

    def _set_render_mode(self, value):
        if value in RENDER_MODES:
            self.render_mode = value
