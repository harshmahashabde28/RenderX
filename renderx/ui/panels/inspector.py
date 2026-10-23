"""Transform and display inspector backed by the existing Scene methods."""

import math

import pygame

from renderx import config
from renderx.rasterizer import RENDER_MODES

from .. import fonts, theme
from ..components import (draw_dropdown, draw_section, draw_slider,
                          draw_toggle, draw_value)
from .common import draw_panel


def draw_inspector_panel(surface, rect, scene, ui, *, mode="dark",
                         collapsed=False):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    draw_panel(surface, rect, mode)
    padding = theme.SPACE["md"]
    if collapsed:
        action_rect = pygame.Rect(rect.centerx - theme.METRICS["hit_target"] // 2,
                                  rect.y + padding, theme.METRICS["hit_target"],
                                  theme.METRICS["hit_target"])
        ui.button(("dock", "right"), "Expand inspector", action_rect)
        ui.paint_button(surface, ("dock", "right"), mode=mode,
                        icon="panel-right-open", align="center")
        return

    x = rect.x + padding
    width = rect.width - padding * 2
    y = rect.y + padding
    fonts.draw_text(surface, "INSPECTOR", (x, y), "hint",
                    colors["TEXT_MUTED"], bold=True)
    collapse_rect = pygame.Rect(rect.right - padding -
                                theme.METRICS["hit_target"] * 2 - theme.SPACE["xs"],
                                y - theme.SPACE["xs"],
                                theme.METRICS["hit_target"],
                                theme.METRICS["hit_target"])
    ui.button(("dock_collapse", "right"), "Collapse inspector dock", collapse_rect)
    ui.paint_button(surface, ("dock_collapse", "right"), mode=mode,
                    icon="panel-right-close", align="center")
    reset = pygame.Rect(rect.right - padding - theme.METRICS["hit_target"], y - theme.SPACE["xs"],
                        theme.METRICS["hit_target"], theme.METRICS["hit_target"])
    ui.button(("reset",), "Reset scene pose", reset)
    ui.paint_button(surface, ("reset",), mode=mode, icon="home",
                    shortcut="R", align="center")
    y += theme.METRICS["section_height"]

    transform_header = pygame.Rect(x, y, width, theme.METRICS["section_height"])
    draw_section(surface, transform_header, "TRANSFORM", mode=mode,
                 expanded=ui.section_open("transform"))
    ui.button(("section", "transform"), "Transform", transform_header)
    y = transform_header.bottom + theme.SPACE["xs"]
    if ui.section_open("transform"):
        y = _axis_group(surface, x, y, width, scene, ui, "Rotation",
                        "rotation", tuple(math.degrees(a) % 360 for a in scene.angles),
                        (0.0, 360.0, 0.0, 359.0), mode, colors)
        y = _axis_group(surface, x, y, width, scene, ui, "Position",
                        "position", scene.position,
                        (-config.POSITION_LIMIT, config.POSITION_LIMIT,
                         -config.POSITION_LIMIT, config.POSITION_LIMIT),
                        mode, colors, depth_range=(config.MIN_DEPTH, config.MAX_DEPTH))
        scale_y = y + theme.SPACE["xs"]
        _draw_slider_field(surface, pygame.Rect(x, scale_y, width,
                            theme.METRICS["slider_row"]), "Scale", scene.scale,
                           config.MIN_SCALE, config.MAX_SCALE,
                           ("slider", "scale", 0), ("field", "scale", 0),
                           ui, mode, colors, fmt=".2f")
        y = scale_y + theme.METRICS["slider_row"] + theme.SPACE["sm"]

    display_y = y + theme.SPACE["xs"]
    display_header = pygame.Rect(x, display_y, width,
                                 theme.METRICS["section_height"])
    draw_section(surface, display_header, "DISPLAY", mode=mode,
                 expanded=ui.section_open("display"))
    ui.button(("section", "display"), "Display", display_header)
    y = display_header.bottom + theme.SPACE["xs"]
    if ui.section_open("display"):
        fonts.draw_text(surface, "Projection", (x, y + theme.SPACE["xs"]),
                        "hint", colors["TEXT_MUTED"])
        y += theme.METRICS["control_height"] + theme.SPACE["xs"]
        item_rects = ui.segmented(surface, ("projection_panel",),
                                  ("Perspective", "Orthographic"),
                                  scene.projection,
                                  pygame.Rect(x, y, width, theme.METRICS["control_height"]),
                                  mode=mode)
        y += theme.METRICS["control_height"] + theme.SPACE["sm"]
        mode_rect = pygame.Rect(x, y, width, theme.METRICS["control_height"])
        ui.button(("render_mode_select",), "Render mode", mode_rect)
        draw_dropdown(surface, mode_rect, "Render mode", ui.render_mode,
                      mode=mode, state=ui.state(("render_mode_select",)))
        y += theme.METRICS["control_height"] + theme.SPACE["xs"]
        axes_rect = pygame.Rect(x, y, width, theme.METRICS["control_height"])
        ui.button(("axes",), "Axes", axes_rect, active=scene.axes_visible)
        draw_toggle(surface, axes_rect, "World axes", scene.axes_visible,
                    mode=mode, state=ui.state(("axes",)))


