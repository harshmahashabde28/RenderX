"""Main Menu launcher screen with plain-language options and keyboard/mouse navigation."""
from typing import Callable, Optional
import pygame

from renderx.ui.theme import (
    current_theme,
    get_font,
    FONT_HERO,
    FONT_SUBTITLE,
    FONT_BODY,
    FONT_SM,
    SPACE_MD,
    SPACE_LG,
)
from renderx.ui.layout import Rect, Column, Align
from renderx.ui.widgets import Button


class MainMenuScreen:
    """Launcher screen presenting Play, Explore, Learn, Settings, About, and Tour."""

    def __init__(
        self,
        on_navigate: Callable[[str], None],
        on_quit: Callable[[], None],
    ):
        self.on_navigate = on_navigate
        self.on_quit = on_quit
        self.buttons: list[Button] = []
        self.selected_index: int = 0

    def layout(self, screen_w: int, screen_h: int) -> None:
        self.buttons.clear()
        menu_w = min(460, screen_w - 40)
        start_y = max(160, screen_h // 2 - 170)
        col = Column(
            (screen_w - menu_w) // 2,
            start_y,
            menu_w,
            spacing=12,
            align=Align.CENTER,
        )

        options = [
            ("PLAY", "Descend into RenderX: Depths wireframe dungeon crawler", lambda: self.on_navigate("Play")),
            ("EXPLORE", "Sandbox 3D model viewer, transforms & OBJ import", lambda: self.on_navigate("Explore")),
            ("LEARN", "Interactive 3D graphics pipeline inspector & lessons", lambda: self.on_navigate("Learn")),
            ("SETTINGS", "Display, audio, controls, theme & accessibility", lambda: self.on_navigate("Settings")),
            ("ABOUT", "Project info, mathematical foundations & credits", lambda: self.on_navigate("About")),
            ("QUICK TOUR", "5-minute guided walkthrough for beginners", lambda: self.on_navigate("Tour")),
            ("EXIT", "Close RenderX", self.on_quit),
        ]

        for idx, (title, subtitle, action) in enumerate(options):
            r = col.add(menu_w, 48)
            btn = Button(
                r,
                f"{title}  —  {subtitle}" if menu_w > 400 else title,
                on_click=action,
                font_size=FONT_SM,
                accent=(idx == 0),
            )
            self.buttons.append(btn)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self._update_focus()
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self._update_focus()
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if 0 <= self.selected_index < len(self.buttons):
                    self.buttons[self.selected_index].on_activate()
                    return True

        for idx, btn in enumerate(self.buttons):
            if btn.handle_event(event):
                self.selected_index = idx
                return True
        return False

    def _update_focus(self) -> None:
        for idx, btn in enumerate(self.buttons):
            btn.focused = (idx == self.selected_index)

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        sw, sh = surface.get_size()
        surface.fill(thm.background)

        # Subtle decorative wireframe background grid
        for x in range(0, sw, 50):
            pygame.draw.line(surface, thm.grid, (x, 0), (x, sh))
        for y in range(0, sh, 50):
            pygame.draw.line(surface, thm.grid, (0, y), (sw, y))

        # Title & Subtitle
        font_hero = get_font(FONT_HERO, bold=True)
        title_img = font_hero.render("RenderX", True, thm.accent)
        surface.blit(title_img, ((sw - title_img.get_width()) // 2, max(40, sh // 2 - 250)))

        font_sub = get_font(FONT_BODY)
        sub_img = font_sub.render(
            "Software 3D Wireframe Engine  •  Play  •  Explore  •  Learn",
            True,
            thm.text_dim,
        )
        surface.blit(sub_img, ((sw - sub_img.get_width()) // 2, max(95, sh // 2 - 195)))

        # Version & Author
        font_sm = get_font(FONT_SM)
        ver_img = font_sm.render("v4.0.0  |  Harsh Mahashabde", True, thm.text_dim)
        surface.blit(ver_img, (SPACE_MD, sh - 28))

        # Buttons
        for btn in self.buttons:
            btn.draw(surface)
