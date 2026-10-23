"""Interactive, skippable first-run tour for new users."""
from typing import Callable, List, Tuple
import pygame

from renderx.services.settings import settings_service
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
from renderx.ui.layout import Rect
from renderx.ui.widgets import Button, Card


TOUR_SLIDES: List[Tuple[str, List[str]]] = [
    (
        "Welcome to RenderX",
        [
            "RenderX is a complete 3D wireframe graphics engine, game, and learning laboratory.",
            "",
            "Three Pillars, One Launcher:",
            "• PLAY: 'RenderX: Depths' — a real-time 3D wireframe dungeon crawler with shooting and progression.",
            "• EXPLORE: Sandbox 3D viewer supporting 17 geometric shapes, transformations, and OBJ import.",
            "• LEARN: Interactive laboratory featuring live pipeline inspection, lessons, and quizzes.",
            "",
            "Every single line on screen is calculated by readable Python mathematics."
        ],
    ),
    (
        "Play: RenderX: Depths",
        [
            "Enter procedural subterranean mazes, battle wireframe guardians, and survive as deep as you can.",
            "",
            "Controls & Mechanics:",
            "• Movement: W/A/S/D to walk and strafe. Mouse look to aim.",
            "• Fire: Left Click or Space to fire your equipped weapon.",
            "• Weapons: 1 (Pulse Pistol), 2 (Scatter Burst), 3 (Arc Launcher).",
            "• Objectives: Find the security key on each floor, unlock the exit, and descend.",
            "• Living Engine: Press F8 during gameplay for the Engine X-Ray diagnostic overlay!"
        ],
    ),
    (
        "Explore: 3D Model Sandbox",
        [
            "Experiment with 3D transformations, projections, and camera views.",
            "",
            "Features:",
            "• 17 built-in procedural polyhedra, curves, and animated signal waves.",
            "• Drag to rotate, pan, or zoom geometry in real-time.",
            "• Press P to toggle between Perspective and Orthographic projection.",
            "• Press O to load Wavefront OBJ 3D models with strict safety checks.",
            "• Press F12 to capture high-resolution timestamped screenshots."
        ],
    ),
    (
        "Learn: Interactive Laboratory",
        [
            "Demystify how 3D computer graphics really work beneath the surface.",
            "",
            "Educational Modules:",
            "• How It Works: 8-stage transformation pipeline tracing coordinates from model to screen pixel.",
            "• Compare Views: Side-by-side Perspective vs Orthographic live comparison.",
            "• Shape Details: Euler characteristics, bounds, and topology inspector.",
            "• Lessons & Quiz: 18 interactive guided lessons and a 14-question testing bank."
        ],
    ),
]


class TourScreen:
    """Multi-slide educational tour walking new users through RenderX."""

    def __init__(self, on_finish: Callable[[], None]):
        self.on_finish = on_finish
        self.current_slide: int = 0
        self.buttons: List[Button] = []

    def layout(self, screen_w: int, screen_h: int) -> None:
        self.buttons.clear()
        content_w = min(720, screen_w - 40)
        card_h = min(460, screen_h - 100)
        card_x = (screen_w - content_w) // 2
        card_y = (screen_h - card_h) // 2

        btn_y = card_y + card_h - 52
        btn_w = 110

        # Skip / Finish button
        self.btn_skip = Button(
            Rect(card_x + SPACE_MD, btn_y, 120, 36),
            "Finish Tour" if self.current_slide == len(TOUR_SLIDES) - 1 else "Skip Tour",
            on_click=self._finish,
            font_size=FONT_SM,
        )
        self.buttons.append(self.btn_skip)

        # Previous button
        if self.current_slide > 0:
            self.btn_prev = Button(
                Rect(card_x + content_w - 2 * btn_w - SPACE_MD - 8, btn_y, btn_w, 36),
                "← Prev",
                on_click=self._prev_slide,
                font_size=FONT_SM,
            )
            self.buttons.append(self.btn_prev)

        # Next button
        if self.current_slide < len(TOUR_SLIDES) - 1:
            self.btn_next = Button(
                Rect(card_x + content_w - btn_w - SPACE_MD, btn_y, btn_w, 36),
                "Next →",
                on_click=self._next_slide,
                font_size=FONT_SM,
                accent=True,
            )
            self.buttons.append(self.btn_next)
        else:
            self.btn_start = Button(
                Rect(card_x + content_w - 140 - SPACE_MD, btn_y, 140, 36),
                "Start Playing →",
                on_click=self._finish,
                font_size=FONT_SM,
                accent=True,
            )
            self.buttons.append(self.btn_start)

    def _next_slide(self) -> None:
        if self.current_slide < len(TOUR_SLIDES) - 1:
            self.current_slide += 1
            sw, sh = pygame.display.get_surface().get_size()
            self.layout(sw, sh)

    def _prev_slide(self) -> None:
        if self.current_slide > 0:
            self.current_slide -= 1
            sw, sh = pygame.display.get_surface().get_size()
            self.layout(sw, sh)

    def _finish(self) -> None:
        settings_service.current.first_run_tour_completed = True
        settings_service.save()
        self.on_finish()

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._finish()
                return True
            elif event.key in (pygame.K_RIGHT, pygame.K_SPACE):
                if self.current_slide < len(TOUR_SLIDES) - 1:
                    self._next_slide()
                else:
                    self._finish()
                return True
            elif event.key == pygame.K_LEFT:
                self._prev_slide()
                return True

        for b in self.buttons:
            if b.handle_event(event):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        sw, sh = surface.get_size()
        surface.fill(thm.background)

        content_w = min(720, sw - 40)
        card_h = min(460, sh - 100)
        card_x = (sw - content_w) // 2
        card_y = (sh - card_h) // 2

        title, body_lines = TOUR_SLIDES[self.current_slide]

        card = Card(
            Rect(card_x, card_y, content_w, card_h),
            f"Step {self.current_slide + 1} of {len(TOUR_SLIDES)}: {title}",
        )
        card.draw(surface)

        font_sm = get_font(FONT_SM)
        y = card_y + 54
        for line in body_lines:
            if not line:
                y += 8
                continue
            is_header = line.isupper() or line.startswith("•") or line.endswith(":")
            f = get_font(FONT_SM, bold=is_header)
            col = thm.accent if is_header else thm.text
            img = f.render(line, True, col)
            surface.blit(img, (card_x + SPACE_MD, y))
            y += img.get_height() + 4

        for b in self.buttons:
            b.draw(surface)