def _axis_group(surface, x, y, width, scene, ui, label, kind, values,
                common_range, mode, colors, depth_range=None):
    fonts.draw_text(surface, label.upper(), (x, y), "micro",
                    colors["TEXT_MUTED"], bold=True)
    y += theme.METRICS["hint_line"]
    axis_names = "XYZ"
    for axis, value in enumerate(values):
        low, high = depth_range if kind == "position" and axis == 2 else common_range[:2]
        if kind == "position" and axis == 2:
            low, high = depth_range
        slider_width = max(theme.METRICS["slider_min_width"],
                           width - theme.METRICS["numeric_field_width"] - theme.SPACE["sm"])
        row = pygame.Rect(x, y, width, theme.METRICS["slider_row"])
        slider_rect = pygame.Rect(x, y, slider_width, row.height)
        field_rect = pygame.Rect(row.right - theme.METRICS["numeric_field_width"], y + theme.SPACE["xs"],
                                 theme.METRICS["numeric_field_width"],
                                 theme.METRICS["control_height"])
        action = ("slider", kind, axis)
        slider_hit = draw_slider(surface, slider_rect, f"{label} {axis_names[axis]}",
                                 value, low, high, mode=mode, value_text="",
                                 state=ui.state(action))
        ui.button(action, f"{label} {axis_names[axis]} · double-click to reset",
                  slider_hit)
        ui.buttons[action] = slider_hit
        field_action = ("field", kind, axis)
        formatted = f"{value:.1f}" if kind == "rotation" else f"{value:.2f}"
        field_display = ui.field_text(field_action, formatted)
        draw_value(surface, field_rect, axis_names[axis], field_display,
                    mode=mode, state="focused" if ui.focused_field == field_action else "default")
        ui.button(field_action, f"Edit {label} {axis_names[axis]}", field_rect)
        y += theme.METRICS["slider_row"]
    return y + theme.SPACE["xs"]


def _draw_slider_field(surface, rect, label, value, low, high, action, field_action,
                       ui, mode, colors, fmt=".2f"):
    slider_width = max(theme.METRICS["slider_min_width"],
                       rect.width - theme.METRICS["numeric_field_width"] - theme.SPACE["sm"])
    slider_rect = pygame.Rect(rect.x, rect.y, slider_width, rect.height)
    field_rect = pygame.Rect(rect.right - theme.METRICS["numeric_field_width"],
                             rect.y + theme.SPACE["xs"],
                             theme.METRICS["numeric_field_width"],
                             theme.METRICS["control_height"])
    hit_rect = draw_slider(surface, slider_rect, label, value, low, high,
                           mode=mode, value_text="", state=ui.state(action))
    ui.button(action, f"{label} · double-click to reset", hit_rect)
    ui.buttons[action] = hit_rect
    shown = ui.field_text(field_action, format(value, fmt))
    draw_value(surface, field_rect, "S", shown, mode=mode,
                state="focused" if ui.focused_field == field_action else "default")
    ui.button(field_action, f"Edit {label}", field_rect)
