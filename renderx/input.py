"""Map input to shared actions; keep drag state out of mesh data."""
import pygame
from renderx import config
from renderx.renderer import VIEWPORT
from renderx.input_map import (DEFAULT_NAVIGATION_PRESET, EDITOR_KEYS,
                               GLOBAL_KEYS, MOUSE_GESTURES,
                               SHAPE_KEYS)


def _key_state(keys, key):
    """Return a held-key value, treating partial test/event maps as unpressed."""
    try:
        return keys[key]
    except (IndexError, KeyError):
        return 0


class _FilteredKeys:
    """Expose only the held keys allowed by the active quest challenge."""
    def __init__(self, keys, allowed):
        self.keys = keys
        self.allowed = set()
        if 'rotate' in allowed:
            self.allowed.update((EDITOR_KEYS["rotate_up"], EDITOR_KEYS["rotate_down"],
                                 EDITOR_KEYS["rotate_left"], EDITOR_KEYS["rotate_right"],
                                 EDITOR_KEYS["rotate_z_negative"],
                                 EDITOR_KEYS["rotate_z_positive"]))
        if 'depth' in allowed:
            self.allowed.update((EDITOR_KEYS["depth_nearer"],
                                 EDITOR_KEYS["depth_farther"]))
        if 'move' in allowed:
            self.allowed.update((EDITOR_KEYS["move_forward"],
                                 EDITOR_KEYS["move_left"],
                                 EDITOR_KEYS["move_backward"],
                                 EDITOR_KEYS["move_right"]))
        if 'scale' in allowed:
            self.allowed.update((*EDITOR_KEYS["scale_up"],
                                 *EDITOR_KEYS["scale_down"]))

    def __getitem__(self, key):
        return _key_state(self.keys, key) if key in self.allowed else 0


