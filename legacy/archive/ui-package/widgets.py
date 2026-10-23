"""Reusable UI widgets rendered at native screen resolution with keyboard navigation."""
from typing import Callable, Optional, Sequence, Tuple, List, Any
import pygame

from renderx.ui.theme import (
    current_theme,
    get_font,
    FONT_SM,
    FONT_BODY,
    FONT_SUBTITLE,
    FONT_TITLE,
    RADIUS_SM,
    RADIUS_MD,
    SPACE_XS,
    SPACE_SM,
    SPACE_MD,
)
from renderx.ui.layout import Rect, Point2D


class Widget:
    """Base interactive UI widget with focus, hover, press, and keyboard navigation."""

    def __init__(self, rect: Rect | None = None, enabled: bool = True):
        self.rect = rect or Rect()
        self.enabled = enabled
        self.hovered = False
        self.pressed = False
        self.focused = False
        self.tooltip_text: Optional[str] = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process mouse and keyboard events. Returns True if event was consumed."""
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            return False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
                self.focused = True
                return True
            else:
                self.focused = False

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed:
                self.pressed = False
                if self.rect.collidepoint(event.pos):
                    self.on_activate()
                    return True

        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_activate()
                return True

        return False

    def on_activate(self) -> None:
        """Invoked when button is clicked or activated via Space/Enter."""
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Render widget onto surface."""
        pass


class Button(Widget):
    """Clickable button with text label, hover, and press states."""

    def __init__(
        self,
        rect: Rect,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        font_size: int = FONT_BODY,
        accent: bool = False,
        tooltip: Optional[str] = None,
    ):
        super().__init__(rect)
        self.text = text
        self.on_click = on_click
        self.font_size = font_size
        self.accent = accent
        self.tooltip_text = tooltip

    def on_activate(self) -> None:
        if self.on_click:
            self.on_click()

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        pg_rect = self.rect.to_pygame_rect()

        # Background color
        if not self.enabled:
            bg = thm.surface
            fg = thm.text_dim
            border = thm.border
        elif self.pressed:
            bg = thm.surface_active
            fg = thm.text
            border = thm.border_focus
        elif self.hovered:
            bg = thm.surface_hover
            fg = thm.text
            border = thm.accent if self.accent else thm.border_focus
        elif self.accent:
            bg = thm.accent
            fg = (255, 255, 255)
            border = thm.accent_hover
        else:
            bg = thm.surface
            fg = thm.text
            border = thm.border_focus if self.focused else thm.border

        pygame.draw.rect(surface, bg, pg_rect, border_radius=RADIUS_MD)
        pygame.draw.rect(surface, border, pg_rect, width=2 if (self.focused or self.accent) else 1, border_radius=RADIUS_MD)

        font = get_font(self.font_size, bold=self.accent)
        label = font.render(self.text, True, fg)
        lbl_x = self.rect.x + (self.rect.w - label.get_width()) // 2
        lbl_y = self.rect.y + (self.rect.h - label.get_height()) // 2
        surface.blit(label, (lbl_x, lbl_y))


class ToggleButton(Widget):
    """Button representing a persistent boolean toggle state."""

    def __init__(
        self,
        rect: Rect,
        text: str,
        active: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        font_size: int = FONT_BODY,
    ):
        super().__init__(rect)
        self.text = text
        self.active = active
        self.on_toggle = on_toggle
        self.font_size = font_size

    def on_activate(self) -> None:
        self.active = not self.active
        if self.on_toggle:
            self.on_toggle(self.active)

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        pg_rect = self.rect.to_pygame_rect()

        if self.active:
            bg = thm.surface_active
            fg = thm.accent
            border = thm.accent
        elif self.hovered:
            bg = thm.surface_hover
            fg = thm.text
            border = thm.border_focus
        else:
            bg = thm.surface
            fg = thm.text_dim
            border = thm.border

        pygame.draw.rect(surface, bg, pg_rect, border_radius=RADIUS_MD)
        pygame.draw.rect(surface, border, pg_rect, width=2 if self.active else 1, border_radius=RADIUS_MD)

        font = get_font(self.font_size, bold=self.active)
        label = font.render(self.text, True, fg)
        lbl_x = self.rect.x + (self.rect.w - label.get_width()) // 2
        lbl_y = self.rect.y + (self.rect.h - label.get_height()) // 2
        surface.blit(label, (lbl_x, lbl_y))


