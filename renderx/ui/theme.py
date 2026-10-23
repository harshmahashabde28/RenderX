"""Shared RenderX UI palette, type scale, spacing, and component metrics."""

from __future__ import annotations

from typing import Final


TYPE_SCALE: Final = {
    "micro": ("ui", 11),
    "hint": ("ui", 12),
    "control": ("ui", 13),
    "body": ("ui", 15),
    "section": ("ui", 18),
    "title": ("ui", 24),
    "value": ("mono", 13),
    "status": ("mono", 11),
}

SPACE: Final = {
    "unit": 4, "xs": 4, "sm": 8, "md": 12, "lg": 16,
    "xl": 24, "xxl": 32,
}

METRICS: Final = {
    "topbar_height": 56,
    "status_height": 28,
    "left_dock": 232,
    "right_dock": 288,
    "dock_min": 176,
    "dock_max": 420,
    "collapsed_rail": 36,
    "splitter": 6,
    "row_height": 32,
    "control_height": 28,
    "section_height": 32,
    "icon_small": 16,
    "icon_medium": 20,
    "icon_large": 24,
    "hit_target": 28,
    "radius": 4,
    "border": 1,
    "stroke": 1,
    "transition_ms": 150,
    "min_width": 1024,
    "min_height": 640,
    "tooltip_width": 288,
    "dialog_width": 480,
    "title_height": 40,
    "brand_width": 118,
    "nav_min_width": 240,
    "nav_max_width": 380,
    "projection_width": 132,
    "render_mode_width": 132,
    "min_viewport_width": 380,
    "slider_row": 32,
    "hint_line": 20,
    "numeric_field_width": 92,
    "slider_min_width": 72,
    "field_width": 92,
    "menu_width": 680,
    "menu_row_height": 36,
    "gizmo_size": 52,
    "panel_padding": 12,
    "viewport_inset": 12,
    "fps_warning": 30,
    "scrollbar_width": 3,
    "scrollbar_min_thumb": 24,
    "tooltip_delay_ms": 550,
}

_DARK: Final = {
    "CANVAS": (16, 20, 23),       # #101417
    "SURFACE_1": (23, 29, 33),    # #171D21
    "SURFACE_2": (32, 39, 44),    # #20272C
    "SURFACE_3": (41, 49, 54),    # #293136
    "SURFACE_4": (53, 62, 68),    # #353E44
    "BORDER": (59, 69, 74),
    "TEXT": (228, 233, 235),
    "TEXT_MUTED": (161, 173, 180),
    "TEXT_DIM": (125, 136, 142),
    "ACCENT": (113, 201, 179),   # #71C9B3
    "ACCENT_TEXT": (14, 31, 27),
    "SUCCESS": (139, 191, 155),
    "WARNING": (213, 173, 112),
    "ERROR": (215, 129, 120),
    "AXIS_X": (210, 122, 114),
    "AXIS_Y": (135, 184, 138),
    "AXIS_Z": (124, 158, 196),
    "GRID": (37, 46, 50),
    "VIEWPORT": (13, 17, 19),
    "FOCUS": (113, 201, 179),
}

_LIGHT: Final = {
    "CANVAS": (239, 241, 239),
    "SURFACE_1": (249, 250, 248),
    "SURFACE_2": (235, 239, 236),
    "SURFACE_3": (224, 230, 226),
    "SURFACE_4": (204, 213, 208),
    "BORDER": (190, 200, 195),
    "TEXT": (35, 44, 45),
    "TEXT_MUTED": (83, 98, 96),
    "TEXT_DIM": (105, 118, 115),
    "ACCENT": (40, 126, 106),
    "ACCENT_TEXT": (248, 252, 250),
    "SUCCESS": (39, 122, 77),
    "WARNING": (143, 98, 37),
    "ERROR": (164, 66, 58),
    "AXIS_X": (179, 70, 61),
    "AXIS_Y": (50, 126, 72),
    "AXIS_Z": (50, 94, 153),
    "GRID": (207, 216, 211),
    "VIEWPORT": (226, 231, 228),
    "FOCUS": (40, 126, 106),
}


def palette(mode: str = "dark") -> dict[str, tuple[int, int, int]]:
    """Return a fresh palette with compatibility aliases for existing drawing."""
    source = _LIGHT if mode == "light" else _DARK
    values = dict(source)
    values.update({
        "BACKGROUND": source["VIEWPORT"],
        "PANEL": source["SURFACE_1"],
        "MUTED": source["TEXT_MUTED"],
        "SELECTED": source["WARNING"],
        "APP_BG": source["CANVAS"],
        "CARD_BG": source["SURFACE_1"],
        "CARD_BORDER": source["BORDER"],
        "TEXT_DARK": source["TEXT"],
        "TEXT_SECONDARY": source["TEXT_MUTED"],
        "TAB_ACTIVE": source["SURFACE_2"],
        "ACCENT_SOFT": source["ACCENT"],
        "CORRECT": source["SUCCESS"],
        "INCORRECT": source["ERROR"],
        "MAP_BG": source["SURFACE_2"],
        "MAP_FOG": source["SURFACE_3"],
        "MAP_WALL": source["TEXT_MUTED"],
        "MAP_FLOOR": source["SURFACE_1"],
        "NOTE_BG": source["SURFACE_2"],
        "BUTTON_HOVER": source["SURFACE_3"],
        "ACTIVE_HOVER": source["ACCENT"],
    })
    return values


def component_color(state: str, mode: str = "dark") -> tuple[int, int, int]:
    """Resolve a control state without scattering palette choices in widgets."""
    colors = palette(mode)
    return {
        "default": colors["SURFACE_2"],
        "hover": colors["SURFACE_3"],
        "pressed": colors["SURFACE_4"],
        "focused": colors["SURFACE_2"],
        "disabled": colors["SURFACE_1"],
        "active": colors["ACCENT"],
    }.get(state, colors["SURFACE_2"])
