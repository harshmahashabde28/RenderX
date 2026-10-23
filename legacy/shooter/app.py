"""Resizable OpenGL survival shooter adapted for the RenderX application."""

from pathlib import Path
import math
import random

import glm
import OpenGL.GL as gl
import pygame

from .engine.camera import Camera
from .engine.mesh import Mesh
from .engine.renderer import Renderer
from .engine.ui_renderer import UIRenderer
from .entities.box import Box
from .entities.enemy import Enemy
from .entities.loot import Loot
from .entities.player import Player
from .entities.projectile import Projectile
from .logic import DIFFICULTIES, aabb_overlap, clamp_frame_time, enemy_count_for_wave
from .storage import load_best, save_if_best


ROOT = Path(__file__).resolve().parent
ARENA_SIZE = 68.0
WINDOW_MIN = (900, 600)


def run_shooter() -> bool:
    """Run the standalone GL mode; return False only when the app should close."""
    pygame.display.quit()
    pygame.display.init()
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                    pygame.GL_CONTEXT_PROFILE_CORE)
    desktop = pygame.display.get_desktop_sizes()[0]
    size = (max(WINDOW_MIN[0], min(1600, int(desktop[0] * .88))),
            max(WINDOW_MIN[1], min(1000, int(desktop[1] * .84))))
    flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
    pygame.display.set_mode(size, flags)
    pygame.display.set_caption("RenderX | Breakpoint")
    pygame.mouse.set_visible(True)
    try:
        return ShooterGame(size, flags).run()
    finally:
        pygame.mouse.set_visible(True)
        pygame.event.clear()
        pygame.display.quit()
        pygame.display.init()


