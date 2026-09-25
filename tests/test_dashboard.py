"""Exercise visible controls, shared commands and canvas coordinate mapping."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import unittest
from unittest.mock import patch
import pygame
from renderx.dashboard import Dashboard, SIZE, VIEW
from renderx.ui import Panel
from renderx.scene import Scene
from renderx.models import make_library
from renderx.learning import LearningState, MODES
from renderx.input import Controls
from renderx.lab import handle_lab
from renderx.app import load_sample, run


class DashboardTests(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.panel=Panel(); self.ui=Dashboard(self.panel)
        self.scene=Scene(); self.models=make_library()
        self.state=LearningState(); self.controls=Controls()

    def tearDown(self): pygame.quit()

    def click(self,action):
        self.ui.layout(self.scene,self.models,self.state)
        event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.ui.buttons[action].center)
        return self.ui.events([event],self.scene,self.models,self.state,self.controls)

    def test_all_modes_and_shapes_have_buttons(self):
        self.ui.layout(self.scene,self.models,self.state)
        for i,mode in enumerate(MODES):
            events=self.click(('key',pygame.K_F1+i))
            old=self.state.mode
            handle_lab(events,self.scene,self.models,self.state,self.controls,self.panel,old,load_sample)
            self.assertEqual(self.state.mode,mode)
        for name in self.models:
            if name != 'OBJ house':
                self.click(('shape',name)); self.assertEqual(self.scene.shape,name)

    def test_transforms_preserve_model_and_use_scene_limits(self):
        original=list(self.models['Cube'].vertices)
        self.click(('rotate',0,1)); self.assertNotEqual(self.scene.angles,Scene().angles)
        self.click(('move',2,-1)); self.assertAlmostEqual(self.scene.position[2],4.8)
        for _ in range(20): self.click(('scale',1))
        self.assertEqual(self.scene.scale,1.3)
        self.assertEqual(self.models['Cube'].vertices,original)
        self.assertIsNone(self.controls.drag)

    def test_pipeline_choices_and_challenge_feedback(self):
        self.state.mode='Pipeline'; self.click(('stage',6))
        self.assertEqual(self.state.stage_index,6)
        self.state.mode='Challenge'; self.click(('choice',0)); self.click(('submit',))
        self.assertEqual(self.state.challenge.score,1)
        self.click(('choice',1)); self.assertEqual(self.state.challenge.choice,0)
        self.click(('submit',)); self.assertEqual(self.state.challenge.index,1)
        self.click(('hint',)); self.assertTrue(self.state.challenge.hint)
        self.click(('retry',)); self.assertEqual(self.state.challenge.answers,[])

    def test_canvas_mapping_and_focus_protection(self):
        self.assertEqual(self.ui.map_position(VIEW.center),(410,370))
        self.assertEqual(self.ui.map_position((1000,200)),(-100,-100))
        self.ui.events([pygame.event.Event(pygame.WINDOWFOCUSLOST)],self.scene,self.models,self.state,self.controls)
        before=self.scene.position
        self.click(('move',2,1)); self.assertEqual(self.scene.position,before)

    def test_help_modal_blocks_covered_controls(self):
        self.click(('help',)); self.assertTrue(self.state.help_visible)
        self.ui.layout(self.scene,self.models,self.state)
        self.assertEqual(list(self.ui.buttons),[('help',)])
        self.click(('help',)); self.assertFalse(self.state.help_visible)

    def test_mouse_only_app_mode_shape_capture_exit(self):
        self.ui.layout(self.scene,self.models,self.state)
        click=lambda action: pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.ui.buttons[action].center)
        frames=[[],[click(('key',pygame.K_F2))],[click(('shape','Torus'))],
                [click(('key',pygame.K_F12))],[click(('key',pygame.K_ESCAPE))]]
        with patch('pygame.event.get',side_effect=frames),patch('renderx.app.save_screenshot') as save:
            from pathlib import Path
            sizes=[]
            def capture(surface):
                sizes.append(surface.get_size())
                return Path('test.png')
            save.side_effect=capture
            with patch('renderx.app.initial_size', return_value=(1360, 900)):
                run()
            self.assertEqual(save.call_count,1)
            self.assertEqual(sizes,[SIZE])
        self.assertFalse(pygame.display.get_init())
