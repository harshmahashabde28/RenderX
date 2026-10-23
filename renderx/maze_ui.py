"""Drawing helpers for the playable wireframe maze destination."""
from math import cos, degrees, sin

import pygame

from renderx import config
from renderx.renderer import draw_wireframe
from renderx.scene import Scene
from renderx.ui.theme import palette


def draw_maze_view(target, maze, viewport, title_font, small_font):
    """Render the first-person world through RenderX's clipping/projection path."""
    viewport = pygame.Rect(viewport)
    scene = Scene(angles=(0.0, 0.0, 0.0), position=(0.0, 0.0, 0.0),
                  scale=1.0, projection=maze.projection, axes_visible=False)
    camera = maze.camera
    wall_visibility = maze.visibility_for(viewport, 390)
    draw_wireframe(target, maze.floor_mesh, scene, camera, viewport=viewport,
                   focal_length=390, line_color=config.GRID,
                   vertex_color=config.GRID, show_vertices=False,
                   edge_visibility=wall_visibility)
    draw_wireframe(target, maze.wall_mesh, scene, camera, viewport=viewport,
                   focal_length=390, clear=False, show_vertices=False,
                   edge_visibility=wall_visibility)
    for index, cell in enumerate(maze.blueprint.keys):
        if index not in maze.keys_found:
            draw_wireframe(target, maze.key_meshes[cell], scene, camera,
                           viewport=viewport, focal_length=390,
                           line_color=config.SELECTED,
                           vertex_color=config.SELECTED, clear=False,
                           show_vertices=False,
                           edge_visibility=wall_visibility)
    exit_color = config.CORRECT if maze.exit_unlocked else config.INCORRECT
    draw_wireframe(target, maze.exit_mesh, scene, camera, viewport=viewport,
                   focal_length=390, line_color=exit_color,
                   vertex_color=exit_color, clear=False, show_vertices=False,
                   edge_visibility=wall_visibility)

    hud = pygame.Rect(viewport.x + 18, viewport.y + 16, 400, 42)
    _card(target, hud, config.PANEL)
    status = (f'LEVEL  {maze.level}/3    ·    KEYS  {len(maze.keys_found)}/2'
              f'    ·    EXIT  {"OPEN" if maze.exit_unlocked else "LOCKED"}')
    _text(target, status, (hud.x + 14, hud.centery), small_font,
          config.TEXT, center_y=True)
    timer = _format_time(maze.elapsed)
    timer_rect = pygame.Rect(viewport.right - 132, viewport.y + 16, 114, 42)
    _card(target, timer_rect, config.PANEL)
    _text(target, timer, timer_rect.center, title_font, config.TEXT, center=True)

    if maze.message_time > 0 and not maze.paused and not maze.won:
        banner = pygame.Rect(viewport.x + 100, viewport.y + 72,
                             viewport.width - 200, 42)
        _card(target, banner, config.PANEL)
        _text(target, maze.message, banner.center, small_font, config.TEXT,
              center=True)

    if maze.scan_flash > 0:
        scan = pygame.Rect(viewport.x + 18, viewport.bottom - 54, 218, 34)
        _card(target, scan, config.PANEL)
        _text(target, 'SIGNAL PULSE   ·   MAP UPDATED', scan.center,
              small_font, config.ACCENT, center=True)

    if maze.paused or maze.won:
        veil = pygame.Surface(viewport.size, pygame.SRCALPHA)
        veil.fill((11, 18, 28, 158))
        target.blit(veil, viewport.topleft)
        card = pygame.Rect(0, 0, 430, 208)
        card.center = viewport.center
        _card(target, card, config.CARD_BG, border=config.CARD_BORDER)
        if maze.paused:
            heading, detail = 'RUN PAUSED', 'Your maze and timer are safely paused.'
            score = 'Press Esc or choose Resume to continue.'
        elif maze.campaign_complete:
            heading, detail = 'SIGNAL RESTORED', 'All three mazes cleared.'
            score = f'Run score  {maze.total_score:,}    ·    Best  {maze.best_score:,}'
        else:
            heading, detail = f'LEVEL {maze.level} CLEARED', 'A new maze is ready when you are.'
            score = f'Level score  +{maze.level_score:,}    ·    Run score  {maze.total_score:,}'
        _text(target, heading, (card.centerx, card.y + 34), title_font,
              config.TEXT_DARK, center=True)
        _text(target, detail, (card.centerx, card.y + 91), small_font,
              config.TEXT_SECONDARY, center=True)
        _text(target, score, (card.centerx, card.y + 126), small_font,
              config.TEXT_DARK, center=True)
        prompt = ('Use the controls below to resume.' if maze.paused else
                  'Choose Next level below to keep your run going.' if not maze.campaign_complete else
                  'Choose New run below to start another campaign.')
        _text(target, prompt, (card.centerx, card.y + 169), small_font,
              config.TEXT_SECONDARY, center=True)
    if not maze.paused and not maze.won:
        _crosshair(target, viewport)


