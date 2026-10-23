"""Small drawing helpers for Projection Quest's three interactive challenges."""

import pygame

from renderx import config
from renderx.axes import draw_axes
from renderx.comparison import COMPARE_FOCAL_LENGTH, projected_bounds
from renderx.quest import CHALLENGES, alignment_progress
from renderx.renderer import draw_wireframe
from renderx.scene import Scene
from renderx.transform import transform_vertex
from renderx.ui.fonts import clear_cache as clear_ui_font_cache
from renderx.ui.fonts import font as local_font


def draw_comparison_challenge(target, mesh, scene, camera, viewport, font):
    """Render the same live scene through both projections side by side."""
    viewport = pygame.Rect(viewport)
    gutter = 12
    pane_width = (viewport.width - gutter) // 2
    panes = (
        ("Perspective", pygame.Rect(viewport.x, viewport.y, pane_width, viewport.height)),
        ("Orthographic", pygame.Rect(viewport.x + pane_width + gutter, viewport.y,
                                      pane_width, viewport.height)),
    )
    world_points = [transform_vertex(point, scene) for point in mesh.vertices]
    results = {}
    for mode, pane in panes:
        draw_wireframe(target, mesh, scene, camera, viewport=pane,
                       projection=mode, focal_length=COMPARE_FOCAL_LENGTH)
        if scene.axes_visible:
            draw_axes(target, camera, mode, font, viewport=pane,
                      focal_length=COMPARE_FOCAL_LENGTH)
        bounds = projected_bounds(world_points, mesh.edges, camera, mode,
                                  pane.center, COMPARE_FOCAL_LENGTH)
        width = 0.0 if bounds is None else bounds[2] - bounds[0]
        height = 0.0 if bounds is None else bounds[3] - bounds[1]
        results[mode] = (width, height)

        heading = pygame.Rect(pane.x + 10, pane.y + 10, pane.width - 20, 32)
        pygame.draw.rect(target, config.PANEL, heading, border_radius=7)
        _text(target, mode.upper(), (heading.centerx, heading.centery), font,
              config.TEXT, center=True)
        note = pygame.Rect(pane.x + 10, pane.bottom - 38, pane.width - 20, 28)
        pygame.draw.rect(target, config.PANEL, note, border_radius=7)
        _text(target, f"Projected width  {width:.0f}px", (note.centerx, note.centery),
              font, config.TEXT, center=True)
        pygame.draw.rect(target, config.CARD_BORDER, pane, 1)
    return results


def draw_near_plane_guide(target, viewport, scene):
    """Show an on-canvas depth ruler with the actual near-plane position marked."""
    viewport = pygame.Rect(viewport)
    ruler = pygame.Rect(viewport.x + 22, viewport.bottom - 52,
                        viewport.width - 44, 42)
    pygame.draw.rect(target, config.PANEL, ruler, border_radius=8)
    line_y = ruler.y + 27
    left, right = ruler.x + 12, ruler.right - 12
    pygame.draw.line(target, config.MUTED, (left, line_y), (right, line_y), 2)
    span = max(config.MAX_DEPTH, 8.0)
    near_x = round(left + (config.NEAR_DEPTH / span) * (right - left))
    model_x = round(left + max(0.0, min(scene.position[2], span)) / span *
                    (right - left))
    pygame.draw.line(target, config.INCORRECT, (near_x, line_y - 8),
                     (near_x, line_y + 7), 2)
    pygame.draw.circle(target, config.ACCENT_SOFT, (model_x, line_y), 5)
    font = _font(16)
    _text(target, 'CAMERA', (left, ruler.y + 4), font, config.MUTED)
    _text(target, f'NEAR PLANE  {config.NEAR_DEPTH:.1f}', (left + 76, ruler.y + 4),
          font, (235, 165, 160))
    _text(target, f'MODEL CENTRE  z={scene.position[2]:.2f}',
          (right, ruler.y + 4), font, config.TEXT, right=True)


