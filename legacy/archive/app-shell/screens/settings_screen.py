"""Settings & Accessibility configuration screen."""
from typing import Callable, List
import pygame

from renderx.services.settings import settings_service, Settings
from renderx.ui.theme import (
    current_theme,
    set_theme,
    THEMES,
    get_font,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_BODY,
    FONT_SM,
    SPACE_MD,
    SPACE_LG,
)
from renderx.ui.layout import Rect, Column, Row, Align
from renderx.ui.widgets import Button, Slider, ToggleButton, Label, Card
from renderx.engine.audio import audio


class SettingsScreen:
    """Manages display, audio, control rebinding, and theme configurations."""

    def __init__(self, on_back: Callable[[], None]):
        self.on_back = on_back
        self.widgets: List[Any] = []
        self.settings: Settings = settings_service.current

    def layout(self, screen_w: int, screen_h: int) -> None:
        self.widgets.clear()
        content_w = min(720, screen_w - 40)
        start_x = (screen_w - content_w) // 2

        # Header Back Button
        self.btn_back = Button(
            Rect(start_x, 30, 100, 36),
            "← Back",
            on_click=self.on_back,
            font_size=FONT_SM,
        )
        self.widgets.append(self.btn_back)

        col = Column(start_x, 80, content_w, spacing=14, align=Align.START)

        # 1. Theme & Appearance
        self.theme_btns = []
        theme_names = list(THEMES.keys())
        theme_row = Row(start_x, col.current_y, 36, spacing=8)
        for t_name in theme_names:
            btn = ToggleButton(
                theme_row.add(content_w // len(theme_names) - 8, 36),
                t_name,
                active=(self.settings.theme == t_name),
                on_toggle=lambda act, name=t_name: self._set_theme_choice(name),
                font_size=FONT_SM,
            )
            self.theme_btns.append(btn)
            self.widgets.append(btn)
        col.current_y += 44

        # 2. Audio Sliders
        s_master = Slider(
            col.add(content_w, 36),
            "Master Volume",
            self.settings.master_volume,
            0.0,
            1.0,
            step=0.05,
            on_change=lambda val: self._update_audio("master", val),
        )
        self.widgets.append(s_master)

        s_sfx = Slider(
            col.add(content_w, 36),
            "Sound FX Volume",
            self.settings.sfx_volume,
            0.0,
            1.0,
            step=0.05,
            on_change=lambda val: self._update_audio("sfx", val),
        )
        self.widgets.append(s_sfx)

        s_amb = Slider(
            col.add(content_w, 36),
            "Ambient Volume",
            self.settings.ambient_volume,
            0.0,
            1.0,
            step=0.05,
            on_change=lambda val: self._update_audio("ambient", val),
        )
        self.widgets.append(s_amb)

        # 3. Graphics & Camera
        s_fov = Slider(
            col.add(content_w, 36),
            "Field of View",
            self.settings.fov,
            45.0,
            90.0,
            step=1.0,
            on_change=lambda val: self._update_setting("fov", val),
        )
        self.widgets.append(s_fov)

        s_sens = Slider(
            col.add(content_w, 36),
            "Mouse Sensitivity",
            self.settings.mouse_sensitivity,
            0.2,
            3.0,
            step=0.1,
            on_change=lambda val: self._update_setting("mouse_sensitivity", val),
        )
        self.widgets.append(s_sens)

        # 4. Accessibility Toggles
        btn_fps = ToggleButton(
            col.add(content_w, 36),
            f"Show FPS: {'ON' if self.settings.show_fps else 'OFF'}",
            active=self.settings.show_fps,
            on_toggle=lambda act: self._toggle_fps(act),
            font_size=FONT_SM,
        )
        self.widgets.append(btn_fps)

        btn_motion = ToggleButton(
            col.add(content_w, 36),
            f"Reduced Motion (Disable Screen Shake): {'ON' if self.settings.reduced_motion else 'OFF'}",
            active=self.settings.reduced_motion,
            on_toggle=lambda act: self._toggle_motion(act),
            font_size=FONT_SM,
        )
        self.widgets.append(btn_motion)

        btn_flash = ToggleButton(
            col.add(content_w, 36),
            f"Reduced Flash (Disable Damage Flashes): {'ON' if self.settings.reduced_flash else 'OFF'}",
            active=self.settings.reduced_flash,
            on_toggle=lambda act: self._toggle_flash(act),
            font_size=FONT_SM,
        )
        self.widgets.append(btn_flash)

        # 5. Reset Keybindings
        btn_reset_keys = Button(
            col.add(content_w, 38),
            "Restore Default Controls",
            on_click=self._restore_default_keys,
            font_size=FONT_SM,
        )
        self.widgets.append(btn_reset_keys)

    def _set_theme_choice(self, name: str) -> None:
        self.settings.theme = name
        set_theme(name)
        for b in self.theme_btns:
            b.active = (b.text == name)
        settings_service.save(self.settings)

    def _update_audio(self, kind: str, val: float) -> None:
        if kind == "master":
            self.settings.master_volume = val
        elif kind == "sfx":
            self.settings.sfx_volume = val
        elif kind == "ambient":
            self.settings.ambient_volume = val
        audio.set_volumes(
            self.settings.master_volume,
            self.settings.sfx_volume,
            self.settings.ambient_volume,
        )
        settings_service.save(self.settings)

    def _update_setting(self, key: str, val: float) -> None:
        setattr(self.settings, key, val)
        settings_service.save(self.settings)

    def _toggle_fps(self, act: bool) -> None:
        self.settings.show_fps = act
        settings_service.save(self.settings)

    def _toggle_motion(self, act: bool) -> None:
        self.settings.reduced_motion = act
        settings_service.save(self.settings)

    def _toggle_flash(self, act: bool) -> None:
        self.settings.reduced_flash = act
        settings_service.save(self.settings)

    def _restore_default_keys(self) -> None:
        self.settings.reset_keys_to_default()
        settings_service.save(self.settings)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()
            return True
        for w in self.widgets:
            if w.handle_event(event):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        thm = current_theme
        sw, sh = surface.get_size()
        surface.fill(thm.background)

        # Title
        font_title = get_font(FONT_TITLE, bold=True)
        title_lbl = font_title.render("Settings & Accessibility", True, thm.accent)
        surface.blit(title_lbl, (sw // 2 - title_lbl.get_width() // 2, 32))

        for w in self.widgets:
            w.draw(surface)
