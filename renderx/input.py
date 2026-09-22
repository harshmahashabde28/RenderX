"""Map input to shared actions; keep drag state out of mesh data."""
import pygame
from renderx import config
from renderx.renderer import VIEWPORT

SHAPE_KEYS = {pygame.K_1: "Cube", pygame.K_2: "Pyramid",
              pygame.K_3: "Rectangular prism"}


class Controls:
    def __init__(self):
        self.load_requested = False
        self.screenshot_requested = False
        self.focused = True
        self.drag = None
        self.drag_button = None

    def cancel_drag(self):
        self.drag = None
        self.drag_button = None

    def held_keys(self, scene, keys, dt):
        dt = min(max(dt, 0), config.MAX_DT)
        rotation = config.ROTATION_SPEED * dt
        movement = config.MOVE_SPEED * dt
        scene.rotate((keys[pygame.K_UP] - keys[pygame.K_DOWN]) * rotation,
                     (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * rotation,
                     (keys[pygame.K_e] - keys[pygame.K_q]) * rotation)
        scene.move((keys[pygame.K_d] - keys[pygame.K_a]) * movement,
                   (keys[pygame.K_w] - keys[pygame.K_s]) * movement,
                   (keys[pygame.K_PAGEDOWN] - keys[pygame.K_PAGEUP]) * movement)
        bigger = keys[pygame.K_EQUALS] or keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS]
        smaller = keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]
        scene.resize((bigger - smaller) * config.SCALE_SPEED * dt)

    def update(self, scene, events, keys, dt, panel, mouse_position, modifiers=0):
        """Return False to exit. A reset/selection wins over motion this frame."""
        self.load_requested = False
        self.screenshot_requested = False
        suppress_motion = False
        focus_changed = False
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
                self.focused = False
                focus_changed = True
                self.cancel_drag()
            elif event.type == pygame.WINDOWFOCUSGAINED:
                self.focused = True
                focus_changed = True
                self.cancel_drag()
            elif event.type == pygame.WINDOWLEAVE:
                self.cancel_drag()
                suppress_motion = True
            action = None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if self.focused:
                    if event.key == pygame.K_p:
                        scene.projection = ("Orthographic" if scene.projection ==
                                            "Perspective" else "Perspective")
                    if event.key == pygame.K_x:
                        scene.axes_visible = not scene.axes_visible
                    if event.key == pygame.K_o:
                        self.load_requested = True
                        suppress_motion = True
                        self.cancel_drag()
                    if event.key == pygame.K_F12:
                        self.screenshot_requested = True
                    action = SHAPE_KEYS.get(event.key)
                    if event.key == pygame.K_r:
                        action = "Reset"
            elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                  and self.focused):
                action = panel.hit_test(event.pos)
            if action == "Exit":
                return False
            if action is not None:
                if action == "Reset":
                    scene.reset()
                else:
                    scene.select(action)
                suppress_motion = True
                self.cancel_drag()

        if not self.focused or focus_changed or suppress_motion:
            return True
        self.held_keys(scene, keys, dt)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if VIEWPORT.collidepoint(event.pos) and self.drag is None:
                    if event.button == 1:
                        self.drag = "pan" if modifiers & pygame.KMOD_SHIFT else "xy"
                    elif event.button == 2:
                        self.drag = "pan"
                    elif event.button == 3:
                        self.drag = "z"
                    if self.drag:
                        self.drag_button = event.button
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == self.drag_button:
                    self.cancel_drag()
            elif event.type == pygame.MOUSEMOTION:
                if not VIEWPORT.collidepoint(event.pos):
                    self.cancel_drag()
                elif self.drag:
                    dx, dy = event.rel
                    if self.drag == "pan":
                        scene.move(dx * config.DRAG_MOVE, -dy * config.DRAG_MOVE)
                    elif self.drag == "xy":
                        scene.rotate(-dy * config.DRAG_ROTATION,
                                     dx * config.DRAG_ROTATION)
                    else:
                        scene.rotate(dz=dx * config.DRAG_ROTATION)
            elif event.type == pygame.MOUSEWHEEL:
                if VIEWPORT.collidepoint(mouse_position):
                    scene.resize(event.y * config.WHEEL_SCALE)
        return True