def draw_quest_card(target, quest, scene, mesh, camera, clipped_edges=0):
    """Draw the active challenge instructions, target, choices, and feedback."""
    panel = pygame.Rect(824, 100, 504, 550)
    _card(target, panel)
    if quest.done:
        draw_quest_complete(target)
        return

    challenge = quest.challenge
    inner_x = panel.x + 32
    _text(target, f'CHALLENGE  {quest.current + 1} / {len(CHALLENGES)}',
          (inner_x, panel.y + 30), _font(19), config.ACCENT_SOFT)
    _text(target, challenge.title, (inner_x, panel.y + 64), _font(34), config.TEXT_DARK)

    if challenge.kind == 'align':
        _draw_align_card(target, challenge, quest, scene, mesh, camera, inner_x)
    elif challenge.kind == 'choice':
        _draw_depth_card(target, challenge, quest, inner_x)
    else:
        _draw_clipping_card(target, challenge, quest, scene, clipped_edges, inner_x)


def _draw_align_card(target, challenge, quest, scene, mesh, camera, x):
    _draw_wrapped(target, challenge.task, x, 207, 440, _font(23), config.TEXT_SECONDARY)
    target_rect = pygame.Rect(x, 302, 212, 190)
    _text(target, 'TARGET VIEW', (target_rect.x, target_rect.y - 25), _font(19),
          config.TEXT_SECONDARY)
    _card(target, target_rect)
    inset = target_rect.inflate(-8, -8)
    target_scene = Scene(
        shape=challenge.setup_shape,
        angles=challenge.target_angles,
        position=(0.0, 0.0, challenge.setup_depth),
        projection=challenge.setup_projection,
        axes_visible=False,
    )
    draw_wireframe(target, mesh, target_scene, camera, viewport=inset,
                   focal_length=190)
    matched = quest.confirmed
    border = config.CORRECT if matched else config.CARD_BORDER
    pygame.draw.rect(target, border, target_rect, 2 if matched else 1)

    progress = alignment_progress(scene.angles, challenge.target_angles)
    status_x = x + 232
    _text(target, 'YOUR ALIGNMENT', (status_x, target_rect.y + 4), _font(19),
          config.TEXT_SECONDARY)
    bar = pygame.Rect(status_x, target_rect.y + 32, 196, 12)
    pygame.draw.rect(target, (234, 237, 235), bar, border_radius=6)
    fill = bar.copy()
    fill.width = round(bar.width * progress)
    if fill.width:
        pygame.draw.rect(target, config.CORRECT if matched else config.ACCENT_SOFT,
                         fill, border_radius=6)
    _text(target, f'{round(progress * 100)}% aligned',
          (status_x, target_rect.y + 56), _font(19), config.TEXT_DARK)
    if matched:
        _text(target, 'Matched!', (status_x, target_rect.y + 93), _font(27),
              config.CORRECT)
        _draw_wrapped(target, challenge.explanation, status_x, target_rect.y + 125,
                      196, _font(19), config.TEXT_SECONDARY)
    else:
        _draw_wrapped(target, 'Rotate each axis toward the target. The outline turns green when it matches.',
                      status_x, target_rect.y + 93, 196, _font(19),
                      config.TEXT_SECONDARY)


def _draw_depth_card(target, challenge, quest, x):
    _draw_wrapped(target, challenge.question, x, 220, 438, _font(23), config.TEXT_DARK)
    if not quest.depth_tested:
        note = pygame.Rect(x, 310, 440, 84)
        pygame.draw.rect(target, config.NOTE_BG, note, border_radius=10)
        _text(target, 'First, run the depth test', (x + 18, note.y + 16), _font(27),
              config.TEXT_DARK)
        _text(target, 'Move the cube farther away to reveal the choices.',
              (x + 18, note.y + 49), _font(19), config.TEXT_SECONDARY)
    if quest.last_answer_correct is False:
        _text(target, 'Not quite. Compare the two panes, then try again.',
              (x, 486), _font(19), config.INCORRECT)
    elif quest.confirmed:
        _draw_wrapped(target, challenge.explanation, x, 475, 438, _font(19),
                      config.CORRECT)


