"""Maze campaign summary, explored map, and direct game actions."""

import pygame

from renderx.maze_ui import draw_explored_map

from .. import fonts, theme
from .common import draw_panel


def draw_maze_panel(surface, rect, maze, ui, *, mode="dark"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    draw_panel(surface, rect, mode)
    x = rect.x + theme.SPACE["md"]
    width = max(1, rect.width - theme.SPACE["lg"])
    y = rect.y + theme.SPACE["md"]
    fonts.draw_text(surface, "SIGNAL RECOVERY", (x, y), "hint", colors["TEXT_MUTED"], bold=True)
    y += theme.METRICS["section_height"]
    fonts.draw_text(surface, f"Stage {maze.level} / 3", (x, y), "section", colors["TEXT"], bold=True)
    y += theme.METRICS["row_height"]
    fonts.draw_text(surface, f"Keys  {len(maze.keys_found)} / 2", (x, y), "hint", colors["TEXT_MUTED"])
    fonts.draw_text(surface, "Exit open" if maze.exit_unlocked else "Exit sealed",
                    (rect.right - theme.SPACE["md"], y), "hint",
                    colors["SUCCESS"] if maze.exit_unlocked else colors["WARNING"],
                    anchor="topright")
    y += theme.METRICS["row_height"]
    fonts.draw_text(surface, f"TIME  {int(maze.elapsed):02d}s", (x, y), "status", colors["TEXT_MUTED"])
    fonts.draw_text(surface, f"SCORE  {maze.total_score:,}",
                    (rect.right - theme.SPACE["md"], y), "status",
                    colors["TEXT_MUTED"], anchor="topright")
    y += theme.METRICS["hint_line"]
    fonts.draw_text(surface, f"BEST  {maze.best_score:,}", (x, y), "status",
                    colors["TEXT_MUTED"])
    y += theme.METRICS["row_height"] + theme.SPACE["xs"]
    fonts.draw_text(surface, "EXPLORED MAP", (x, y), "micro", colors["TEXT_MUTED"], bold=True)
    y += theme.METRICS["hint_line"]
    buttons_h = theme.METRICS["control_height"]
    actions_h = buttons_h * 2 + theme.SPACE["sm"]
    map_size = min(width, rect.bottom - y - actions_h - theme.SPACE["xl"])
    map_rect = pygame.Rect(x, y, max(1, map_size), max(1, map_size))
    draw_explored_map(surface, maze, map_rect, mode=mode)
    y = map_rect.bottom + theme.SPACE["sm"]
    scan_text = f"Scan  ·  {max(0, 3 - maze.scans_used)} left"
    pair_gap = theme.SPACE["sm"]
    half = (width - pair_gap) // 2
    _button(surface, ui, ("maze_action", "scan"), scan_text,
            pygame.Rect(x, y, half, buttons_h), mode,
            "disabled" if maze.paused or maze.won else "default")
    _button(surface, ui, ("maze_action", "pause"),
            "Resume" if maze.paused else "Pause",
            pygame.Rect(x + half + pair_gap, y, half, buttons_h), mode,
            "active" if maze.paused else "default")
    y += buttons_h + theme.SPACE["xs"]
    _button(surface, ui, ("maze_action", "projection"),
            f"{maze.projection} projection",
            pygame.Rect(x, y, half, buttons_h), mode)
    next_action = "continue" if maze.won and not maze.campaign_complete else "new-maze"
    next_label = "Next stage" if next_action == "continue" else "New run"
    _button(surface, ui, ("maze_action", next_action), next_label,
            pygame.Rect(x + half + pair_gap, y, half, buttons_h), mode,
            "active" if next_action == "continue" else "default")
    hint_y = rect.bottom - theme.METRICS["hint_line"] - theme.SPACE["xs"]
    fonts.draw_text(surface, "WASD move  ·  Q/E strafe  ·  Space scan",
                    (x, hint_y), "micro", colors["TEXT_DIM"], max_width=width)


def _button(surface, ui, action, label, rect, mode, state="default"):
    ui.button(action, label, rect, active=state == "active")
    ui.paint_button(surface, action, mode=mode, state=state, align="center")
