"""Responsive, restrained HUD rendered as a crisp Pygame overlay."""

import ctypes

import OpenGL.GL as gl
import OpenGL.GL.shaders
import numpy as np
import pygame
from renderx import theme as appearance
from renderx.ui.fonts import font as local_font
from renderx.ui import icons
from renderx.ui.theme import palette
from renderx.ui.components.slider import draw_slider


class UIRenderer:
    def __init__(self, width, height, shader_dir, audio=None):
        self.width, self.height = max(1, width), max(1, height)
        self.shader_dir = shader_dir
        self.audio = audio
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.font.init()
        self.fonts = {}
        colors = palette(appearance.mode())
        self.BG = colors["CANVAS"]
        self.PANEL = colors["SURFACE_1"]
        self.PANEL_EDGE = colors["BORDER"]
        self.SURFACE_2 = colors["SURFACE_2"]
        self.SURFACE_3 = colors["SURFACE_3"]
        self.GRID = colors["GRID"]
        self.TEXT = colors["TEXT"]
        self.MUTED = colors["TEXT_MUTED"]
        self.TEXT_DIM = colors["TEXT_DIM"]
        self.ACCENT = colors["ACCENT"]
        self.ACCENT_TEXT = colors["ACCENT_TEXT"]
        self.GOLD = colors["WARNING"]
        self.RED = colors["ERROR"]
        self.buttons = {}
        self._last_health = 100
        self.tex_id = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height,
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        self._compile_shaders()
        self._setup_quad()

    def resize(self, width, height):
        self.width, self.height = max(1, width), max(1, height)
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height,
                        0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)

    def _font(self, size, bold=False):
        key = size, bold
        if key not in self.fonts:
            self.fonts[key] = local_font("body", size, bold=bold)
        return self.fonts[key]

    def _compile_shaders(self):
        with open(self.shader_dir / "ui_vertex.glsl", encoding="utf-8") as source:
            vertex = source.read()
        with open(self.shader_dir / "ui_fragment.glsl", encoding="utf-8") as source:
            fragment = source.read()
        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(vertex, gl.GL_VERTEX_SHADER),
            OpenGL.GL.shaders.compileShader(fragment, gl.GL_FRAGMENT_SHADER),
        )
        self.sampler = gl.glGetUniformLocation(self.shader, "uiTexture")

    def _setup_quad(self):
        vertices = np.array([
            -1, -1, 0, 0,  1, -1, 1, 0,  1, 1, 1, 1,
             1,  1, 1, 1, -1,  1, 0, 1, -1, -1, 0, 0,
        ], dtype=np.float32)
        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 16, ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(1)
        gl.glBindVertexArray(0)

    def action_at(self, position):
        return next((action for action, rect in reversed(tuple(self.buttons.items()))
                     if rect.collidepoint(position)), None)

    def draw(self, state, health, score, high_score, difficulty, wave, remaining,
             mouse, elapsed=0.0, message="", dash_ready=True, next_wave=0.0,
             player_position=(0.0, 0.0), enemy_positions=(), supply_positions=(),
             buffs=None, boss=None):
        self.surface.fill((0, 0, 0, 0))
        self.buttons.clear()
        if state == "PLAYING":
            self._draw_hud(health, score, wave, remaining, mouse, elapsed,
                           message, dash_ready, next_wave, player_position,
                           enemy_positions, supply_positions, buffs or {}, boss)
        elif state in ("MENU", "DIFFICULTY"):
            self._draw_title(state, high_score, difficulty, mouse)
        elif state == "PAUSED":
            self._draw_dim()
            self._draw_dialog("PAUSED", "Run suspended", mouse, [
                ("resume", "Resume run"), ("restart", "Restart run"),
                ("menu", "Return to menu"), ("return", "Return to RenderX"),
            ])
        elif state == "GAME_OVER":
            self._draw_dim((*self.BG, 202))
            self._draw_dialog("RUN ENDED", f"Score  {score:,}     Wave  {wave}", mouse, [
                ("restart", "Run again"), ("menu", "Return to menu"),
                ("return", "Return to RenderX"),
            ])
        elif state == "CONFIRM_RETURN":
            self._draw_dim()
            self._draw_dialog("Leave this run?", "Your current run will end.", mouse, [
                ("cancel_return", "Cancel"), ("leave_return", "Leave"),
            ])
        if state == "PLAYING" and boss:
            self._draw_boss_bar(boss)
        self._draw_audio_controls(mouse)
        self._upload()

    def _draw_audio_controls(self, mouse):
        """Keep music mute and master volume available in every shooter state."""
        panel = pygame.Rect(0, 0, 236, 42)
        panel.centerx = self.width // 2
        panel.y = max(12, round(self.height * .025))
        self._panel(panel, alpha=238)
        muted = bool(self.audio and self.audio.music_muted)
        color = self.MUTED if muted else self.ACCENT
        self._label("MUSIC", (panel.x + 10, panel.centery), 11, color,
                    bold=True, center_y=True)
        volume = self.audio.volume if self.audio else 0.66
        slider_rect = pygame.Rect(panel.x + 48, panel.y + 5, 130, 32)
        hit = draw_slider(self.surface, slider_rect, "VOL", volume, 0.0, 1.0,
                          mode=appearance.mode(), value_text=f"{round(volume * 100)}%")
        self.buttons["audio_volume"] = hit
        action = "audio_music"
        button = pygame.Rect(panel.right - 46, panel.y + 5, 38, 32)
        self.buttons[action] = button
        hovered = button.collidepoint(mouse)
        fill = self.SURFACE_3 if hovered else self.SURFACE_2
        self._panel(button, fill=fill, border=self.ACCENT if hovered else self.PANEL_EDGE,
                    alpha=255)
        icons.draw_icon(self.surface, "volume-x" if muted else "volume-2",
                        button.inflate(-10, -8), color)

    def _draw_hud(self, health, score, wave, remaining, mouse, elapsed,
                  message, dash_ready, next_wave, player_position,
                  enemy_positions, supply_positions, buffs, boss):
        s = self.surface
        margin = max(22, round(self.width * .025))
        top = pygame.Rect(margin, margin, min(300, self.width // 3), 76)
        self._panel(top, alpha=220)
        self._label("VITALS", (top.x + 16, top.y + 9), 13, self.MUTED, bold=True)
        self._label(f"{max(0, int(health)):03d}", (top.x + 16, top.y + 27), 25,
                    self.TEXT, bold=True)
        bar = pygame.Rect(top.x + 92, top.y + 42, top.width - 110, 9)
        pygame.draw.rect(s, self.SURFACE_3, bar, border_radius=5)
        fill = bar.copy()
        fill.width = round(bar.width * max(0, min(1, health / 100)))
        if fill.width:
            col = self.ACCENT if health > 35 else self.RED
            pygame.draw.rect(s, col, fill, border_radius=5)
        self._label(f"SCORE  {score:,}", (top.right + 18, top.y + 26), 18,
                    self.TEXT, bold=True)

        right = pygame.Rect(self.width - margin - 192, margin, 192, 110)
        self._panel(right, alpha=220)
        self._label(f"WAVE  {wave:02d}", (right.x + 15, right.y + 12), 18,
                    self.GOLD, bold=True)
        self._label(f"HOSTILES  {remaining:02d}", (right.x + 15, right.y + 42),
                    15, self.TEXT, bold=True)
        self._label(_clock_text(elapsed), (right.x + 15, right.y + 73), 15,
                    self.MUTED)

        self._minimap((self.width - margin - 132, right.bottom + 12, 132, 132),
                      player_position, enemy_positions, supply_positions)
        cross = self.ACCENT if dash_ready else self.TEXT_DIM
        mx, my = mouse
        gap, length = 7, 11
        pygame.draw.line(s, cross, (mx - gap - length, my), (mx - gap, my), 2)
        pygame.draw.line(s, cross, (mx + gap, my), (mx + gap + length, my), 2)
        pygame.draw.line(s, cross, (mx, my - gap - length), (mx, my - gap), 2)
        pygame.draw.line(s, cross, (mx, my + gap), (mx, my + gap + length), 2)
        pygame.draw.circle(s, cross, (mx, my), 2)

        footer = pygame.Rect(margin, self.height - margin - 42,
                             min(530, self.width - margin * 2), 42)
        self._panel(footer, alpha=205)
        controls = "WASD Move  ·  Mouse Aim  ·  LMB / Space Fire  ·  Shift Dash  ·  Esc Pause"
        self._label(controls, (footer.x + 14, footer.centery), 13, self.MUTED,
                    center_y=True)
        if buffs:
            self._draw_buff_status(buffs, footer)
        if message:
            self._banner(message, self.height * (.30 if boss else .18))
        elif next_wave > 0:
            self._banner(f"NEXT WAVE  ·  {next_wave:0.1f}", self.height * .18)

    def _draw_boss_bar(self, boss):
        name, health, maximum, phase = boss
        panel = pygame.Rect(0, 0, min(360, self.width - 40), 38)
        panel.centerx = self.width // 2
        panel.y = max(108, round(self.height * .18))
        self._panel(panel, alpha=238)
        ratio = max(0.0, min(1.0, health / max(1, maximum)))
        self._label(name, (panel.x + 12, panel.y + 7), 11, self.TEXT, bold=True)
        self._label(f"PHASE {phase}  ·  {round(ratio * 100)}%",
                    (panel.right - 12, panel.y + 7), 11, self.MUTED,
                    bold=True, align="right")
        track = pygame.Rect(panel.x + 12, panel.y + 25, panel.width - 24, 5)
        pygame.draw.rect(self.surface, self.SURFACE_3, track, border_radius=3)
        fill = track.copy()
        fill.width = round(track.width * ratio)
        if fill.width:
            color = self.ACCENT if phase == 1 else self.GOLD if phase == 2 else self.RED
            pygame.draw.rect(self.surface, color, fill, border_radius=3)

    def _draw_buff_status(self, buffs, footer):
        styles = {
            "rapid": ("RAPID FIRE", self.GOLD, 12.0),
            "shield": ("SHIELD", self.ACCENT, 10.0),
            "overdrive": ("OVERDRIVE", (184, 137, 255), 9.0),
        }
        active = [(name, max(0.0, time_left), *styles[name])
                  for name, time_left in buffs.items()
                  if name in styles and time_left > 0]
        if not active:
            return
        gap = 8
        badge_width = min(150, max(112, (self.width - 48 - gap *
                                         (len(active) - 1)) // len(active)))
        row = pygame.Rect(0, 0, badge_width * len(active) + gap * (len(active) - 1), 30)
        row.centerx = self.width // 2
        row.bottom = footer.y - 8
        for index, (_, time_left, label, color, duration) in enumerate(active):
            badge = pygame.Rect(row.x + index * (badge_width + gap), row.y,
                                badge_width, row.height)
            self._panel(badge, fill=self.SURFACE_2, border=color, alpha=238)
            self._label(f"{label}  {time_left:.0f}s", badge.center, 11,
                        color, bold=True, center=True)
            track = pygame.Rect(badge.x + 8, badge.bottom - 4,
                                badge.width - 16, 2)
            pygame.draw.rect(self.surface, self.SURFACE_3, track)
            fill = track.copy()
            fill.width = round(track.width * min(1.0, time_left / duration))
            pygame.draw.rect(self.surface, color, fill)

    def _minimap(self, rect, player_position, enemies, supplies):
        box = pygame.Rect(rect)
        self._panel(box, alpha=215)
        inner = box.inflate(-18, -18)
        pygame.draw.rect(self.surface, self.SURFACE_2, inner, border_radius=5)
        pygame.draw.rect(self.surface, self.PANEL_EDGE, inner, 1, border_radius=5)
        for index in range(1, 4):
            x = inner.x + inner.w * index / 4
            y = inner.y + inner.h * index / 4
            pygame.draw.line(self.surface, self.GRID, (x, inner.y), (x, inner.bottom), 1)
            pygame.draw.line(self.surface, self.GRID, (inner.x, y), (inner.right, y), 1)
        player_x, player_z = player_position
        radius = 36.0
        enemy_colors = {
            "scout": (100, 190, 230),
            "striker": self.GOLD,
            "bulwark": self.RED,
            "wraith": (184, 137, 255),
            "boss": self.RED,
        }
        for x, z, kind in enemies:
            dx, dz = x - player_x, z - player_z
            if abs(dx) <= radius and abs(dz) <= radius:
                point = (round(inner.centerx + dx / radius * inner.w / 2),
                         round(inner.centery + dz / radius * inner.h / 2))
                if isinstance(kind, bool):
                    kind = "boss" if kind else "striker"
                size = 5 if kind == "boss" else 3 if kind == "bulwark" else 2
                pygame.draw.circle(self.surface, enemy_colors.get(kind, self.RED),
                                   point, size)
        supply_colors = {
            "health": self.ACCENT,
            "rapid": self.GOLD,
            "shield": (85, 190, 240),
            "overdrive": (184, 137, 255),
        }
        for x, z, kind in supplies:
            dx, dz = x - player_x, z - player_z
            if abs(dx) <= radius and abs(dz) <= radius:
                point = (round(inner.centerx + dx / radius * inner.w / 2),
                         round(inner.centery + dz / radius * inner.h / 2))
                pygame.draw.circle(self.surface, supply_colors.get(kind, self.ACCENT),
                                   point, 3)
        pygame.draw.circle(self.surface, self.TEXT, inner.center, 4)

    def _draw_title(self, state, high_score, difficulty, mouse):
        w, h = self.width, self.height
        self._draw_dim((*self.BG, 104))
        panel_w = min(610, max(410, round(w * .42)))
        panel_h = min(520, max(430, round(h * .72)))
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (round(w * .5), round(h * .50))
        self._panel(panel, alpha=248)
        brand_mark = pygame.Rect(panel.x + 32, panel.y + 22, 24, 24)
        icons.draw_icon(self.surface, "brand", brand_mark, self.ACCENT)
        self._label("RENDERX   /   FIELD OPERATIONS",
                    (panel.x + 64, panel.y + 30), 13, self.ACCENT, bold=True)
        if state == "MENU":
            self._label("BREAKPOINT", (panel.x + 32, panel.y + 72), 43,
                        self.TEXT, bold=True)
            self._label("3D survival shooter", (panel.x + 34, panel.y + 127),
                        18, self.MUTED)
            self._rule(panel.x + 34, panel.y + 168, panel.width - 68)
            stats = pygame.Rect(panel.x + 34, panel.y + 190, panel.width - 68, 82)
            self._panel(stats, fill=self.SURFACE_2, alpha=255)
            self._label("BEST RUN", (stats.x + 17, stats.y + 14), 13,
                        self.MUTED, bold=True)
            self._label(f"{high_score:,}", (stats.x + 17, stats.y + 35),
                        24, self.GOLD, bold=True)
            self._label("WAVES", (stats.right - 100, stats.y + 14), 13,
                        self.MUTED, bold=True)
            self._label("ENDLESS", (stats.right - 100, stats.y + 40),
                        16, self.TEXT, bold=True)
            self._button("start", "Start run", pygame.Rect(
                panel.x + 34, panel.bottom - 132, panel.width - 68, 48), mouse,
                primary=True)
            self._button("return", "Return to RenderX", pygame.Rect(
                panel.x + 34, panel.bottom - 72, panel.width - 68, 42), mouse)
            self._label("WASD  Move       Mouse  Aim       LMB  Fire       Shift  Dash",
                        (panel.centerx, panel.bottom + 24), 13, self.MUTED,
                        center=True)
        else:
            self._label("SET DIFFICULTY", (panel.x + 32, panel.y + 72), 34,
                        self.TEXT, bold=True)
            self._label("Choose the pressure for this run.",
                        (panel.x + 34, panel.y + 121), 16, self.MUTED)
            names = ("EASY", "NORMAL", "HARD")
            desc = ("Forgiving", "Balanced", "Relentless")
            gap = 10
            card_w = (panel.width - 68 - 2 * gap) // 3
            card_y = panel.y + 177
            for i, name in enumerate(names):
                card = pygame.Rect(panel.x + 34 + i * (card_w + gap), card_y,
                                   card_w, 112)
                selected = name == difficulty
                self._panel(card, fill=self.SURFACE_3 if selected else self.SURFACE_2,
                            border=self.ACCENT if selected else self.PANEL_EDGE,
                            alpha=255)
                self._label(name, (card.centerx, card.y + 33), 15,
                            self.ACCENT if selected else self.TEXT, bold=True,
                            center=True)
                self._label(desc[i], (card.centerx, card.y + 70), 11,
                            self.MUTED, center=True)
                self.buttons[f"difficulty_{name}"] = card
            self._button("launch", "Deploy", pygame.Rect(
                panel.x + 34, panel.bottom - 132, panel.width - 68, 48), mouse,
                primary=True)
            self._button("back", "Back", pygame.Rect(
                panel.x + 34, panel.bottom - 72, panel.width - 68, 42), mouse)

    def _draw_dialog(self, title, subtitle, mouse, actions):
        w, h = self.width, self.height
        panel = pygame.Rect(0, 0, min(500, w - 36), 170 + len(actions) * 58)
        panel.center = (w // 2, h // 2)
        self._panel(panel, alpha=250)
        self._label(title, (panel.centerx, panel.y + 34), 31, self.TEXT,
                    bold=True, center=True)
        self._label(subtitle, (panel.centerx, panel.y + 76), 15, self.MUTED,
                    center=True)
        for index, (action, label) in enumerate(actions):
            rect = pygame.Rect(panel.x + 32, panel.y + 108 + index * 54,
                               panel.width - 64, 42)
            self._button(action, label, rect, mouse, primary=index == 0)

    def _draw_dim(self, color=None):
        self.surface.fill(color or (*self.BG, 154))

    def _button(self, action, label, rect, mouse, primary=False):
        self.buttons[action] = pygame.Rect(rect)
        hovered = rect.collidepoint(mouse)
        fill = self.ACCENT if primary else self.SURFACE_2
        border = self.ACCENT if primary else self.PANEL_EDGE
        if hovered:
            fill = self.SURFACE_3
            border = self.ACCENT
        self._panel(rect, fill=fill, border=border, alpha=255)
        text_color = self.ACCENT_TEXT if primary and not hovered else self.TEXT
        self._label(label, rect.center, 16, text_color, bold=True, center=True)

    def _panel(self, rect, fill=None, border=None, alpha=220):
        rect = pygame.Rect(rect)
        color = self.PANEL if fill is None else fill
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, (*color, alpha), layer.get_rect(), border_radius=10)
        edge = self.PANEL_EDGE if border is None else border
        pygame.draw.rect(layer, (*edge, min(255, alpha + 20)), layer.get_rect(),
                         1, border_radius=10)
        self.surface.blit(layer, rect)

    def _label(self, value, position, size, color, bold=False, center=False,
               center_y=False, align="left"):
        image = self._font(size, bold).render(str(value), True, color)
        rect = image.get_rect()
        if center:
            rect.center = (round(position[0]), round(position[1]))
        elif center_y:
            rect.midleft = (round(position[0]), round(position[1]))
        elif align == "right":
            rect.topright = (round(position[0]), round(position[1]))
        else:
            rect.topleft = (round(position[0]), round(position[1]))
        self.surface.blit(image, rect)

    def _rule(self, x, y, width):
        pygame.draw.line(self.surface, self.PANEL_EDGE, (x, y), (x + width, y), 1)

    def _banner(self, message, y):
        font = self._font(16, True)
        text = font.render(message, True, self.TEXT)
        rect = text.get_rect(center=(self.width // 2, round(y)))
        pill = rect.inflate(32, 20)
        self._panel(pill, fill=self.SURFACE_2, border=self.ACCENT, alpha=240)
        self.surface.blit(text, rect)

    def _upload(self):
        data = pygame.image.tobytes(self.surface, "RGBA", True)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)
        gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
                           gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        gl.glUseProgram(self.shader)
        gl.glUniform1i(self.sampler, 0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glBindVertexArray(self.vao)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tex_id)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
        gl.glBindVertexArray(0)
        gl.glEnable(gl.GL_DEPTH_TEST)

    def close(self):
        gl.glDeleteTextures([self.tex_id])
        gl.glDeleteBuffers(1, [self.vbo])
        gl.glDeleteVertexArrays(1, [self.vao])
        gl.glDeleteProgram(self.shader)


def _clock_text(seconds):
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"