class TabBar(Widget):
    """Horizontal tab selector bar."""

    def __init__(
        self,
        rect: Rect,
        tabs: Sequence[str],
        active_index: int = 0,
        on_tab_change: Optional[Callable[[int, str], None]] = None,
    ):
        super().__init__(rect)
        self.tabs = list(tabs)
        self.active_index = active_index
        self.on_tab_change = on_tab_change

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                tab_w = self.rect.w // max(1, len(self.tabs))
                idx = (event.pos[0] - self.rect.x) // tab_w
                if 0 <= idx < len(self.tabs) and idx != self.active_index:
                    self.active_index = idx
                    if self.on_tab_change:
                        self.on_tab_change(self.active_index, self.tabs[self.active_index])
                    return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.tabs:
            return
        thm = current_theme
        tab_w = self.rect.w // len(self.tabs)
        font = get_font(FONT_BODY)

        for i, tab_name in enumerate(self.tabs):
            tab_rect = pygame.Rect(self.rect.x + i * tab_w, self.rect.y, tab_w, self.rect.h)
            is_active = (i == self.active_index)
            bg = thm.surface_active if is_active else thm.surface
            fg = thm.accent if is_active else thm.text_dim
            pygame.draw.rect(surface, bg, tab_rect, border_radius=RADIUS_SM)
            if is_active:
                pygame.draw.rect(surface, thm.accent, tab_rect, width=2, border_radius=RADIUS_SM)
                # Bottom indicator bar
                pygame.draw.rect(
                    surface,
                    thm.accent,
                    pygame.Rect(tab_rect.left, tab_rect.bottom - 3, tab_rect.width, 3),
                )
            else:
                pygame.draw.rect(surface, thm.border, tab_rect, width=1, border_radius=RADIUS_SM)

            label = font.render(tab_name, True, fg)
            lbl_x = tab_rect.left + (tab_rect.width - label.get_width()) // 2
            lbl_y = tab_rect.top + (tab_rect.height - label.get_height()) // 2
            surface.blit(label, (lbl_x, lbl_y))


