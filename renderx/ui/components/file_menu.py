"""Compact File menu anchored visually as a centered desktop-style popup."""

import pygame

from renderx.input_map import modifier_name
from .. import fonts, theme
from .button import draw_button


def draw_file_menu(surface, recent, *, mode="dark", hovered=None):
    colors = theme.palette(mode)
    veil = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    veil.fill((*colors["CANVAS"], 150))
    surface.blit(veil, (0, 0))
    padding = theme.SPACE["lg"]
    modifier = modifier_name()
    rows = [(("file_menu", "open"), "Open OBJ…", f"{modifier}+O")]
    rows.extend((("file_menu", "recent", path), path, "")
                for path in recent[:6])
    rows.extend([
        (("file_menu", "export"), "Export screenshot", f"{modifier}+S / F12"),
        (("file_menu", "home"), "Return to landing", f"{modifier}+Shift+H"),
        (("file_menu", "preferences"), "Preferences", f"{modifier}+,"),
        (("file_menu", "quit"), "Quit RenderX", f"{modifier}+Q"),
    ])
    width = min(theme.METRICS["dialog_width"], surface.get_width() - padding * 2)
    row_height = theme.METRICS["row_height"]
    height = padding * 2 + theme.METRICS["title_height"] + len(rows) * row_height
    height = min(height, surface.get_height() - padding * 2)
    panel = pygame.Rect(0, 0, width, height)
    panel.center = surface.get_rect().center
    pygame.draw.rect(surface, colors["SURFACE_1"], panel,
                     border_radius=theme.METRICS["radius"])
    pygame.draw.rect(surface, colors["BORDER"], panel, theme.METRICS["border"],
                     border_radius=theme.METRICS["radius"])
    fonts.draw_text(surface, "File", (panel.x + padding, panel.y + padding),
                    "section", colors["TEXT"], bold=True)
    item_height = max(theme.METRICS["control_height"],
                      min(row_height, (panel.height - padding * 2 -
                                      theme.METRICS["title_height"]) // len(rows)))
    y = panel.y + padding + theme.METRICS["title_height"]
    actions = {}
    for action, label, shortcut in rows:
        rect = pygame.Rect(panel.x + padding, y,
                           panel.width - padding * 2, item_height)
        visible = label
        if len(action) > 1 and action[1] == "recent":
            visible = label.replace("\\", "/").rsplit("/", 1)[-1]
        draw_button(surface, rect, visible, mode=mode, align="left",
                    shortcut=shortcut or None,
                    state="hover" if action == hovered else "default")
        actions[action] = rect
        y += item_height
    return panel, actions