def draw_maze_sidebar(target, maze, rect, title_font, body_font, small_font):
    """Draw a compact game HUD and a map that fills in as the player explores."""
    rect = pygame.Rect(rect)
    _card(target, rect, config.CARD_BG, border=config.CARD_BORDER)
    x = rect.x + 24
    _text(target, 'SIGNAL RECOVERY', (x, rect.y + 24), small_font,
          config.ACCENT_TEXT)
    _text(target, f'Maze run  ·  Level {maze.level}', (x, rect.y + 48),
          title_font, config.TEXT_DARK)
    _wrap(target,
          'Find both signal keys. Your map fills in as you explore; scan for nearby routes.',
          x, rect.y + 82, rect.width - 48, body_font, config.TEXT_SECONDARY)

    stat_y = rect.y + 132
    half = (rect.width - 58) // 2
    _stat(target, pygame.Rect(x, stat_y, half, 58), 'RUN TIME',
          _format_time(maze.elapsed), small_font, config)
    _stat(target, pygame.Rect(x + half + 10, stat_y, half, 58), 'RUN SCORE',
          f'{maze.total_score:,}', small_font, config)
    _stat(target, pygame.Rect(x, stat_y + 66, half, 58), 'CELLS WALKED',
          str(maze.steps), small_font, config)
    _stat(target, pygame.Rect(x + half + 10, stat_y + 66, half, 58), 'BEST RUN',
          f'{maze.best_score:,}', small_font, config)

    objective_y = stat_y + 140
    _pill(target, (x, objective_y, 170, 34),
          f'Signal keys  {len(maze.keys_found)}/2',
          config.TAB_ACTIVE if maze.keys_found else config.CARD_BG,
          config.TEXT_DARK, small_font)
    exit_text = 'Exit open' if maze.exit_unlocked else 'Exit sealed'
    exit_color = config.CORRECT if maze.exit_unlocked else config.TEXT_SECONDARY
    _text(target, exit_text, (x + 188, objective_y + 9), small_font, exit_color)

    map_label_y = objective_y + 46
    _text(target, 'EXPLORED MAP', (x, map_label_y), small_font,
          config.TEXT_SECONDARY)
    _text(target, f'SEED {maze.seed}', (rect.right - 24, map_label_y),
          small_font, config.TEXT_SECONDARY, right=True)
    map_rect = pygame.Rect(x, map_label_y + 23, rect.width - 48, 186)
    _draw_minimap(target, maze, map_rect)

    legend_y = map_rect.bottom + 10
    _text(target, 'YOU', (x, legend_y), small_font, config.ACCENT_TEXT)
    _text(target, 'KEY', (x + 80, legend_y), small_font, config.SELECTED)
    _text(target, 'EXIT', (x + 160, legend_y), small_font,
          config.CORRECT if maze.exit_unlocked else config.INCORRECT)

    rule_y = rect.bottom - 76
    pygame.draw.line(target, config.CARD_BORDER, (x, rule_y),
                     (rect.right - 24, rule_y), 1)
    charges = max(0, 3 - maze.scans_used)
    _text(target, f'SCAN PULSE  {charges}/3', (x, rule_y + 16), small_font,
          config.TEXT_DARK)
    _text(target, 'Space or Scan reveals nearby cells.',
          (x, rule_y + 42), small_font, config.TEXT_SECONDARY)


def draw_maze_controls(target, rect, small_font, maze=None):
    rect = pygame.Rect(rect)
    _card(target, rect, config.CARD_BG, border=config.CARD_BORDER)
    if maze is not None and maze.paused:
        hint = 'Run paused   ·   Esc or Resume continues   ·   New run resets your progress'
    elif maze is not None and maze.won and maze.campaign_complete:
        hint = 'Campaign complete   ·   New run starts another three-stage run'
    elif maze is not None and maze.won:
        hint = 'Level cleared   ·   Next level continues your run   ·   New run resets progress'
    else:
        hint = ('W / Up move   ·   S / Down back   ·   A / D turn   ·   Q / E strafe   ·   '
                'Space scan   ·   P projection   ·   Esc pause')
    _text(target, hint, (rect.x + 20, rect.bottom - 28), small_font,
          config.TEXT_SECONDARY)