def _draw_clipping_card(target, challenge, quest, scene, clipped_edges, x):
    if not quest.clipping_seen:
        _draw_wrapped(target, challenge.task, x, 220, 438, _font(23), config.TEXT_DARK)
        note = pygame.Rect(x, 310, 440, 104)
        pygame.draw.rect(target, config.NOTE_BG, note, border_radius=10)
        _text(target, 'Move closer with Page Up', (x + 18, note.y + 17), _font(27),
              config.TEXT_DARK)
        _text(target, f'Object depth: {scene.position[2]:.2f}',
              (x + 18, note.y + 52), _font(19), config.TEXT_SECONDARY)
        _text(target, f'Edges crossing the near plane: {clipped_edges}',
              (x + 18, note.y + 76), _font(19),
              config.ACCENT_SOFT if clipped_edges else config.TEXT_SECONDARY)
    else:
        _draw_wrapped(target, challenge.question, x, 220, 438, _font(23), config.TEXT_DARK)
        _text(target, f'You observed {clipped_edges} clipped edge(s).',
              (x, 270), _font(19), config.ACCENT_SOFT)
        if quest.last_answer_correct is False:
            _text(target, 'Not quite. Watch where each edge reaches the near-plane guide.',
                  (x, 486), _font(19), config.INCORRECT)
        elif quest.confirmed:
            _draw_wrapped(target, challenge.explanation, x, 475, 438, _font(19),
                          config.CORRECT)


def draw_quest_complete(target):
    x = 856
    _text(target, 'QUEST COMPLETE', (x, 138), _font(19), config.CORRECT)
    _text(target, 'Done', (x, 176), _font(34), config.TEXT_DARK)
    pygame.draw.line(target, config.CARD_BORDER, (x, 220), (1296, 220), 1)
    _draw_wrapped(target, 'You explored wireframes, projection, and clipping.',
                  x, 252, 430, _font(23), config.TEXT_DARK)
    _draw_wrapped(target, 'You practiced alignment, projection, and clipping.',
                  x, 322, 430, _font(23), config.TEXT_SECONDARY)


def draw_quest_progress(target, quest, rect, hint):
    """Draw the quiet progress strip below the challenge canvas and card."""
    _card(target, rect)
    _text(target, 'Projection Quest', (rect.x + 20, rect.y + 20), _font(27),
          config.TEXT_DARK)
    _text(target, 'Alignment  ·  depth  ·  clipping',
          (rect.x + 20, rect.y + 49), _font(19), config.TEXT_SECONDARY)
    dot_y = rect.y + 36
    start_x = rect.x + 480
    for index in range(3):
        color = config.CORRECT if index < quest.current else (
            config.ACCENT_SOFT if index == quest.current and not quest.done
            else config.CARD_BORDER)
        pygame.draw.circle(target, color, (start_x + index * 34, dot_y), 8)
        if index < 2:
            pygame.draw.line(target, config.CARD_BORDER,
                             (start_x + index * 34 + 10, dot_y),
                             (start_x + (index + 1) * 34 - 10, dot_y), 2)
    _text(target, hint, (rect.x + 20, rect.y + 88), _font(19),
          config.TEXT_SECONDARY)


def _draw_wrapped(target, value, x, y, width, font, color, line_gap=5):
    words = str(value).split()
    rows, row = [], ''
    for word in words:
        candidate = word if not row else row + ' ' + word
        if font.size(candidate)[0] <= width or not row:
            row = candidate
        else:
            rows.append(row)
            row = word
    if row:
        rows.append(row)
    for line in rows:
        image = font.render(line, True, color)
        target.blit(image, (x, y))
        y += image.get_height() + line_gap
    return y


def _card(target, rect):
    pygame.draw.rect(target, config.CARD_BG, rect, border_radius=10)
    pygame.draw.rect(target, config.CARD_BORDER, rect, 1, border_radius=10)


def _text(target, value, position, font, color, center=False, right=False):
    image = font.render(str(value), True, color)
    rect = image.get_rect()
    if center:
        rect.center = position
    elif right:
        rect.midright = position
    else:
        rect.topleft = position
    target.blit(image, rect)


_FONTS = {}


def clear_font_cache():
    """Drop Pygame font objects before the app shuts Pygame down."""
    _FONTS.clear()


def _font(size):
    # Recover if the font module was shut down outside the app lifecycle.
    if not pygame.font.get_init():
        clear_font_cache()
        clear_ui_font_cache()
        pygame.font.init()
    if size not in _FONTS:
        _FONTS[size] = local_font("body", size)
    return _FONTS[size]
