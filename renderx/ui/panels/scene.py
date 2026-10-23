"""Scene/object dock with a scrollable model catalog and sample import."""

import pygame

from .. import fonts, theme
from ..components import draw_button, draw_section
from .common import draw_panel


class ScenePanel:
    def __init__(self):
        self.scroll = 0
        self.list_rect = pygame.Rect(0, 0, 0, 0)
        self.objects_open = True

    def scroll_by(self, delta, models):
        rows = max(0, len(models) - self.visible_rows)
        self.scroll = max(0, min(rows, self.scroll + int(delta)))

    @property
    def visible_rows(self):
        return max(1, self.list_rect.height // theme.METRICS["row_height"])

    def draw(self, surface, rect, models, scene, ui, *, mode="dark",
             collapsed=False, destination="Explore", quest=None, maze=None):
        rect = pygame.Rect(rect)
        colors = theme.palette(mode)
        draw_panel(surface, rect, mode)
        padding = theme.SPACE["md"]
        if collapsed:
            size = theme.METRICS["icon_medium"]
            action_rect = pygame.Rect(rect.centerx - theme.METRICS["hit_target"] // 2,
                                      rect.y + padding,
                                      theme.METRICS["hit_target"],
                                      theme.METRICS["hit_target"])
            ui.button(("dock", "left"), "Expand scene dock", action_rect)
            ui.paint_button(surface, ("dock", "left"), mode=mode,
                            icon="panel-left-open", align="center")
            return

        top = rect.y + padding
        fonts.draw_text(surface, "SCENE", (rect.x + padding, top), "hint",
                        colors["TEXT_MUTED"], bold=True)
        collapse_rect = pygame.Rect(rect.right - padding - theme.METRICS["hit_target"],
                                    top - theme.SPACE["xs"],
                                    theme.METRICS["hit_target"],
                                    theme.METRICS["hit_target"])
        ui.button(("dock_collapse", "left"), "Collapse scene dock", collapse_rect)
        ui.paint_button(surface, ("dock_collapse", "left"), mode=mode,
                        icon="panel-left-close", align="center")
        if destination == "Explore":
            count = len(models)
            section_rect = pygame.Rect(rect.x + padding, top + theme.METRICS["section_height"],
                                       rect.width - padding * 2, theme.METRICS["section_height"])
            draw_section(surface, section_rect, "OBJECTS", mode=mode,
                         expanded=self.objects_open, count=count)
            ui.button(("section", "objects"), "Objects", section_rect)
            self.list_rect = pygame.Rect(
                rect.x + padding, section_rect.bottom + theme.SPACE["xs"],
                rect.width - padding * 2,
                max(0, rect.bottom - theme.METRICS["control_height"] -
                    theme.METRICS["section_height"] - section_rect.bottom - theme.SPACE["lg"]),
            )
            if self.objects_open and self.list_rect.height > 0:
                old_clip = surface.get_clip()
                surface.set_clip(old_clip.clip(self.list_rect))
                row_height = theme.METRICS["row_height"]
                names = list(models)
                self.scroll = max(0, min(max(0, len(names) - self.visible_rows), self.scroll))
                for index in range(self.scroll,
                                   min(len(names), self.scroll + self.visible_rows + 1)):
                    name = names[index]
                    row = pygame.Rect(self.list_rect.x,
                                      self.list_rect.y + (index - self.scroll) * row_height,
                                      self.list_rect.width - theme.METRICS["scrollbar_width"] -
                                      theme.SPACE["xs"], row_height)
                    action = ("shape", name)
                    state = "active" if scene.shape == name else "default"
                    ui.button(action, name, row, active=state == "active")
                    ui.paint_button(surface, action, mode=mode, state=state,
                                    icon=f"shape:{name}", align="left")
                surface.set_clip(old_clip)
                if len(names) > self.visible_rows:
                    track = pygame.Rect(
                        self.list_rect.right - theme.METRICS["scrollbar_width"],
                        self.list_rect.y, theme.METRICS["scrollbar_width"],
                        self.list_rect.height)
                    pygame.draw.rect(surface, colors["SURFACE_2"], track)
                    thumb_height = max(
                        theme.METRICS["scrollbar_min_thumb"],
                        round(track.height * self.visible_rows / len(names)))
                    travel = max(0, track.height - thumb_height)
                    maximum = max(1, len(names) - self.visible_rows)
                    thumb_y = track.y + round(travel * self.scroll / maximum)
                    pygame.draw.rect(surface, colors["TEXT_DIM"],
                                     pygame.Rect(track.x, thumb_y, track.width,
                                                 thumb_height))
            import_rect = pygame.Rect(rect.x + padding, rect.bottom - padding -
                                      theme.METRICS["control_height"],
                                      rect.width - padding * 2,
                                      theme.METRICS["control_height"])
            ui.button(("load_sample",), "Load sample OBJ", import_rect)
            ui.paint_button(surface, ("load_sample",), mode=mode,
                            icon="folder", shortcut="O", align="left")
        elif destination == "Challenges" and quest is not None:
            self._draw_challenges(surface, rect, quest, mode)
        elif destination == "Maze" and maze is not None:
            self._draw_maze_summary(surface, rect, maze, mode)
        else:
            self._draw_shooter_summary(surface, rect, mode)

    def _draw_challenges(self, surface, rect, quest, mode):
        colors = theme.palette(mode)
        x = rect.x + theme.SPACE["md"]
        y = rect.y + theme.METRICS["topbar_height"]
        fonts.draw_text(surface, "PROJECTION CHALLENGES", (x, y), "hint",
                        colors["TEXT_MUTED"], bold=True)
        y += theme.METRICS["section_height"]
        from renderx.quest import CHALLENGES
        row_height = theme.METRICS["row_height"] + theme.SPACE["xs"]
        for index, challenge in enumerate(CHALLENGES):
            state = ("active" if index == quest.current and not quest.done else
                     "default")
            label = f"{index + 1:02d}  {challenge.title}"
            colors_row = colors["ACCENT"] if state == "active" else colors["BORDER"]
            pygame.draw.line(surface, colors_row, (x, y),
                             (rect.right - theme.SPACE["md"], y),
                             theme.METRICS["border"])
            fonts.draw_text(surface, label, (x, y + theme.SPACE["sm"]),
                            "control", colors["TEXT"] if state == "active" else colors["TEXT_MUTED"],
                            max_width=rect.width - theme.SPACE["lg"])
            fonts.draw_text(surface, "Complete" if index < quest.current else
                            "Current" if index == quest.current and not quest.done else
                            "Locked", (x, y + theme.METRICS["row_height"]),
                            "micro", colors["TEXT_DIM"])
            y += row_height + theme.SPACE["sm"]
        fonts.draw_wrapped(surface, "Each step demonstrates a different renderer behavior.",
                            (x, y + theme.SPACE["lg"]), rect.width - theme.SPACE["xl"],
                            "hint", colors["TEXT_MUTED"])

    def _draw_maze_summary(self, surface, rect, maze, mode):
        colors = theme.palette(mode)
        x = rect.x + theme.SPACE["md"]
        y = rect.y + theme.METRICS["topbar_height"]
        fonts.draw_text(surface, "SIGNAL RECOVERY", (x, y), "hint",
                        colors["TEXT_MUTED"], bold=True)
        y += theme.METRICS["section_height"]
        for label, value in (("Stage", f"{maze.level} / 3"),
                             ("Keys", f"{len(maze.keys_found)} / 2"),
                             ("Exit", "Open" if maze.exit_unlocked else "Locked"),
                             ("Elapsed", f"{int(maze.elapsed)} s")):
            fonts.draw_text(surface, label, (x, y), "hint", colors["TEXT_MUTED"])
            fonts.draw_text(surface, value, (rect.right - theme.SPACE["md"], y),
                            "value", colors["TEXT"], anchor="topright")
            y += theme.METRICS["row_height"]

    def _draw_shooter_summary(self, surface, rect, mode):
        colors = theme.palette(mode)
        x = rect.x + theme.SPACE["md"]
        y = rect.y + theme.METRICS["topbar_height"]
        fonts.draw_text(surface, "PREVIEW OBJECT", (x, y), "hint",
                        colors["TEXT_MUTED"], bold=True)
        y += theme.METRICS["section_height"]
        fonts.draw_text(surface, "Torus", (x, y), "section",
                        colors["TEXT"], bold=True)
        y += theme.METRICS["row_height"]
        fonts.draw_text(surface, "Wireframe scene", (x, y), "hint",
                        colors["TEXT_MUTED"])
