"""Responsive, restrained HUD rendered as a crisp Pygame overlay."""

import ctypes

import OpenGL.GL as gl
import OpenGL.GL.shaders
import numpy as np
import pygame


class UIRenderer:
    BG = (12, 17, 24)
    PANEL = (18, 25, 34)
    PANEL_EDGE = (58, 72, 88)
    TEXT = (232, 238, 244)
    MUTED = (158, 172, 186)
    ACCENT = (105, 225, 191)
    GOLD = (241, 190, 103)
    RED = (231, 111, 105)

    def __init__(self, width, height, shader_dir):
        self.width, self.height = max(1, width), max(1, height)
        self.shader_dir = shader_dir
        self.surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.font.init()
        self.fonts = {}
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
            self.fonts[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
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
             player_position=(0.0, 0.0), enemy_positions=(), supply_positions=()):
        self.surface.fill((0, 0, 0, 0))
        self.buttons.clear()
        if state == "PLAYING":
            self._draw_hud(health, score, wave, remaining, mouse, elapsed,
                           message, dash_ready, next_wave, player_position,
                           enemy_positions, supply_positions)
        elif state in ("MENU", "DIFFICULTY"):
            self._draw_title(state, high_score, difficulty, mouse)
        elif state == "PAUSED":
            self._draw_dim()
            self._draw_dialog("PAUSED", "Run suspended", mouse, [
                ("resume", "Resume run"), ("restart", "Restart run"),
                ("menu", "Return to menu"),
            ])
        elif state == "GAME_OVER":
            self._draw_dim((6, 8, 12, 202))
            self._draw_dialog("RUN ENDED", f"Score  {score:,}     Wave  {wave}", mouse, [
                ("restart", "Run again"), ("menu", "Return to menu"),
            ])
        self._upload()

    def _draw_hud(self, health, score, wave, remaining, mouse, elapsed,
                  message, dash_ready, next_wave, player_position,
                  enemy_positions, supply_positions):
        s = self.surface
        margin = max(22, round(self.width * .025))
        top = pygame.Rect(margin, margin, min(300, self.width // 3), 76)
        self._panel(top, alpha=220)
        self._label("VITALS", (top.x + 16, top.y + 9), 13, self.MUTED, bold=True)
        self._label(f"{max(0, int(health)):03d}", (top.x + 16, top.y + 27), 25,
                    self.TEXT, bold=True)
        bar = pygame.Rect(top.x + 92, top.y + 42, top.width - 110, 9)
        pygame.draw.rect(s, (55, 67, 79), bar, border_radius=5)
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
        cross = (self.ACCENT if dash_ready else (125, 143, 158))
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
        if message:
            self._banner(message, self.height * .18)
        elif next_wave > 0:
            self._banner(f"NEXT WAVE  ·  {next_wave:0.1f}", self.height * .18)

    def _minimap(self, rect, player_position, enemies, supplies):
        box = pygame.Rect(rect)
        self._panel(box, alpha=215)
        inner = box.inflate(-18, -18)
        pygame.draw.rect(self.surface, (23, 32, 42), inner, border_radius=5)
        pygame.draw.rect(self.surface, (76, 92, 107), inner, 1, border_radius=5)
        for index in range(1, 4):
            x = inner.x + inner.w * index / 4
            y = inner.y + inner.h * index / 4
            pygame.draw.line(self.surface, (43, 56, 69), (x, inner.y), (x, inner.bottom), 1)
            pygame.draw.line(self.surface, (43, 56, 69), (inner.x, y), (inner.right, y), 1)
        player_x, player_z = player_position
        radius = 36.0
        for x, z, elite in enemies:
            dx, dz = x - player_x, z - player_z
            if abs(dx) <= radius and abs(dz) <= radius:
                point = (round(inner.centerx + dx / radius * inner.w / 2),
                         round(inner.centery + dz / radius * inner.h / 2))
                pygame.draw.circle(self.surface, self.GOLD if elite else self.RED,
                                   point, 3 if elite else 2)
        for x, z in supplies:
            dx, dz = x - player_x, z - player_z
            if abs(dx) <= radius and abs(dz) <= radius:
                point = (round(inner.centerx + dx / radius * inner.w / 2),
                         round(inner.centery + dz / radius * inner.h / 2))
                pygame.draw.circle(self.surface, self.ACCENT, point, 3)
        pygame.draw.circle(self.surface, self.TEXT, inner.center, 4)

    def _draw_title(self, state, high_score, difficulty, mouse):
        w, h = self.width, self.height
        self._draw_dim((7, 10, 15, 104))
        panel_w = min(610, max(410, round(w * .42)))
        panel_h = min(520, max(430, round(h * .72)))
        panel = pygame.Rect(0, 0, panel_w, panel_h)
        panel.center = (round(w * .5), round(h * .50))
        self._panel(panel, alpha=248)
        self._label("RENDERX   /   FIELD OPERATIONS",
                    (panel.x + 34, panel.y + 30), 13, self.ACCENT, bold=True)
        if state == "MENU":
            self._label("BREAKPOINT", (panel.x + 32, panel.y + 72), 43,
                        self.TEXT, bold=True)
            self._label("3D survival shooter", (panel.x + 34, panel.y + 127),
                        18, self.MUTED)
            self._rule(panel.x + 34, panel.y + 168, panel.width - 68)
            stats = pygame.Rect(panel.x + 34, panel.y + 190, panel.width - 68, 82)
            self._panel(stats, fill=(23, 33, 43), alpha=255)
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
                self._panel(card, fill=(28, 53, 55) if selected else (23, 33, 43),
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

    def _draw_dim(self, color=(5, 8, 12, 154)):
        self.surface.fill(color)

    def _button(self, action, label, rect, mouse, primary=False):
        self.buttons[action] = pygame.Rect(rect)
        hovered = rect.collidepoint(mouse)
        fill = (52, 104, 94) if primary else (28, 39, 50)
        border = self.ACCENT if primary else self.PANEL_EDGE
        if hovered:
            fill = (68, 126, 111) if primary else (38, 54, 67)
            border = self.ACCENT
        self._panel(rect, fill=fill, border=border, alpha=255)
        self._label(label, rect.center, 16, self.TEXT, bold=True, center=True)

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
               center_y=False):
        image = self._font(size, bold).render(str(value), True, color)
        rect = image.get_rect()
        if center:
            rect.center = (round(position[0]), round(position[1]))
        elif center_y:
            rect.midleft = (round(position[0]), round(position[1]))
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
        self._panel(pill, fill=(22, 36, 43), border=self.ACCENT, alpha=240)
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