class Slider(Widget):
    """Horizontal value slider."""

    def __init__(
        self,
        rect: Rect,
        label: str,
        value: float,
        min_val: float,
        max_val: float,
        step: float = 0.1,
        on_change: Optional[Callable[[float], None]] = None,
    ):
        super().__init__(rect)
        self.label = label
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.on_change = on_change
        self.dragging = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_val_from_mouse(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_val_from_mouse(event.pos[0])
            return True
        return False

    def _update_val_from_mouse(self, mouse_x: int) -> None:
        track_left = self.rect.x + 120
        track_w = max(10, self.rect.w - 180)
        norm = max(0.0, min(1.0, (mouse_x - track_left) / track_w))
        raw = self.min_val + norm * (self.max_val - self.min_val)
        stepped = round(raw / self.step) * self.step
        new_val = max(self.min_val, min(self.max_val, stepped))
        if new_val != self.value:
            self.value = new_val
            if self.on_change:
                self.on_change(self.value)

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        font = get_font(FONT_SM)
        # Label
        lbl = font.render(self.label, True, thm.text)
        surface.blit(lbl, (self.rect.x, self.rect.y + (self.rect.h - lbl.get_height()) // 2))

        # Track
        track_left = self.rect.x + 120
        track_w = max(10, self.rect.w - 180)
        track_y = self.rect.y + self.rect.h // 2
        pygame.draw.line(surface, thm.border, (track_left, track_y), (track_left + track_w, track_y), 4)

        # Fill track
        norm = max(0.0, min(1.0, (self.value - self.min_val) / max(0.001, self.max_val - self.min_val)))
        fill_w = int(track_w * norm)
        pygame.draw.line(surface, thm.accent, (track_left, track_y), (track_left + fill_w, track_y), 4)

        # Thumb knob
        thumb_x = track_left + fill_w
        pygame.draw.circle(surface, thm.accent_hover if self.dragging else thm.accent, (thumb_x, track_y), 7)
        pygame.draw.circle(surface, thm.text, (thumb_x, track_y), 3)

        # Numeric value readout
        val_str = f"{self.value:.1f}" if self.step < 1.0 else f"{int(self.value)}"
        val_lbl = font.render(val_str, True, thm.text_dim)
        surface.blit(val_lbl, (track_left + track_w + 12, self.rect.y + (self.rect.h - val_lbl.get_height()) // 2))


class Label(Widget):
    """Text label supporting automatic word-wrapping."""

    def __init__(
        self,
        rect: Rect,
        text: str,
        font_size: int = FONT_BODY,
        color: Optional[Tuple[int, int, int]] = None,
        bold: bool = False,
        align: str = "left",
    ):
        super().__init__(rect)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.bold = bold
        self.align = align

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        fg = self.color or thm.text
        font = get_font(self.font_size, bold=self.bold)

        lines = self.text.split("\n")
        rendered_lines = []
        for raw_line in lines:
            words = raw_line.split(" ")
            curr = ""
            for w in words:
                test = curr + (" " if curr else "") + w
                if font.size(test)[0] <= self.rect.w or not curr:
                    curr = test
                else:
                    rendered_lines.append(curr)
                    curr = w
            if curr:
                rendered_lines.append(curr)

        y = self.rect.y
        line_height = font.get_linesize()
        for l in rendered_lines:
            img = font.render(l, True, fg)
            if self.align == "center":
                x = self.rect.x + (self.rect.w - img.get_width()) // 2
            elif self.align == "right":
                x = self.rect.x + self.rect.w - img.get_width()
            else:
                x = self.rect.x
            surface.blit(img, (x, y))
            y += line_height


class Card(Widget):
    """Styled background panel with border, padding, and optional header."""

    def __init__(self, rect: Rect, title: Optional[str] = None):
        super().__init__(rect)
        self.title = title

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        pg_rect = self.rect.to_pygame_rect()
        pygame.draw.rect(surface, thm.surface, pg_rect, border_radius=RADIUS_MD)
        pygame.draw.rect(surface, thm.border, pg_rect, width=1, border_radius=RADIUS_MD)

        if self.title:
            font = get_font(FONT_SUBTITLE, bold=True)
            lbl = font.render(self.title, True, thm.text)
            surface.blit(lbl, (self.rect.x + SPACE_MD, self.rect.y + SPACE_SM))
            pygame.draw.line(
                surface,
                thm.border,
                (self.rect.x, self.rect.y + 36),
                (self.rect.right, self.rect.y + 36),
                1,
            )


class ProgressBar(Widget):
    """Animated horizontal progress meter."""

    def __init__(
        self,
        rect: Rect,
        fraction: float = 0.0,
        fill_color: Optional[Tuple[int, int, int]] = None,
        text_overlay: Optional[str] = None,
    ):
        super().__init__(rect)
        self.fraction = max(0.0, min(1.0, fraction))
        self.fill_color = fill_color
        self.text_overlay = text_overlay

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        pg_rect = self.rect.to_pygame_rect()
        pygame.draw.rect(surface, thm.surface_active, pg_rect, border_radius=RADIUS_SM)

        fill_w = int(self.rect.w * self.fraction)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            fill_col = self.fill_color or thm.accent
            pygame.draw.rect(surface, fill_col, fill_rect, border_radius=RADIUS_SM)

        pygame.draw.rect(surface, thm.border, pg_rect, width=1, border_radius=RADIUS_SM)

        if self.text_overlay:
            font = get_font(FONT_SM, bold=True)
            lbl = font.render(self.text_overlay, True, thm.text)
            surface.blit(
                lbl,
                (
                    self.rect.x + (self.rect.w - lbl.get_width()) // 2,
                    self.rect.y + (self.rect.h - lbl.get_height()) // 2,
                ),
            )
