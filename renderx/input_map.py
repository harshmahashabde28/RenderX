"""Shared keyboard and viewport gesture bindings for the RenderX editor.

Keeping display names beside the actual key constants makes the help overlay
and interaction code describe the same actions.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys

import pygame


SHAPE_KEYS = {
    pygame.K_1: "Cube",
    pygame.K_2: "Pyramid",
    pygame.K_3: "Rectangular prism",
}

EDITOR_KEYS = {
    "rotate_up": pygame.K_UP, "rotate_down": pygame.K_DOWN,
    "rotate_right": pygame.K_RIGHT, "rotate_left": pygame.K_LEFT,
    "rotate_z_positive": pygame.K_e, "rotate_z_negative": pygame.K_q,
    "move_right": pygame.K_d, "move_left": pygame.K_a,
    "move_forward": pygame.K_w, "move_backward": pygame.K_s,
    "depth_farther": pygame.K_PAGEDOWN, "depth_nearer": pygame.K_PAGEUP,
    "scale_up": (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS),
    "scale_down": (pygame.K_MINUS, pygame.K_KP_MINUS),
    "projection": pygame.K_p, "axes": pygame.K_x,
    "open_sample": pygame.K_o, "screenshot": pygame.K_F12,
    "reset": pygame.K_r, "render_mode": pygame.K_m,
    "play_pause": pygame.K_SPACE,
}

MAZE_KEYS = {
    "turn_right": (pygame.K_RIGHT, pygame.K_d),
    "turn_left": (pygame.K_LEFT, pygame.K_a),
    "move_forward": (pygame.K_UP, pygame.K_w),
    "move_backward": (pygame.K_DOWN, pygame.K_s),
    "strafe_right": pygame.K_e, "strafe_left": pygame.K_q,
    "projection": pygame.K_p, "scan": pygame.K_SPACE,
    "pause": pygame.K_ESCAPE, "new_run": pygame.K_r,
    "continue": (pygame.K_RETURN, pygame.K_c),
}

SHOOTER_KEYS = {
    "move_right": (pygame.K_d, pygame.K_RIGHT),
    "move_left": (pygame.K_a, pygame.K_LEFT),
    "move_backward": (pygame.K_s, pygame.K_DOWN),
    "move_forward": (pygame.K_w, pygame.K_UP),
    "fire": pygame.K_SPACE,
    "fullscreen": pygame.K_F11,
    "pause": pygame.K_ESCAPE,
    "dash": (pygame.K_LSHIFT, pygame.K_RSHIFT),
}

GLOBAL_KEYS = {
    "help": (pygame.K_F1,), "preferences": pygame.K_COMMA,
    "open_file": pygame.K_o, "export_screenshot": pygame.K_s,
    "quit": pygame.K_q, "quit_alt": pygame.K_F4,
    "fullscreen": pygame.K_F11, "cancel": pygame.K_ESCAPE,
    "next_destination": pygame.K_TAB, "focus_next": pygame.K_F6,
    "activate": (pygame.K_RETURN, pygame.K_KP_ENTER),
    "field_backspace": pygame.K_BACKSPACE,
    "select_all": pygame.K_a,
    "step_up": pygame.K_UP, "step_down": pygame.K_DOWN,
    "adjust_left": pygame.K_LEFT, "adjust_right": pygame.K_RIGHT,
    "reset_view": (pygame.K_HOME, pygame.K_f, pygame.K_KP_PERIOD),
    "projection_toggle": (pygame.K_KP5, pygame.K_5),
    "front_view": (pygame.K_KP1, pygame.K_1),
    "right_view": (pygame.K_KP3, pygame.K_3),
    "top_view": (pygame.K_KP7, pygame.K_7),
    "return_home": pygame.K_h,
}

NAVIGATION_PRESETS = ("Orbit Viewer", "RenderX Classic")
DEFAULT_NAVIGATION_PRESET = "Orbit Viewer"
MOUSE_BUTTONS = {"primary": 1, "middle": 2, "secondary": 3}
MOUSE_GESTURES = {
    "Orbit Viewer": {"orbit": MOUSE_BUTTONS["primary"],
                     "pan": (MOUSE_BUTTONS["middle"], MOUSE_BUTTONS["secondary"]),
                     "z_turn": ()},
    "RenderX Classic": {"orbit": MOUSE_BUTTONS["primary"],
                        "pan": (MOUSE_BUTTONS["middle"],),
                        "z_turn": (MOUSE_BUTTONS["secondary"],)},
}


@dataclass(frozen=True)
class Shortcut:
    group: str
    action: str
    key: str
    destinations: tuple[str, ...] = ()


def modifier_name() -> str:
    """Return the platform's familiar Command or Control label."""
    return "Cmd" if sys.platform == "darwin" else "Ctrl"


