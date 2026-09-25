"""Fit the dashboard to the desktop and map resized mouse coordinates safely."""
import pygame
from renderx.dashboard import SIZE


def initial_size(desktop):
    """Leave room for the title bar/taskbar; never force a 900-pixel-tall window."""
    available=(max(1,desktop[0]-80),max(1,desktop[1]-120))
    scale=min(1180/SIZE[0],780/SIZE[1],available[0]/SIZE[0],available[1]/SIZE[1])
    return (max(1,int(SIZE[0]*scale)),max(1,int(SIZE[1]*scale)))


class WindowView:
    def __init__(self,size):
        self.resize(size)

    def resize(self,size):
        self.scale=min(max(1,size[0])/SIZE[0],max(1,size[1])/SIZE[1])
        self.rect=pygame.Rect(0,0,max(1,int(SIZE[0]*self.scale)),max(1,int(SIZE[1]*self.scale)))
        self.rect.center=(size[0]//2,size[1]//2)

    def point(self,position):
        return ((position[0]-self.rect.x)*SIZE[0]/self.rect.width,
                (position[1]-self.rect.y)*SIZE[1]/self.rect.height)

    def event(self,event):
        if event.type not in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEBUTTONUP,pygame.MOUSEMOTION):
            return event
        values=event.dict.copy()
        values['pos']=self.point(event.pos)
        if 'rel' in values:
            values['rel']=(event.rel[0]*SIZE[0]/self.rect.width,event.rel[1]*SIZE[1]/self.rect.height)
        return pygame.event.Event(event.type,values)

    def draw(self,display,canvas):
        display.fill((10,16,27))
        display.blit(pygame.transform.smoothscale(canvas,self.rect.size),self.rect)
