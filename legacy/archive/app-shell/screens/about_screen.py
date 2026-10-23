"""About & Information screen for RenderX."""
from typing import Callable
import pygame

from renderx.ui.theme import (
    current_theme,
    get_font,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_BODY,
    FONT_SM,
    SPACE_MD,
    SPACE_LG,
)
from renderx.ui.layout import Rect, Column, Align
from renderx.ui.widgets import Button, Card, Label


class AboutScreen:
    """Displays project mission, developer attribution, controls summary, and design principles."""

    def __init__(self, on_back: Callable[[], None]):
        self.on_back = on_back
        self.btn_back: Button | None = None

    def layout(self, screen_w: int, screen_h: int) -> None:
        content_w = min(760, screen_w - 40)
        start_x = (screen_w - content_w) // 2
        self.btn_back = Button(
            Rect(start_x, 30, 100, 36),
            "← Back",
            on_click=self.on_back,
            font_size=FONT_SM,
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()
            return True
        if self.btn_back and self.btn_back.handle_event(event):
            return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        sw, sh = surface.get_size()
        surface.fill(thm.background)

        content_w = min(760, sw - 40)
        start_x = (sw - content_w) // 2

        if self.btn_back:
            self.btn_back.draw(surface)

        font_title = get_font(FONT_TITLE, bold=True)
        title_lbl = font_title.render("About RenderX", True, thm.accent)
        surface.blit(title_lbl, (sw // 2 - title_lbl.get_width() // 2, 32))

        # Main Info Card
        card_rect = Rect(start_x, 80, content_w, sh - 110)
        card = Card(card_rect, "Product Mission & Architecture")
        card.draw(surface)

        font_b = get_font(FONT_BODY)
        font_sm = get_font(FONT_SM)

        y = card_rect.y + 48
        texts = [
            ("RenderX is a 3D wireframe graphics engine you can play, explore, and learn from.", True),
            ("Every line rendered on screen is generated from hand-written, readable Python mathematics.", False),
            ("Developed by Harsh Mahashabde (student developer).", True),
            ("", False),
            ("THREE PILLARS:", True),
            ("1. Play: 'RenderX: Depths' — A first-person wireframe dungeon crawler with shooting & RPG progression.", False),
            ("2. Explore: 3D model sandbox with 17 procedural shapes, OBJ loading, and transformation inspection.", False),
            ("3. Learn: The Learning Laboratory with an 8-stage pipeline inspector, 18 lessons, and quiz.", False),
            ("", False),
            ("CORE DESIGN RULES:", True),
            ("• Pure Python linear algebra core with zero external 3D engines or GPU shaders.", False),
            ("• Pygame handles only the window, 2D line primitives, audio mixing, and input.", False),
            ("• Optional NumPy fast path for vectorized vertex transformations with pure-Python reference.", False),
            ("• Guaranteed solvable procedural dungeon generation validated via Breadth-First Search.", False),
        ]

        for line, is_bold in texts:
            if not line:
                y += 10
                continue
            f = get_font(FONT_SM, bold=is_bold)
            col = thm.accent if is_bold else thm.text
            img = f.render(line, True, col)
            surface.blit(img, (start_x + SPACE_MD, y))
            y += img.get_height() + 4
