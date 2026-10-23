"""Resizable OpenGL survival shooter adapted for the RenderX application."""

from pathlib import Path
import math
import random

import glm
import OpenGL.GL as gl
import pygame

from renderx.input_map import MOUSE_BUTTONS, SHOOTER_KEYS

from .engine.camera import Camera
from .engine.mesh import Mesh
from .engine.renderer import Renderer
from .engine.ui_renderer import UIRenderer
from renderx.audio import AudioManager
from renderx.ui.identity import set_window_identity
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
BUFF_DURATIONS = {"rapid": 12.0, "shield": 10.0, "overdrive": 9.0}
_VEHICLE_COMBAT = {
    "scout": (-1, 1.30, 1.18),
    "striker": (0, 1.0, 1.0),
    "bulwark": (3, .72, 1.22),
    "wraith": (1, 1.34, .82),
}


def run_shooter(audio=None) -> bool:
    """Run the standalone GL mode; return False only when the app should close."""
    owns_audio = audio is None
    if audio is None:
        audio = AudioManager()
    audio.switch_music("shooter")
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
    set_window_identity("RenderX | Breakpoint")
    pygame.mouse.set_visible(True)
    try:
        return ShooterGame(size, flags, audio).run()
    finally:
        if owns_audio:
            audio.switch_music(None)
        pygame.mouse.set_visible(True)
        pygame.event.clear()
        pygame.display.quit()
        pygame.display.init()