def shortcut_catalog(destination: str, shape: str) -> tuple[Shortcut, ...]:
    """Return shortcuts that are available in the current editor destination."""
    mod = modifier_name()
    rows = [
        Shortcut("File", "Open OBJ", f"{mod}+O"),
        Shortcut("File", "Export screenshot", f"{mod}+S / F12"),
        Shortcut("Application", "Quit", f"{mod}+Q / Alt+F4"),
        Shortcut("Application", "Toggle fullscreen", "F11"),
        Shortcut("Application", "Preferences", f"{mod}+,"),
        Shortcut("Application", "Shortcuts", "F1 / ?"),
        Shortcut("Application", "Close / cancel overlay", "Esc"),
        Shortcut("Application", "Move focus through controls", "F6"),
        Shortcut("Application", "Switch destination", "Tab"),
        Shortcut("Application", "Open landing page", f"{mod}+Shift+H"),
        Shortcut("Application", "Switch page", f"{mod}+Alt+1–4"),
    ]
    if destination == "Explore":
        rows.extend((
            Shortcut("Navigation", "Orbit / pan / zoom", "Preset gestures"),
            Shortcut("Navigation", "Reset scene pose", "Home / F / KP . / R"),
            Shortcut("Navigation", "Front / right / top",
                     f"KP 1 / 3 / 7; {mod}+1 / 3 / 7"),
            Shortcut("Navigation", "Opposite views",
                     f"{mod}+KP 1 / 3 / 7; {mod}+Shift+1 / 3 / 7"),
            Shortcut("Navigation", "Perspective / orthographic",
                     f"KP 5 / {mod}+5 / P"),
            Shortcut("Object", "Choose Cube / Pyramid / Prism", "1 / 2 / 3"),
            Shortcut("Object", "Rotate X / Y / Z", "↑ ↓ ← → / Q E"),
            Shortcut("Object", "Move X / Y", "W A S D"),
            Shortcut("Object", "Move depth / scale", "Page Up/Down / + −"),
            Shortcut("Object", "Reset object transforms", "R"),
            Shortcut("Display", "Render mode / axes / sample", "M / X / O"),
        ))
        if shape == "Signal wave":
            rows.append(Shortcut("Animation", "Signal wave play / pause", "Space"))
        rows.extend((
            Shortcut("Navigation", "Open context menu", "Right-click viewport / object"),
            Shortcut("Navigation", "Pan alias", "Shift+LMB"),
            Shortcut("Fields", "Commit / cancel numeric edit", "Enter / Esc"),
            Shortcut("Fields", "Select all / step / next field", f"{mod}+A / ↑↓ / Tab"),
        ))
    elif destination == "Challenges":
        rows.extend((
            Shortcut("Challenge", "Rotate / move / scale", "↑ ↓ ← → / Q E / W A S D / + −"),
            Shortcut("Challenge", "Projection / axes", "P / X"),
        ))
    elif destination == "Maze":
        rows.extend((
            Shortcut("Maze", "Move / turn", "W A S D / ↑ ↓ ← →"),
            Shortcut("Maze", "Strafe / projection", "Q E / P"),
            Shortcut("Maze", "Scan / pause", "Space / Esc"),
            Shortcut("Maze", "New run", "R"),
            Shortcut("Maze", "Continue after stage", "Enter / C"),
        ))
    else:
        rows.extend((
            Shortcut("Breakpoint", "Move / aim / fire", "W A S D / mouse / LMB or Space"),
            Shortcut("Breakpoint", "Dash / pause / fullscreen", "Shift / Esc / F11"),
        ))
    return tuple(rows)


def help_rows(destination: str, shape: str, preset: str) -> tuple[tuple[str, str], ...]:
    """Format the live binding catalog for the compact shortcuts overlay."""
    rows = []
    for binding in shortcut_catalog(destination, shape):
        key = binding.key
        if binding.key == "Preset gestures":
            key = ("LMB orbit · RMB drag pan · MMB pan · wheel zoom"
                   if preset == "Orbit Viewer" else
                   "LMB orbit · RMB drag Z-turn · MMB pan · wheel zoom")
        rows.append((f"{binding.group} · {binding.action}", key))
    return tuple(rows)


def navigation_status(preset: str) -> str:
    """Short live mouse guidance for the Explore status bar."""
    if preset == "RenderX Classic":
        return "Y-up · LMB orbit · RMB click menu / drag Z · MMB pan · wheel zoom"
    return "Y-up · LMB orbit · RMB click menu / drag pan · MMB pan · wheel zoom"


def _ctrl(modifiers: int) -> bool:
    return bool(modifiers & pygame.KMOD_CTRL) or (
        sys.platform == "darwin" and bool(modifiers & pygame.KMOD_META))


def has_primary_modifier(modifiers: int) -> bool:
    return _ctrl(modifiers)


def view_shortcut(key: int, modifiers: int) -> tuple[str, int] | None:
    """Return (axis, sign) for a standard front/right/top view key.

    Ctrl+number is the laptop-friendly alias because the existing unmodified
    1/2/3 keys already select meshes. Ctrl+Shift selects the opposite side.
    """
    control = _ctrl(modifiers)
    shift = bool(modifiers & pygame.KMOD_SHIFT)
    views = {
        pygame.K_KP1: "front", pygame.K_KP3: "right", pygame.K_KP7: "top",
        pygame.K_1: "front", pygame.K_3: "right", pygame.K_7: "top",
    }
    view = views.get(key)
    if view is None:
        return None
    if key in (pygame.K_1, pygame.K_3, pygame.K_7) and not control:
        return None
    opposite = (control if key in (pygame.K_KP1, pygame.K_KP3, pygame.K_KP7)
                else control and shift)
    return view, -1 if opposite else 1
