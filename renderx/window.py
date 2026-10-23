"""Fit the dashboard to the desktop and map resized mouse coordinates safely."""
import os

import pygame
from renderx.dashboard import SIZE
from renderx import config
from renderx.ui.theme import METRICS


def enable_dpi_awareness():
    """Ask Windows to keep the SDL window at native pixel density."""
    if os.name != 'nt':
        return
    try:
        import ctypes
        set_awareness = ctypes.windll.user32.SetProcessDpiAwarenessContext
        set_awareness.argtypes = [ctypes.c_void_p]
        set_awareness.restype = ctypes.c_bool
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        set_awareness(ctypes.c_void_p(-4))
    except (AttributeError, OSError, ValueError):
        # Older Windows versions or a host manifest may have already set it.
        pass


def initial_size(desktop):
    """Open large enough for the docks while respecting the desktop where possible."""
    available = (max(1, desktop[0] - 80), max(1, desktop[1] - 120))
    scale = min(1.0, available[0] / SIZE[0], available[1] / SIZE[1])
    return (max(METRICS["min_width"], int(SIZE[0] * scale)),
            max(METRICS["min_height"], int(SIZE[1] * scale)))


class WindowView:
    def __init__(self, size, canvas_size=None):
        self.canvas_size = tuple(canvas_size or SIZE)
        self.resize(size, self.canvas_size)

    def resize(self, size, canvas_size=None):
        if canvas_size is not None:
            self.canvas_size = tuple(max(1, int(value)) for value in canvas_size)
        self.scale = min(max(1, size[0]) / self.canvas_size[0],
                         max(1, size[1]) / self.canvas_size[1])
        self.rect = pygame.Rect(0, 0, max(1, int(self.canvas_size[0] * self.scale)),
                                max(1, int(self.canvas_size[1] * self.scale)))
        self.rect.center=(size[0]//2,size[1]//2)

    def point(self,position):
        return ((position[0]-self.rect.x)*self.canvas_size[0]/self.rect.width,
                (position[1]-self.rect.y)*self.canvas_size[1]/self.rect.height)

    def event(self,event):
        if event.type not in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP,pygame.MOUSEMOTION):
            return event
        values=event.dict.copy()
        values['pos']=self.point(event.pos)
        if 'rel' in values:
            values['rel']=(event.rel[0]*self.canvas_size[0]/self.rect.width,
                           event.rel[1]*self.canvas_size[1]/self.rect.height)
        return pygame.event.Event(event.type,values)

    def draw(self,display,canvas):
        display.fill(config.APP_BG)
        if self.rect.size == canvas.get_size() and self.rect.topleft == (0, 0):
            display.blit(canvas,self.rect)
        else:
            # The app normally renders at display size, so this is only used
            # when a caller deliberately supplies a differently sized canvas.
            display.blit(pygame.transform.scale(canvas,self.rect.size),self.rect)