class ShooterGame:
    def __init__(self, size, display_flags, audio=None):
        self.width, self.height = size
        self.display_flags = display_flags
        self.audio = audio
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
        self.buffs = {name: 0.0 for name in BUFF_DURATIONS}
        self.footstep_timer = 0.0
        self.audio_drag = False
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
        self.ui = UIRenderer(self.width, self.height, ROOT / "shaders", audio)
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
                        if self.audio_drag and self.audio:
                            self.audio.save_settings()
                        self.audio_drag = False
                        if self.state == "PLAYING":
                            self.state = "PAUSED"
                    elif event.type == pygame.KEYDOWN:
                        if event.key == SHOOTER_KEYS["fullscreen"]:
                            self._toggle_fullscreen()
                        elif event.key == SHOOTER_KEYS["pause"]:
                            if self.state == "PLAYING":
                                self.state = "PAUSED"
                                self._play_sound("ui_click")
                            elif self.state == "PAUSED":
                                self.state = "PLAYING"
                                self._play_sound("ui_click")
                            elif self.state == "CONFIRM_RETURN":
                                self.state = "PAUSED"
                                self._play_sound("ui_click")
                        elif event.key in SHOOTER_KEYS["dash"]:
                            if self.state == "PLAYING":
                                self._dash()
                        elif event.key == SHOOTER_KEYS["fire"] and self.state != "PLAYING":
                            self._activate(self.ui.action_at(mouse))
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        action = (self.ui.action_at(event.pos)
                                  if event.button == MOUSE_BUTTONS["primary"] else None)
                        if action == "audio_music":
                            self._activate(action)
                        elif action == "audio_volume":
                            self.audio_drag = True
                            self._set_audio_volume(event.pos, persist=False)
                            self._play_sound("ui_click")
                        elif (self.state == "PLAYING" and
                              event.button == MOUSE_BUTTONS["primary"]):
                            self._fire()
                        elif (self.state != "PLAYING" and
                              event.button == MOUSE_BUTTONS["primary"]):
                            self._activate(action)
                    elif event.type == pygame.MOUSEMOTION and self.audio_drag:
                        self._set_audio_volume(event.pos, persist=False)
                    elif (event.type == pygame.MOUSEBUTTONUP and
                          event.button == MOUSE_BUTTONS["primary"]):
                        if self.audio_drag and self.audio:
                            self.audio.save_settings()
                        self.audio_drag = False

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
        if action is None:
            return
        self._play_sound("ui_click")
        if action == "audio_music":
            if self.audio:
                self.audio.toggle_music()
            return
        if action == "start":
            self.state = "DIFFICULTY"
        elif action and action.startswith("difficulty_"):
            self.difficulty = action.removeprefix("difficulty_")
        elif action == "launch":
            self._start_run()
        elif action == "back":
            self.state = "MENU"
        elif action == "return":
            if self.state in ("PLAYING", "PAUSED"):
                self.state = "CONFIRM_RETURN"
            else:
                self.best = save_if_best(self.score, self.wave, self.difficulty)
                self.state = "RETURN"
        elif action == "cancel_return":
            self.state = "PAUSED"
        elif action == "leave_return":
            self.best = save_if_best(self.score, self.wave, self.difficulty)
            self._clear_combat()
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
        self.buffs = {name: 0.0 for name in BUFF_DURATIONS}
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
        self._play_sound("confirm")
        self.spawn_queue = enemy_count_for_wave(self.wave)
        self.spawn_timer = .25
        if self.wave % 5 == 0:
            self.message = f"BOSS WAVE  {self.wave:02d}  ·  IRON WRAITH"
        elif self.wave == 3:
            self.message = "WAVE  03  ·  STRIKERS DEPLOYED"
        elif self.wave == 6:
            self.message = "WAVE  06  ·  BULWARKS DEPLOYED"
        elif self.wave == 8:
            self.message = "WAVE  08  ·  WRAITHS DEPLOYED"
        else:
            self.message = f"WAVE  {self.wave:02d}"
        self.message_timer = 2.0
        self.wave_intermission = 0.0

    def _update(self, dt):
        keys = pygame.key.get_pressed()
        self.elapsed += dt
        self.damage_timer = max(0.0, self.damage_timer - dt)
        self.message_timer = max(0.0, self.message_timer - dt)
        self.streak_timer = max(0.0, self.streak_timer - dt)
        for name in self.buffs:
            self.buffs[name] = max(0.0, self.buffs[name] - dt)
        self.player.fire_rate = .095 if self.buffs["rapid"] > 0 else .17
        self.player.speed = 12.0 if self.buffs["overdrive"] > 0 else 8.5
        if self.streak_timer == 0:
            self.streak = 0

        aim_x, aim_z = ((None, None) if self.audio_drag else self._aim_target())
        if aim_x is not None:
            self.player.aim_at(aim_x, aim_z)
        prior_position = self.player.x, self.player.z
        self.player.move(keys, dt, self.boxes, ARENA_SIZE)
        self.footstep_timer = max(0.0, self.footstep_timer - dt)
        if ((self.player.x, self.player.z) != prior_position and
                self.footstep_timer <= 0.0):
            self._play_sound("footstep", cooldown=0.18)
            self.footstep_timer = 0.38
        self.camera.follow_target(self.player.x, self.player.z, dt)
        if pygame.mouse.get_pressed()[0] or keys[SHOOTER_KEYS["fire"]]:
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
            boss = self.wave % 5 == 0 and self.spawn_queue == 0
            first_spawn = (self.spawn_queue == enemy_count_for_wave(self.wave) - 1)
            kind = ("boss" if boss else
                    self._vehicle_for_wave(first_spawn=first_spawn))
            base_health = profile.enemy_health + max(0, (self.wave - 1) // 4)
            base_speed = profile.enemy_speed + min(.9, self.wave * .035)
            base_fire_interval = max(.75, profile.enemy_fire_interval -
                                     min(.4, self.wave * .018))
            if boss:
                health = profile.enemy_health * 14 + self.wave
                speed = max(.8, base_speed * .72)
                fire_interval = 2.2
            else:
                health_bonus, speed_scale, fire_scale = _VEHICLE_COMBAT[kind]
                health = max(1, base_health + health_bonus)
                speed = base_speed * speed_scale
                fire_interval = max(.8, base_fire_interval * fire_scale)
            enemy = Enemy(x, z, health=health, speed=speed,
                          fire_interval=fire_interval, elite=boss, kind=kind)
            self.enemies.append(enemy)
            if boss:
                self.message = "IRON WRAITH  ·  ENGAGED"
                self.message_timer = 2.0
            return
        self.spawn_queue += 1
        self.spawn_timer = .25

    def _vehicle_for_wave(self, *, first_spawn=False):
        """Unlock recognizable enemy chassis in paced steps across the run."""
        if self.wave <= 2:
            return "scout"
        if first_spawn and self.wave == 3:
            return "striker"
        if first_spawn and self.wave == 6:
            return "bulwark"
        if first_spawn and self.wave == 8:
            return "wraith"
        if self.wave < 6:
            return random.choice(("scout", "striker", "striker"))
        if self.wave < 8:
            return random.choice(("striker", "bulwark", "bulwark"))
        return random.choice(("striker", "bulwark", "wraith", "wraith"))

    def _update_enemies(self, dt):
        profile = DIFFICULTIES[self.difficulty]
        for enemy in tuple(self.enemies):
            enemy.update(dt, self.player.x, self.player.z, self.boxes, ARENA_SIZE)
            phase = enemy.update_boss_phase()
            if phase is not None:
                self.message = f"IRON WRAITH  ·  PHASE {phase}"
                self.message_timer = 1.8
                self._play_sound("confirm")
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
                spread = ((-.16, 0.0, .16) if enemy.is_boss and enemy.phase >= 3
                          else (-.13, .13) if enemy.is_boss and enemy.phase == 2
                          else (0.0,))
                speed = 14.5 if enemy.is_boss else 17.0
                for offset in spread:
                    self.enemy_bullets.append(Projectile(
                        enemy.x, enemy.z, angle + offset, speed, team="enemy"))
                self._play_sound("enemy_shoot", cooldown=.45 if enemy.is_boss else .1)

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
                    else:
                        self._play_sound("impact", cooldown=0.025)
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
                        self._play_sound("impact", cooldown=0.025)
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
                self.score += 20
                self.best = save_if_best(self.score, self.wave, self.difficulty)
                if supply.kind == "health":
                    self.player_health = min(100.0,
                                             self.player_health + supply.amount)
                    self.message = f"FIELD KIT  +{supply.amount} VITALS"
                    self._play_sound("health_pickup")
                else:
                    self.buffs[supply.kind] = max(
                        self.buffs[supply.kind], BUFF_DURATIONS[supply.kind])
                    buff_name = {"rapid": "RAPID FIRE", "shield": "SHIELD",
                                 "overdrive": "OVERDRIVE"}[supply.kind]
                    self.message = f"{buff_name}  ONLINE"
                    self._play_sound("pickup")
                self.message_timer = 1.7
                self.supplies.remove(supply)

    def _enemy_down(self, enemy):
        self._play_sound("enemy_down")
        if self.streak_timer > 0:
            self.streak += 1
        else:
            self.streak = 1
        self.streak_timer = 2.6
        score_value = 500 if enemy.is_boss else 300 if enemy.elite else 100
        self.score += score_value * self.wave + max(0, self.streak - 1) * 25
        self.best = save_if_best(self.score, self.wave, self.difficulty)
        if enemy.is_boss:
            self.supplies.append(Loot(enemy.x - 2.8, enemy.z, amount=40))
            buff = random.choice(tuple(BUFF_DURATIONS))
            self.supplies.append(Loot(enemy.x + 2.8, enemy.z, kind=buff))
            self.message = "IRON WRAITH  ·  DESTROYED"
            self.message_timer = 2.8
        elif self.player_health < 85 and random.random() < .16:
            self.supplies.append(Loot(enemy.x, enemy.z))
        elif random.random() < .12:
            self.supplies.append(Loot(enemy.x, enemy.z,
                                      kind=random.choice(tuple(BUFF_DURATIONS))))
        if self.streak >= 3 and not enemy.is_boss:
            self.message = f"{self.streak}×  STREAK"
            self.message_timer = 1.2

    def _damage_player(self, damage):
        if self.buffs["shield"] > 0:
            damage *= .35
        self.player_health = max(0.0, self.player_health - damage)
        self.damage_timer = .55
        if self.player_health <= 0:
            self._play_sound("player_down")
            self.best = save_if_best(self.score, self.wave, self.difficulty)
            self.state = "GAME_OVER"
        else:
            self._play_sound("impact")

    def _fire(self):
        if self.player.can_shoot():
            self.player_bullets.append(Projectile(
                self.player.x, self.player.z, self.player.rotation_y,
                speed=44.0, team="player"))
            self._play_sound("shoot", cooldown=0.06)

    def _dash(self):
        if self.player.dash(pygame.key.get_pressed(), *self._aim_target()):
            self._play_sound("dash")

    def _set_audio_volume(self, position, *, persist):
        if not self.audio:
            return
        rect = self.ui.buttons.get("audio_volume")
        if rect is None:
            return
        ratio = max(0.0, min(1.0,
                             (position[0] - rect.x) / max(1, rect.width)))
        self.audio.set_volume(ratio, persist=persist)

    def _play_sound(self, name, *, cooldown=0.0):
        if self.audio:
            self.audio.play(name, cooldown=cooldown)

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
        boss = next((enemy for enemy in self.enemies if enemy.is_boss), None)
        boss_status = (("IRON WRAITH", boss.health, boss.max_health, boss.phase)
                       if boss else None)
        active_buffs = {name: time_left for name, time_left in self.buffs.items()
                        if time_left > 0}
        self.ui.draw(self.state, self.player_health, self.score, self.best["score"],
                     self.difficulty, self.wave,
                     len(self.enemies) + self.spawn_queue, mouse,
                     elapsed=self.elapsed,
                     message=self.message if self.message_timer > 0 else "",
                     dash_ready=self.player.dash_cooldown <= 0,
                     next_wave=(self.wave_intermission if self.spawn_queue == 0
                                and not self.enemies else 0.0),
                     player_position=(self.player.x, self.player.z),
                     enemy_positions=[(enemy.x, enemy.z, enemy.kind)
                                       for enemy in self.enemies],
                     supply_positions=[(item.x, item.z, item.kind)
                                       for item in self.supplies],
                     buffs=active_buffs, boss=boss_status)

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
                gun = glm.translate(glm.mat4(1.0), glm.vec3(
                    enemy.x, 2.2 * enemy.model_scale, enemy.z))
                gun = glm.rotate(gun, enemy.rotation_y, glm.vec3(0, 1, 0))
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
                                     color=supply.color,
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
