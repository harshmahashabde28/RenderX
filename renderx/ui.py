"""A fixed control panel: fonts are created once, then reused each frame."""
from math import degrees
import pygame
from renderx import config


class Panel:
    def __init__(self):
        self.message = ""
        self.message_until = 0
        self.small = pygame.font.Font(None, 21)
        self.normal = pygame.font.Font(None, 25)
        self.title = pygame.font.Font(None, 38)
        left = config.VIEW_WIDTH + 20
        self.buttons = {
            "Cube": pygame.Rect(left, 107, 124, 36),
            "Pyramid": pygame.Rect(left + 136, 107, 124, 36),
            "Rectangular prism": pygame.Rect(left, 151, 260, 36),
            "Reset": pygame.Rect(left, 668, 124, 40),
            "Exit": pygame.Rect(left + 136, 668, 124, 40),
        }

    def notify(self, message):
        self.message = message
        self.message_until = pygame.time.get_ticks() + 6000
        print(message)  # Full paths/errors remain readable in the terminal.

    def hit_test(self, position):
        for action, rectangle in self.buttons.items():
            if rectangle.collidepoint(position):
                return action
        return None

    def draw_buttons(self, surface, scene):
        for action, rectangle in self.buttons.items():
            active = action == scene.shape
            pygame.draw.rect(surface, (36, 62, 70) if active else (32, 44, 62),
                             rectangle, border_radius=6)
            if active:
                pygame.draw.rect(surface, config.ACCENT, rectangle, 1, 6)
            text = self.normal.render(action, True, config.TEXT)
            surface.blit(text, text.get_rect(center=rectangle.center))

    def draw(self, surface, scene, mesh, fps, learning=None, snapshots=None):
        if snapshots is not None:
            self.draw_pipeline(surface, scene, mesh, learning, snapshots)
            self.draw_overlay(surface, scene, fps, learning)
            return
        left = config.VIEW_WIDTH + 20
        pygame.draw.rect(surface, config.PANEL,
                         (config.VIEW_WIDTH, 0, config.PANEL_WIDTH, config.HEIGHT))

        def label(text, y, font=None, color=config.TEXT):
            surface.blit((font or self.small).render(text, True, color), (left, y))

        label("RenderX", 24, self.title)
        label("LEARNING LABORATORY", 64, color=config.ACCENT)
        self.draw_buttons(surface, scene)
        label(f"{len(mesh.vertices)} vertices / {len(mesh.edges)} edges", 205)
        label("TRANSFORM", 245, color=config.ACCENT)
        angles = tuple(round(degrees(angle)) % 360 for angle in scene.angles)
        label(f"Rotation   X {angles[0]}   Y {angles[1]}   Z {angles[2]}", 272)
        x, y, z = scene.position
        label(f"Position   {x:+.2f}, {y:+.2f}, {z:.2f}", 297)
        label(f"Scale   {scene.scale:.2f}x", 322)
        label("KEYBOARD", 361, color=config.ACCENT)
        for i, text in enumerate([
            "Arrows: rotate X / Y    Q / E: Z",
            "W A S D: move up / left / down / right",
            "Page Up / Down: nearer / farther",
            "+ / -: scale    1/2/3: shape    O: OBJ",
            "R: reset    Esc: exit",
        ]):
            label(text, 389 + i * 23)
        label("MOUSE", 519, color=config.ACCENT)
        for i, text in enumerate([
            "Left drag: rotate X / Y",
            "Right drag: rotate Z",
            "Shift + left / middle drag: move",
            "Scroll: scale    Buttons: select / reset",
        ]):
            label(text, 547 + i * 23)
        label("P: projection   X: axes   F12: PNG", 642, color=config.ACCENT)
        self.draw_overlay(surface, scene, fps, learning)

    def draw_pipeline(self, surface, scene, mesh, learning, snapshots):
        left = config.VIEW_WIDTH + 20
        pygame.draw.rect(surface, config.PANEL,
                         (config.VIEW_WIDTH, 0, config.INSPECTOR_WIDTH, config.HEIGHT))

        def label(text, x, y, font=None, color=config.TEXT):
            surface.blit((font or self.small).render(text, True, color), (x, y))

        label("Pipeline Inspector", left, 24, self.title)
        label("LEARNING LABORATORY / CHECKPOINT 3", left, 64,
              color=config.ACCENT)
        self.draw_buttons(surface, scene)
        label(f"VERTEX {learning.selected_vertex}", left + 280, 110,
              self.normal, config.SELECTED)
        label(f"{len(mesh.vertices)} vertices / {len(mesh.edges)} edges",
              left + 280, 140)
        label("Indices start at zero", left + 280, 166, color=config.MUTED)
        label("COORDINATE SEQUENCE", left, 207, color=config.ACCENT)
        label("World units; final row in pixels", left + 250, 207,
              color=config.MUTED)
        for index, stage in enumerate(snapshots):
            y = 235 + index * 34
            active = index == learning.stage_index
            if active:
                pygame.draw.rect(surface, (44, 54, 61),
                                 (left - 8, y - 5, 496, 31), border_radius=4)
            color = config.SELECTED if active else config.TEXT
            label(stage.name, left, y, color=color)
            if stage.coordinates is None:
                value = "Not projected"
            else:
                value = "(" + ", ".join(f"{v:.3f}" for v in stage.coordinates) + ")"
                # Near-plane projections may be large; retain meaningful digits.
                if self.small.size(value)[0] > 238:
                    value = "(" + ", ".join(f"{v:.3g}" for v in stage.coordinates) + ")"
            label(value, left + 250, y, color=color)
        active = snapshots[learning.stage_index]
        label(f"STAGE {learning.stage_index + 1}/8 - FORMULA", left, 514,
              color=config.SELECTED)
        for index, formula in enumerate(active.formula):
            label(formula, left, 540 + index * 21)
        words = active.explanation.split()
        lines = [""]
        for word in words:
            candidate = (lines[-1] + " " + word).strip()
            if self.small.size(candidate)[0] > 480:
                lines.append(word)
            else:
                lines[-1] = candidate
        for index, line in enumerate(lines):
            label(line, left, 611 + index * 20, color=config.MUTED)
        label("R: reset   P: projection", left + 280, 673)
        label("X: axes   O: OBJ   F12: PNG", left + 280, 696)
        label(", / .  vertex     [ / ]  stage     Tab  Explore", left, 719,
              color=config.ACCENT)

    def draw_overlay(self, surface, scene, fps, learning):
        if self.message and pygame.time.get_ticks() < self.message_until:
            text = self.message
            while self.small.size(text)[0] > config.VIEW_WIDTH - 48:
                text = text[:-4] + "..."
            background = pygame.Rect(16, config.HEIGHT - 64, config.VIEW_WIDTH - 32, 27)
            pygame.draw.rect(surface, config.PANEL, background, border_radius=4)
            surface.blit(self.small.render(text, True, config.TEXT),
                         (24, config.HEIGHT - 59))
        surface.blit(self.normal.render(scene.shape.upper(), True, config.TEXT),
                     (24, 23))
        surface.blit(self.small.render(f"{scene.projection}  /  Axes: {'on' if scene.axes_visible else 'off'} (X)", True,
                                       config.MUTED), (24, 52))
        mode = learning.mode if learning is not None else "Explore"
        surface.blit(self.small.render(f"{mode} Mode  |  Tab: switch mode", True,
                                       config.ACCENT), (24, 77))
        if mode == "Pipeline":
            angles = ", ".join(f"{degrees(a):.1f}" for a in scene.angles)
            position = ", ".join(f"{v:.2f}" for v in scene.position)
            for index, text in enumerate([
                f"Rotation XYZ (degrees): {angles}",
                f"Position: ({position})   Scale: {scene.scale:.2f}",
                "Gold marker: selected vertex's final screen position",
            ]):
                surface.blit(self.small.render(text, True, config.MUTED),
                             (24, 105 + index * 23))
            footer = "Arrows/Q/E: rotate | WASD: pan | PgUp/Dn: depth | +/-: scale | Esc: exit"
        else:
            footer = "Drag to explore | Tab: Pipeline Inspector"
        surface.blit(self.small.render(f"{fps:.0f} FPS  |  {footer}", True,
                                       config.MUTED), (24, config.HEIGHT - 30))
