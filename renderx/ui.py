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

    def draw(self, surface, scene, mesh, fps):
        left = config.VIEW_WIDTH + 20
        pygame.draw.rect(surface, config.PANEL,
                         (config.VIEW_WIDTH, 0, config.PANEL_WIDTH, config.HEIGHT))

        def label(text, y, font=None, color=config.TEXT):
            surface.blit((font or self.small).render(text, True, color), (left, y))

        label("RenderX", 24, self.title)
        label("3D WIREFRAME EXPLORER", 64, color=config.ACCENT)
        for action, rectangle in self.buttons.items():
            active = action == scene.shape
            pygame.draw.rect(surface, (36, 62, 70) if active else (32, 44, 62),
                             rectangle, border_radius=6)
            if active:
                pygame.draw.rect(surface, config.ACCENT, rectangle, 1, 6)
            text = self.normal.render(action, True, config.TEXT)
            surface.blit(text, text.get_rect(center=rectangle.center))
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
        surface.blit(self.small.render(f"{fps:.0f} FPS  |  Drag to explore", True,
                                       config.MUTED), (24, config.HEIGHT - 30))