class Controls:
    def __init__(self):
        self.load_requested = False
        self.screenshot_requested = False
        self.focused = True
        self.drag = None
        self.drag_button = None
        self.navigation_preset = DEFAULT_NAVIGATION_PRESET
        self._mouse_captured = False
        self._held_keys = set()
        self._blocked_keys = set()

    def observe_events(self, events):
        """Track keys even when the dashboard consumes their key-down event."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._held_keys.add(event.key)
            elif event.type == pygame.KEYUP:
                self._held_keys.discard(event.key)
                self._blocked_keys.discard(event.key)

    def release_held_keys(self):
        """Ignore keys held through a destination change until they are released."""
        self._blocked_keys.update(self._held_keys)

    def cancel_drag(self):
        self.drag = None
        self.drag_button = None
        if self._mouse_captured:
            try:
                pygame.event.set_grab(False)
            except pygame.error:
                pass
            self._mouse_captured = False

    def _capture_mouse(self):
        try:
            pygame.event.set_grab(True)
            self._mouse_captured = pygame.event.get_grab()
        except pygame.error:
            self._mouse_captured = False

    def held_keys(self, scene, keys, dt):
        dt = min(max(dt, 0), config.MAX_DT)
        rotation = config.ROTATION_SPEED * dt
        movement = config.MOVE_SPEED * dt
        scene.rotate((_key_state(keys, EDITOR_KEYS["rotate_up"]) -
                      _key_state(keys, EDITOR_KEYS["rotate_down"])) * rotation,
                     (_key_state(keys, EDITOR_KEYS["rotate_right"]) -
                      _key_state(keys, EDITOR_KEYS["rotate_left"])) * rotation,
                     (_key_state(keys, EDITOR_KEYS["rotate_z_positive"]) -
                      _key_state(keys, EDITOR_KEYS["rotate_z_negative"])) * rotation)
        scene.move((_key_state(keys, EDITOR_KEYS["move_right"]) -
                    _key_state(keys, EDITOR_KEYS["move_left"])) * movement,
                   (_key_state(keys, EDITOR_KEYS["move_forward"]) -
                    _key_state(keys, EDITOR_KEYS["move_backward"])) * movement,
                   (_key_state(keys, EDITOR_KEYS["depth_farther"]) -
                    _key_state(keys, EDITOR_KEYS["depth_nearer"])) * movement)
        bigger = any(_key_state(keys, key) for key in EDITOR_KEYS["scale_up"])
        smaller = any(_key_state(keys, key) for key in EDITOR_KEYS["scale_down"])
        scene.resize((bigger - smaller) * config.SCALE_SPEED * dt)

    def update(self, scene, events, keys, dt, _panel, mouse_position, modifiers=0,
               allowed_controls=None):
        """Return False to exit. A reset/selection wins over motion this frame."""
        self.observe_events(events)
        self.load_requested = False
        self.screenshot_requested = False
        suppress_motion = False
        focus_changed = False
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
                self.focused = False
                focus_changed = True
                self.cancel_drag()
            elif event.type == pygame.WINDOWFOCUSGAINED:
                self.focused = True
                focus_changed = True
                self.cancel_drag()
            action = None
            if event.type == pygame.KEYDOWN:
                if event.key == GLOBAL_KEYS["cancel"]:
                    return False
                if self.focused:
                    unrestricted = allowed_controls is None
                    if event.key == EDITOR_KEYS["projection"] and (unrestricted or 'projection' in allowed_controls):
                        scene.projection = ("Orthographic" if scene.projection ==
                                            "Perspective" else "Perspective")
                    if event.key == EDITOR_KEYS["axes"] and (unrestricted or 'axes' in allowed_controls):
                        scene.axes_visible = not scene.axes_visible
                    if event.key == EDITOR_KEYS["open_sample"] and (unrestricted or 'obj' in allowed_controls):
                        self.load_requested = True
                        suppress_motion = True
                        self.cancel_drag()
                    if event.key == EDITOR_KEYS["screenshot"]:
                        self.screenshot_requested = True
                    if unrestricted or 'shape' in allowed_controls:
                        action = SHAPE_KEYS.get(event.key)
                    if event.key == EDITOR_KEYS["reset"] and (unrestricted or 'reset' in allowed_controls):
                        action = "Reset"
            if action is not None:
                if action == "Reset":
                    scene.reset()
                else:
                    scene.select(action)
                suppress_motion = True
                self.cancel_drag()

        if not self.focused or focus_changed or suppress_motion:
            return True
        base_keys = (_BlockedKeys(keys, self._blocked_keys)
                     if self._blocked_keys else keys)
        filtered_keys = (base_keys if allowed_controls is None else
                         _FilteredKeys(base_keys, allowed_controls))
        self.held_keys(scene, filtered_keys, dt)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if VIEWPORT.collidepoint(event.pos) and self.drag is None:
                    can_rotate = allowed_controls is None or 'rotate' in allowed_controls
                    can_move = allowed_controls is None or 'move' in allowed_controls
                    shift = bool(modifiers & pygame.KMOD_SHIFT)
                    gesture = MOUSE_GESTURES.get(
                        self.navigation_preset, MOUSE_GESTURES[DEFAULT_NAVIGATION_PRESET])
                    if event.button == gesture["orbit"] and (can_rotate or can_move):
                        if shift and can_move:
                            self.drag = "pan"
                        elif can_rotate:
                            self.drag = "xy"
                    elif event.button in gesture["pan"] and can_move:
                        self.drag = "pan"
                    elif event.button in gesture["z_turn"] and can_rotate:
                        self.drag = "z"
                    if self.drag:
                        self.drag_button = event.button
                        self._capture_mouse()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == self.drag_button:
                    self.cancel_drag()
            elif event.type == pygame.MOUSEMOTION and self.drag:
                dx, dy = event.rel
                if self.drag == "pan":
                    scene.move(dx * config.DRAG_MOVE, -dy * config.DRAG_MOVE)
                elif self.drag == "xy":
                    scene.rotate(-dy * config.DRAG_ROTATION,
                                 dx * config.DRAG_ROTATION)
                else:
                    scene.rotate(dz=dx * config.DRAG_ROTATION)
            elif event.type == pygame.MOUSEWHEEL:
                if ((allowed_controls is None or 'scale' in allowed_controls) and
                        VIEWPORT.collidepoint(mouse_position)):
                    scene.resize(event.y * config.WHEEL_SCALE)
        return True


class _BlockedKeys:
    """Hide physically held keys until a matching KEYUP clears the block."""
    def __init__(self, keys, blocked):
        self.keys = keys
        self.blocked = blocked

    def __getitem__(self, key):
        return 0 if key in self.blocked else _key_state(self.keys, key)
