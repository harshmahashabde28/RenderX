"""Compact controls and feedback for the existing projection challenges."""

import pygame

from renderx.quest import CHALLENGES, alignment_progress
from renderx.renderer import draw_wireframe
from renderx.scene import Scene

from .. import fonts, theme
from .common import draw_panel


def draw_challenge_panel(surface, rect, quest, scene, models, camera, ui,
                         clipped_edges=0, *, mode="dark"):
    rect = pygame.Rect(rect)
    colors = theme.palette(mode)
    draw_panel(surface, rect, mode)
    x = rect.x + theme.SPACE["md"]
    width = max(1, rect.width - theme.SPACE["lg"])
    y = rect.y + theme.SPACE["md"]
    fonts.draw_text(surface, "CHALLENGE", (x, y), "hint", colors["TEXT_MUTED"], bold=True)
    y += theme.METRICS["section_height"]
    if quest.done:
        fonts.draw_text(surface, "Projection complete", (x, y), "section", colors["TEXT"], bold=True)
        y += theme.METRICS["section_height"]
        fonts.draw_wrapped(surface, "You worked with orientation, depth, and near-plane clipping.",
                           (x, y), width, "body", colors["TEXT_MUTED"])
        button = pygame.Rect(x, rect.bottom - theme.SPACE["lg"] - theme.METRICS["control_height"],
                             width, theme.METRICS["control_height"])
        _button(surface, ui, ("quest_back",), "Back to Explore", button,
                mode, "active")
        return

    challenge = quest.challenge
    fonts.draw_text(surface, challenge.title, (x, y), "section", colors["TEXT"], bold=True,
                    max_width=width)
    y += theme.METRICS["section_height"]
    fonts.draw_wrapped(surface, challenge.task if challenge.kind != "choice" else challenge.question,
                       (x, y), width, "hint", colors["TEXT_MUTED"])
    y += theme.METRICS["row_height"] * 2
    fonts.draw_text(surface, f"STEP  {quest.current + 1} / {len(CHALLENGES)}",
                    (x, y), "status", colors["TEXT_MUTED"])
    y += theme.METRICS["hint_line"]

    if challenge.kind == "align":
        progress = alignment_progress(scene.angles, challenge.target_angles)
        _progress(surface, pygame.Rect(x, y, width, theme.SPACE["sm"]), progress,
                  colors["SUCCESS"] if quest.confirmed else colors["ACCENT"], colors)
        y += theme.METRICS["row_height"]
        fonts.draw_text(surface, f"{round(progress * 100)}% aligned",
                        (x, y), "value", colors["TEXT"])
        y += theme.METRICS["row_height"]
        preview_h = min(theme.METRICS["title_height"] * 3, max(1, rect.bottom - y - 170))
        preview = pygame.Rect(x, y, width, preview_h)
        pygame.draw.rect(surface, colors["VIEWPORT"], preview)
        pygame.draw.rect(surface, colors["BORDER"], preview, theme.METRICS["border"])
        target_scene = Scene(shape=challenge.setup_shape,
                             angles=challenge.target_angles,
                             position=(0.0, 0.0, challenge.setup_depth),
                             axes_visible=False)
        draw_wireframe(surface, models[challenge.setup_shape], target_scene, camera,
                       viewport=preview.inflate(-theme.SPACE["xs"], -theme.SPACE["xs"]),
                       focal_length=160)
        y = preview.bottom + theme.SPACE["sm"]
        fonts.draw_text(surface, "Rotation steps", (x, y), "micro", colors["TEXT_MUTED"])
        y += theme.METRICS["hint_line"]
        _axis_buttons(surface, ui, x, y, width, mode)
        y += theme.METRICS["row_height"] + theme.SPACE["sm"]
        if quest.confirmed:
            fonts.draw_wrapped(surface, challenge.explanation, (x, y), width,
                               "hint", colors["SUCCESS"])
            button = pygame.Rect(x, rect.bottom - theme.SPACE["lg"] -
                                 theme.METRICS["control_height"], width,
                                 theme.METRICS["control_height"])
            _button(surface, ui, ("quest_next",), "Next challenge", button,
                    mode, "active")
        return

    if challenge.kind == "choice":
        status = "Depth test complete" if quest.depth_tested else "Move farther to unlock choices"
    else:
        status = (f"{clipped_edges} edge(s) clipped" if quest.clipping_seen
                  else "Move closer to observe clipping")
    fonts.draw_wrapped(surface, status, (x, y), width, "hint",
                       colors["SUCCESS"] if (quest.depth_tested if challenge.kind == "choice"
                                              else quest.clipping_seen) else colors["WARNING"])
    y += theme.METRICS["row_height"] + theme.SPACE["xs"]
    half = (width - theme.SPACE["sm"]) // 2
    _button(surface, ui, ("quest_depth", -1), "Nearer",
            pygame.Rect(x, y, half, theme.METRICS["control_height"]), mode)
    _button(surface, ui, ("quest_depth", 1), "Farther",
            pygame.Rect(x + half + theme.SPACE["sm"], y, half,
                        theme.METRICS["control_height"]), mode)
    y += theme.METRICS["control_height"] + theme.SPACE["sm"]

    unlocked = (quest.depth_tested if challenge.kind == "choice" else quest.clipping_seen)
    if unlocked and challenge.choices:
        for index, choice in enumerate(challenge.choices):
            row = pygame.Rect(x, y, width, theme.METRICS["control_height"])
            state = "active" if quest.answer == index else "default"
            _button(surface, ui, ("quest_choice", index), choice, row, mode, state)
            y += theme.METRICS["control_height"] + theme.SPACE["xs"]
        if quest.last_answer_correct is False:
            fonts.draw_text(surface, "Try once more.", (x, y), "hint", colors["ERROR"])
            y += theme.METRICS["hint_line"]
        if quest.confirmed:
            fonts.draw_wrapped(surface, challenge.explanation, (x, y), width,
                               "micro", colors["SUCCESS"])
            y = max(y, rect.bottom - theme.METRICS["control_height"] - theme.SPACE["xl"])
        if quest.confirmed:
            action, label = ("quest_next", "Next challenge")
        else:
            action, label = ("quest_check", "Check answer")
        state = "active" if quest.confirmed or quest.answer is not None else "disabled"
        _button(surface, ui, (action,), label,
                pygame.Rect(x, rect.bottom - theme.SPACE["lg"] - theme.METRICS["control_height"],
                            width, theme.METRICS["control_height"]), mode, state)


def _axis_buttons(surface, ui, x, y, width, mode):
    gap = theme.SPACE["xs"]
    button_w = (width - gap * 2) // 3
    for axis, letter in enumerate("XYZ"):
        row_x = x + axis * (button_w + gap)
        for sign, suffix, offset in ((-1, "−", 0), (1, "+", button_w // 2)):
            rect = pygame.Rect(row_x + offset, y, button_w // 2, theme.METRICS["control_height"])
            _button(surface, ui, ("quest_rotate", axis, sign), letter + suffix,
                    rect, mode)


def _button(surface, ui, action, label, rect, mode, state="default"):
    ui.button(action, label, rect, active=state == "active")
    ui.paint_button(surface, action, mode=mode, state=state,
                    align="center")


def _progress(surface, rect, ratio, fill, colors):
    pygame.draw.rect(surface, colors["SURFACE_3"], rect)
    amount = rect.copy()
    amount.width = round(rect.width * max(0, min(1, ratio)))
    pygame.draw.rect(surface, fill, amount)