def _draw_minimap(target, maze, rect):
    pygame.draw.rect(target, config.MAP_BG, rect, border_radius=9)
    pygame.draw.rect(target, config.CARD_BORDER, rect, 1, border_radius=9)
    size = min(17, (rect.width - 20) / maze.blueprint.size,
               (rect.height - 20) / maze.blueprint.size)
    map_width = round(size * maze.blueprint.size)
    map_height = map_width
    left = rect.centerx - map_width // 2
    top = rect.centery - map_height // 2
    fog = config.MAP_FOG
    wall = config.MAP_WALL
    floor = config.MAP_FLOOR
    for z, row in enumerate(maze.blueprint.cells):
        for x, is_wall in enumerate(row):
            tile = pygame.Rect(round(left + x * size), round(top + z * size),
                               max(1, round(size) + 1), max(1, round(size) + 1))
            color = wall if is_wall else floor
            if (x, z) not in maze.revealed_cells:
                color = fog
            pygame.draw.rect(target, color, tile)

    for index, cell in enumerate(maze.blueprint.keys):
        if index not in maze.keys_found and cell in maze.revealed_cells:
            _map_marker(target, cell, left, top, size, config.SELECTED)
    if maze.blueprint.exit in maze.revealed_cells:
        exit_color = config.CORRECT if maze.exit_unlocked else config.INCORRECT
        _map_marker(target, maze.blueprint.exit, left, top, size, exit_color)
    player_cell = (maze.player_x / 2, maze.player_z / 2)
    point = (round(left + player_cell[0] * size),
             round(top + player_cell[1] * size))
    pygame.draw.circle(target, config.ACCENT_SOFT, point, max(4, round(size * .3)))
    direction = (point[0] + round(sin(maze.yaw) * size * .42),
                 point[1] + round(cos(maze.yaw) * size * .42))
    pygame.draw.line(target, config.TEXT_DARK, point, direction, 2)


def draw_explored_map(target, maze, rect, *, mode="dark"):
    """Draw only the explored map inside the redesigned compact inspector."""
    rect = pygame.Rect(rect)
    colors = palette(mode)
    pygame.draw.rect(target, colors["SURFACE_2"], rect, border_radius=4)
    pygame.draw.rect(target, colors["BORDER"], rect, 1, border_radius=4)
    size = min((rect.width - 12) / maze.blueprint.size,
               (rect.height - 12) / maze.blueprint.size)
    map_width = round(size * maze.blueprint.size)
    left = rect.centerx - map_width // 2
    top = rect.centery - map_width // 2
    for z, row in enumerate(maze.blueprint.cells):
        for x, is_wall in enumerate(row):
            tile = pygame.Rect(round(left + x * size), round(top + z * size),
                               max(1, round(size) + 1), max(1, round(size) + 1))
            color = colors["TEXT_MUTED"] if is_wall else colors["SURFACE_1"]
            if (x, z) not in maze.revealed_cells:
                color = colors["SURFACE_3"]
            pygame.draw.rect(target, color, tile)
    for index, cell in enumerate(maze.blueprint.keys):
        if index not in maze.keys_found and cell in maze.revealed_cells:
            _map_marker(target, cell, left, top, size, colors["WARNING"])
    if maze.blueprint.exit in maze.revealed_cells:
        _map_marker(target, maze.blueprint.exit, left, top, size,
                    colors["SUCCESS"] if maze.exit_unlocked else colors["ERROR"])
    player_cell = (maze.player_x / 2, maze.player_z / 2)
    point = (round(left + (player_cell[0] + .5) * size),
             round(top + (player_cell[1] + .5) * size))
    pygame.draw.circle(target, colors["ACCENT"], point, max(3, round(size * .3)))


def _stat(target, rect, label, value, font, config):
    _card(target, rect, config.NOTE_BG, border=config.CARD_BORDER)
    _text(target, label, (rect.x + 12, rect.y + 9), font,
          config.TEXT_SECONDARY)
    _text(target, value, (rect.x + 12, rect.y + 32), font,
          config.TEXT_DARK)


def _format_time(seconds):
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    return f'{minutes:02d}:{seconds:02d}' if minutes < 100 else f'{minutes}:{seconds:02d}'


def _map_marker(target, cell, left, top, size, color):
    x, z = cell
    center = (round(left + (x + .5) * size), round(top + (z + .5) * size))
    pygame.draw.circle(target, color, center, max(3, round(size * .28)))


def _crosshair(target, viewport):
    center = viewport.center
    color = (226, 231, 229)
    pygame.draw.line(target, color, (center[0] - 7, center[1]),
                     (center[0] + 7, center[1]), 1)
    pygame.draw.line(target, color, (center[0], center[1] - 7),
                     (center[0], center[1] + 7), 1)


def _wrap(target, text, x, y, width, font, color):
    words, lines, line = text.split(), [], ''
    for word in words:
        candidate = word if not line else line + ' ' + word
        if font.size(candidate)[0] <= width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    for line in lines:
        target.blit(font.render(line, True, color), (x, y))
        y += font.get_linesize() + 2


def _pill(target, rect, label, fill, color, font):
    rect = pygame.Rect(rect)
    pygame.draw.rect(target, fill, rect, border_radius=9)
    pygame.draw.rect(target, config.CARD_BORDER, rect, 1, border_radius=9)
    _text(target, label, rect.center, font, color, center=True)


def _card(target, rect, fill, border=None):
    pygame.draw.rect(target, fill, rect, border_radius=12)
    if border is not None:
        pygame.draw.rect(target, border, rect, 1, border_radius=12)


def _text(target, text, position, font, color, center=False, center_y=False,
          right=False):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = position
    elif center_y:
        rect.midleft = position
    elif right:
        rect.midright = position
    else:
        rect.topleft = position
    target.blit(image, rect)