class ShooterGame:
    def __init__(self, size, display_flags):
        self.width, self.height = size
        self.display_flags = display_flags
        self.state = "MENU"
        self.difficulty = "NORMAL"
        self.best = load_best()
        self.score = 0
        self.wave = 0
        self.elapsed = 0.0
        self.wave_intermission = 0.0
        self.spawn_queue = 0
        self.spawn_timer = 0.0
        self.damage_timer = 0.0
        self.message = ""
        self.message_timer = 0.0
        self.streak = 0
        self.streak_timer = 0.0
        self.player_health = 100.0
        self.camera = Camera(self.width, self.height)
        self.player = Player()
        self.boxes = []
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.supplies = []
        self._make_cover()

        self.renderer = Renderer(ROOT / "shaders")
        models = ROOT / "assets" / "models"
        self.meshes = {
            "player": Mesh(models / "player.glb"),
            "enemy": Mesh(models / "enemy.glb"),
            "bullet": Mesh(models / "bullet-foam-tip.glb"),
            "crate": Mesh(models / "crate-medium.glb"),
            "player_gun": Mesh(models / "player_gun.glb"),
            "enemy_gun": Mesh(models / "enemy_gun.glb"),
        }
        self.car_texture = self.renderer.load_texture(str(models / "car_map.png"))
        self.gun_texture = self.renderer.load_texture(str(models / "blaster_map.png"))
        self.ui = UIRenderer(self.width, self.height, ROOT / "shaders")
        self.walls = _make_walls()
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glClearColor(.035, .050, .067, 1.0)
        self.clock = pygame.time.Clock()
        self.keep_host_open = True
        self.fullscreen = False

    def run(self):
        active = True
        try:
            while active:
                dt = clamp_frame_time(self.clock.tick(60) / 1000.0)
                mouse = pygame.mouse.get_pos()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        active = False
                        self.keep_host_open = False
                    elif event.type == pygame.VIDEORESIZE:
                        self._resize(max(WINDOW_MIN[0], event.w),
                                     max(WINDOW_MIN[1], event.h))
                    elif event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
                        if self.state == "PLAYING":
                            self.state = "PAUSED"
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F11:
                            self._toggle_fullscreen()
                        elif event.key == pygame.K_ESCAPE:
                            if self.state == "PLAYING":
                                self.state = "PAUSED"
                            elif self.state == "PAUSED":
                                self.state = "PLAYING"
                        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                            if self.state == "PLAYING":
                                self.player.dash(pygame.key.get_pressed(), *self._aim_target())
                        elif event.key == pygame.K_SPACE and self.state != "PLAYING":
                            self._activate(self.ui.action_at(mouse))
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if self.state == "PLAYING" and event.button == 1:
                            self._fire()
                        elif self.state != "PLAYING" and event.button == 1:
                            self._activate(self.ui.action_at(event.pos))

                if self.state == "PLAYING":
                    self._update(dt)
                self._draw(pygame.mouse.get_pos())
                pygame.display.flip()
        except _ReturnToHost:
            pass
        finally:
            self._close_gl()
        return self.keep_host_open

    def _activate(self, action):
        if action == "start":
            self.state = "DIFFICULTY"
        elif action and action.startswith("difficulty_"):
            self.difficulty = action.removeprefix("difficulty_")
        elif action == "launch":
            self._start_run()
        elif action == "back":
            self.state = "MENU"
        elif action == "return":
            self.state = "RETURN"
        elif action == "resume":
            self.state = "PLAYING"
        elif action == "restart":
            self._start_run()
        elif action == "menu":
            self.best = save_if_best(self.score, self.wave, self.difficulty)
            self._clear_combat()
            self.state = "MENU"

    def _start_run(self):
        self._make_cover()
        self.player = Player()
        self.camera = Camera(self.width, self.height)
        self.player_health = float(DIFFICULTIES[self.difficulty].starting_health)
        self.score = 0
        self.wave = 0
        self.elapsed = 0.0
        self.wave_intermission = 0.0
        self.spawn_queue = 0
        self.spawn_timer = 0.0
        self.damage_timer = 0.0
        self.message = ""
        self.message_timer = 0.0
        self.streak = 0
        self.streak_timer = 0.0
        self._clear_combat()
        self._begin_wave()
        self.state = "PLAYING"

    def _make_cover(self):
        rng = random.Random(503)
        self.boxes = []
        attempts = 0
        while len(self.boxes) < 36 and attempts < 600:
            attempts += 1
            x = rng.uniform(-ARENA_SIZE + 5, ARENA_SIZE - 5)
            z = rng.uniform(-ARENA_SIZE + 5, ARENA_SIZE - 5)
            if math.hypot(x, z) < 13:
                continue
            if any(math.hypot(x - box.x, z - box.z) < 5 for box in self.boxes):
                continue
            box = Box(x, z)
            box.width = box.depth = 2.7
            box.health = 4
            self.boxes.append(box)

    def _clear_combat(self):
        self.enemies.clear()
        self.player_bullets.clear()
        self.enemy_bullets.clear()
        self.supplies.clear()

    def _begin_wave(self):
        self.wave += 1
        self.spawn_queue = enemy_count_for_wave(self.wave)
        self.spawn_timer = .25
        self.message = f"WAVE  {self.wave:02d}"
        self.message_timer = 2.0
        self.wave_intermission = 0.0

    def _update(self, dt):
        keys = pygame.key.get_pressed()
        self.elapsed += dt
        self.damage_timer = max(0.0, self.damage_timer - dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        self.streak_timer = max(0.0, self.streak_timer - dt)
        if self.streak_timer == 0:
            self.streak = 0

        aim_x, aim_z = self._aim_target()
        if aim_x is not None:
            self.player.aim_at(aim_x, aim_z)
        self.player.move(keys, dt, self.boxes, ARENA_SIZE)
        self.camera.follow_target(self.player.x, self.player.z, dt)
        if pygame.mouse.get_pressed()[0] or keys[pygame.K_SPACE]:
            self._fire()

        self._spawn_enemies(dt)
        self._update_enemies(dt)
        self._update_projectiles(dt)
        self._update_supplies(dt)
        if self.spawn_queue == 0 and not self.enemies:
            if self.wave_intermission <= 0:
                self.wave_intermission = 3.0
            else:
                self.wave_intermission -= dt
                if self.wave_intermission <= 0:
                    self._begin_wave()

    def _spawn_enemies(self, dt):
        if self.spawn_queue <= 0:
            return
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return
        self.spawn_timer = max(.28, .76 - min(.35, self.wave * .012))
        self.spawn_queue -= 1
        for _ in range(50):
            angle = random.uniform(0.0, math.tau)
            distance = random.uniform(22.0, 35.0)
            x = max(-ARENA_SIZE + 4, min(ARENA_SIZE - 4,
                                          self.player.x + math.cos(angle) * distance))
            z = max(-ARENA_SIZE + 4, min(ARENA_SIZE - 4,
                                          self.player.z + math.sin(angle) * distance))
            if math.hypot(x - self.player.x, z - self.player.z) < 24:
                continue
            if any(aabb_overlap(x, z, 2.5, 2.5, box.x, box.z,
                                box.width, box.depth) for box in self.boxes):
                continue
            profile = DIFFICULTIES[self.difficulty]
            elite = self.wave % 5 == 0 and self.spawn_queue == 0
            enemy = Enemy(x, z,
                          health=profile.enemy_health + max(0, (self.wave - 1) // 4)
                          + (6 if elite else 0),
                          speed=(profile.enemy_speed + min(.9, self.wave * .035))
                          * (1.12 if elite else 1.0),
                          fire_interval=max(.75, profile.enemy_fire_interval -
                                            min(.4, self.wave * .018)),
                          elite=elite)
            self.enemies.append(enemy)
            if elite:
                self.message = "ELITE CONTACT"
                self.message_timer = 2.0
            return
        self.spawn_queue += 1
        self.spawn_timer = .25

    def _update_enemies(self, dt):
        profile = DIFFICULTIES[self.difficulty]
        for enemy in tuple(self.enemies):
            enemy.update(dt, self.player.x, self.player.z, self.boxes, ARENA_SIZE)
            if aabb_overlap(self.player.x, self.player.z, 1.8, 1.8,
                            enemy.x, enemy.z, enemy.width, enemy.depth):
                if self.damage_timer <= 0 and self.player.invulnerable <= 0:
                    self._damage_player(profile.player_damage)
                dx, dz = enemy.x - self.player.x, enemy.z - self.player.z
                distance = math.hypot(dx, dz) or 1.0
                enemy._try_move(dx / distance * dt * 5, dz / distance * dt * 5,
                                self.boxes, ARENA_SIZE)
            distance = math.hypot(enemy.x - self.player.x, enemy.z - self.player.z)
            if enemy.can_shoot() and distance < 40 and self._line_clear(
                    enemy.x, enemy.z, self.player.x, self.player.z):
                angle = math.atan2(self.player.x - enemy.x,
                                   self.player.z - enemy.z)
                self.enemy_bullets.append(Projectile(enemy.x, enemy.z, angle,
                                                      17.0, team="enemy"))

    def _update_projectiles(self, dt):
        for projectile in tuple(self.player_bullets):
            projectile.update(dt)
            hit = False
            for enemy in tuple(self.enemies):
                if aabb_overlap(projectile.x, projectile.z, 1.5, 1.5,
                                enemy.x, enemy.z, enemy.width, enemy.depth):
                    if enemy.hit():
                        self.enemies.remove(enemy)
                        self._enemy_down(enemy)
                    hit = True
                    break
            if not hit:
                for box in tuple(self.boxes):
                    if aabb_overlap(projectile.x, projectile.z, 1.2, 1.2,
                                    box.x, box.z, box.width, box.depth):
                        box.health -= 1
                        box.color = (1.0, .45, .32)
                        if box.health <= 0:
                            self.boxes.remove(box)
                            self.score += 25
                            self.best = save_if_best(self.score, self.wave,
                                                     self.difficulty)
                        hit = True
                        break
            if (hit or projectile.age >= projectile.lifespan or
                    abs(projectile.x) >= ARENA_SIZE or abs(projectile.z) >= ARENA_SIZE):
                self.player_bullets.remove(projectile)

        for projectile in tuple(self.enemy_bullets):
            projectile.update(dt)
            hit = aabb_overlap(projectile.x, projectile.z, 1.1, 1.1,
                               self.player.x, self.player.z, 1.7, 1.7)
            if hit and self.player.invulnerable <= 0 and self.damage_timer <= 0:
                self._damage_player(DIFFICULTIES[self.difficulty].player_damage)
            blocked = any(aabb_overlap(projectile.x, projectile.z, 1.1, 1.1,
                                       box.x, box.z, box.width, box.depth)
                          for box in self.boxes)
            if (hit or blocked or projectile.age >= projectile.lifespan or
                    abs(projectile.x) >= ARENA_SIZE or abs(projectile.z) >= ARENA_SIZE):
                self.enemy_bullets.remove(projectile)

    def _update_supplies(self, dt):
        for supply in tuple(self.supplies):
            if supply.update(dt):
                self.supplies.remove(supply)
            elif aabb_overlap(self.player.x, self.player.z, 2.4, 2.4,
                              supply.x, supply.z, 1.4, 1.4):
                self.player_health = min(100.0, self.player_health + supply.amount)
                self.score += 20
                self.best = save_if_best(self.score, self.wave, self.difficulty)
                self.message = f"FIELD KIT  +{supply.amount} VITALS"
                self.message_timer = 1.7
                self.supplies.remove(supply)

    def _enemy_down(self, enemy):
        if self.streak_timer > 0:
            self.streak += 1
        else:
            self.streak = 1
        self.streak_timer = 2.6
        self.score += (300 if enemy.elite else 100) * self.wave + max(0, self.streak - 1) * 25
        self.best = save_if_best(self.score, self.wave, self.difficulty)
        if random.random() < .16 and self.player_health < 85:
            self.supplies.append(Loot(enemy.x, enemy.z))
        if self.streak >= 3:
            self.message = f"{self.streak}×  STREAK"
            self.message_timer = 1.2

    def _damage_player(self, damage):
        self.player_health = max(0.0, self.player_health - damage)
        self.damage_timer = .55
        if self.player_health <= 0:
            self.best = save_if_best(self.score, self.wave, self.difficulty)
            self.state = "GAME_OVER"

    def _fire(self):
        if self.player.can_shoot():
            self.player_bullets.append(Projectile(
                self.player.x, self.player.z, self.player.rotation_y,
                speed=44.0, team="player"))

    def _aim_target(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        view, projection = (self.camera.get_view_matrix(),
                            self.camera.get_projection_matrix())
        viewport = glm.vec4(0, 0, self.width, self.height)
        try:
            near = glm.unProject(glm.vec3(mouse_x, self.height - mouse_y, 0),
                                 view, projection, viewport)
            far = glm.unProject(glm.vec3(mouse_x, self.height - mouse_y, 1),
                                view, projection, viewport)
        except Exception:
            return None, None
        direction = far - near
        if abs(direction.y) < 1e-5:
            return None, None
        t = (1.0 - near.y) / direction.y
        if t < 0:
            return None, None
        point = near + direction * t
        return float(point.x), float(point.z)

    def _line_clear(self, x1, z1, x2, z2):
        for i in range(1, 14):
            t = i / 14
            x, z = x1 + (x2 - x1) * t, z1 + (z2 - z1) * t
            if any(aabb_overlap(x, z, .45, .45, box.x, box.z,
                                box.width, box.depth) for box in self.boxes):
                return False
        return True

    def _resize(self, width, height):
        self.width, self.height = width, height
        pygame.display.set_mode((width, height), self.display_flags)
        gl.glViewport(0, 0, width, height)
        self.camera.update_projection(width, height)
        self.ui.resize(width, height)

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.display_flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN
            size = pygame.display.get_desktop_sizes()[0]
        else:
            self.display_flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
            size = (max(WINDOW_MIN[0], min(1600, self.width)),
                    max(WINDOW_MIN[1], min(1000, self.height)))
        surface = pygame.display.set_mode(size, self.display_flags)
        self.width, self.height = surface.get_size()
        gl.glViewport(0, 0, self.width, self.height)
        self.camera.update_projection(self.width, self.height)
        self.ui.resize(self.width, self.height)

    def _draw(self, mouse):
        gameplay = self.state in ("PLAYING", "PAUSED", "GAME_OVER")
        if self.state == "RETURN":
            self.state = "MENU"
            self.keep_host_open = True
            raise _ReturnToHost
        gl.glViewport(0, 0, self.width, self.height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        self._draw_world(gameplay)
        pygame.mouse.set_visible(self.state != "PLAYING")
        self.ui.draw(self.state, self.player_health, self.score, self.best["score"],
                     self.difficulty, self.wave,
                     len(self.enemies) + self.spawn_queue, mouse,
                     elapsed=self.elapsed,
                     message=self.message if self.message_timer > 0 else "",
                     dash_ready=self.player.dash_cooldown <= 0,
                     next_wave=(self.wave_intermission if self.spawn_queue == 0
                                and not self.enemies else 0.0),
                     player_position=(self.player.x, self.player.z),
                     enemy_positions=[(enemy.x, enemy.z, enemy.elite)
                                       for enemy in self.enemies],
                     supply_positions=[(item.x, item.z) for item in self.supplies])

    def _draw_world(self, gameplay):
        floor = glm.translate(glm.mat4(1.0), glm.vec3(0, -0.1, 0))
        floor = glm.scale(floor, glm.vec3(ARENA_SIZE * 2.25, .1,
                                          ARENA_SIZE * 2.25))
        self.renderer.render(self.camera, floor, is_floor=True)

        gl.glDepthMask(gl.GL_FALSE)
        for box in self.boxes:
            self.renderer.render(self.camera, box.get_model_matrix(),
                                 custom_mesh=self.meshes["crate"], is_shadow=True)
        if gameplay:
            for enemy in self.enemies:
                self.renderer.render(self.camera, enemy.get_model_matrix(),
                                     custom_mesh=self.meshes["enemy"], is_shadow=True)
        player_matrix = self.player.get_model_matrix()
        self.renderer.render(self.camera, player_matrix,
                             custom_mesh=self.meshes["player"], is_shadow=True)
        gl.glDepthMask(gl.GL_TRUE)

        for box in self.boxes:
            self.renderer.render(self.camera, box.get_model_matrix(), color=box.color,
                                 custom_mesh=self.meshes["crate"],
                                 texture_id=self.gun_texture)
            box.color = (1.0, 1.0, 1.0)
        for wall in self.walls:
            self.renderer.render(self.camera, wall, color=(.12, .20, .22))
        if gameplay:
            for enemy in self.enemies:
                self.renderer.render(self.camera, enemy.get_model_matrix(),
                                     color=enemy.color, custom_mesh=self.meshes["enemy"],
                                     texture_id=self.car_texture)
                gun = glm.translate(enemy.get_model_matrix(), glm.vec3(0, 2.2, 0))
                gun = glm.rotate(gun, math.pi, glm.vec3(0, 1, 0))
                gun = glm.scale(gun, glm.vec3(2.5 * enemy.model_scale))
                self.renderer.render(self.camera, gun, custom_mesh=self.meshes["enemy_gun"],
                                     texture_id=self.gun_texture)
        if self.player.invulnerable <= 0.12 or not gameplay:
            self.renderer.render(self.camera, player_matrix,
                                 custom_mesh=self.meshes["player"],
                                 texture_id=self.car_texture)
            gun = glm.translate(player_matrix, glm.vec3(0, 1.2, 0))
            gun = glm.rotate(gun, math.pi, glm.vec3(0, 1, 0))
            gun = glm.scale(gun, glm.vec3(2.6))
            self.renderer.render(self.camera, gun, custom_mesh=self.meshes["player_gun"],
                                 texture_id=self.gun_texture)
        if gameplay:
            for bullet in self.player_bullets:
                self.renderer.render(self.camera, bullet.get_model_matrix(),
                                     custom_mesh=self.meshes["bullet"],
                                     texture_id=self.gun_texture)
            for bullet in self.enemy_bullets:
                self.renderer.render(self.camera, bullet.get_model_matrix(),
                                     color=(1.0, .28, .12),
                                     custom_mesh=self.meshes["bullet"],
                                     texture_id=self.gun_texture)
            for supply in self.supplies:
                self.renderer.render(self.camera, supply.get_model_matrix(),
                                     color=(.28, 1.0, .58),
                                     custom_mesh=self.meshes["crate"])

    def _close_gl(self):
        pygame.event.set_grab(False)
        for mesh in getattr(self, "meshes", {}).values():
            mesh.close()
        if hasattr(self, "ui"):
            self.ui.close()
        if hasattr(self, "renderer"):
            self.renderer.close()


class _ReturnToHost(Exception):
    """Signal the embedded mode to hand the display back to RenderX."""


def _make_walls():
    walls = []
    for z, rotation in ((-ARENA_SIZE, math.pi / 2), (ARENA_SIZE, -math.pi / 2)):
        matrix = glm.translate(glm.mat4(1.0), glm.vec3(0, 5, z))
        matrix = glm.rotate(matrix, rotation, glm.vec3(1, 0, 0))
        walls.append(glm.scale(matrix, glm.vec3(ARENA_SIZE * 2, 1, 10)))
    for x, rotation in ((ARENA_SIZE, math.pi / 2), (-ARENA_SIZE, -math.pi / 2)):
        matrix = glm.translate(glm.mat4(1.0), glm.vec3(x, 5, 0))
        matrix = glm.rotate(matrix, rotation, glm.vec3(0, 0, 1))
        walls.append(glm.scale(matrix, glm.vec3(ARENA_SIZE * 2, 1, 10)))
    return walls
