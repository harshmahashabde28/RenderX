"""Verify desktop fit, resized hit targets, drag distances and capture dimensions."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import unittest
from pathlib import Path
from unittest.mock import patch
import pygame
from renderx.window import initial_size, WindowView
from renderx.dashboard import SIZE, Dashboard
from renderx.ui import Panel
from renderx.scene import Scene
from renderx.models import make_library
from renderx.learning import LearningState
from renderx.input import Controls
from renderx.app import run


class WindowTests(unittest.TestCase):
    def tearDown(self): pygame.quit()

    def test_initial_size_fits_common_laptop_desktops(self):
        for desktop in ((1366,768),(1920,1080),(1536,864),(1024,768)):
            width,height=initial_size(desktop)
            self.assertLessEqual(width,desktop[0]-80)
            self.assertLessEqual(height,desktop[1]-120)
            self.assertLessEqual(width,1180)
            self.assertAlmostEqual(width/height,SIZE[0]/SIZE[1],places=2)

    def test_letterboxed_click_and_drag_map_to_same_controls(self):
        pygame.font.init()
        panel=Panel(); ui=Dashboard(panel); scene=Scene(); models=make_library()
        state=LearningState(); controls=Controls()
        ui.layout(scene,models,state)
        for size in ((980,648),(1180,780),(1500,700),(700,900)):
            view=WindowView(size)
            logical=ui.buttons[('move',2,-1)].center
            physical=(view.rect.x+logical[0]*view.rect.width/SIZE[0],view.rect.y+logical[1]*view.rect.height/SIZE[1])
            event=view.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=physical))
            before=scene.position[2]
            ui.events([event],scene,models,state,controls)
            self.assertAlmostEqual(scene.position[2],before-.2)
            motion=view.event(pygame.event.Event(pygame.MOUSEMOTION,pos=physical,rel=(view.rect.width/136,view.rect.height/90),buttons=(1,0,0)))
            self.assertAlmostEqual(motion.rel[0],10)
            self.assertAlmostEqual(motion.rel[1],10)
            self.assertLess(view.point((view.rect.left-5,view.rect.top))[0],0)

    def test_real_app_resize_screenshot_and_resized_exit_button(self):
        pygame.font.init()
        ui=Dashboard(Panel()); ui.layout(Scene(),make_library(),LearningState())
        view=WindowView((980,648))
        logical=ui.buttons[('key',pygame.K_ESCAPE)].center
        exit_position=(view.rect.x+logical[0]*view.rect.width/SIZE[0],view.rect.y+logical[1]*view.rect.height/SIZE[1])
        frames=[[],[pygame.event.Event(pygame.VIDEORESIZE,w=980,h=648,size=(980,648))],
                [pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F12)],
                [pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=exit_position)]]
        sizes=[]
        def save(surface):
            sizes.append(surface.get_size()); return Path('resized.png')
        with patch('pygame.event.get',side_effect=frames),patch('renderx.app.save_screenshot',side_effect=save):
            run()
        self.assertEqual(sizes,[(980,648)])
        self.assertFalse(pygame.display.get_init())
