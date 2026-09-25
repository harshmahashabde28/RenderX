"""Topology, learning logic and whole-app checks for the compact final release."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pygame
from renderx.models import make_library
from renderx.mesh import Mesh, inspect_mesh, validate_mesh
from renderx.shapes import sphere, torus, prism, surface, helix
from renderx.curriculum import Challenge, QUESTIONS, LESSONS
from renderx.experiments import clipping_experiment, order_experiment
from renderx.scene import Scene
from renderx.learning import LearningState, MODES
from renderx.obj_loader import load_obj
from renderx.app import run, load_sample
from renderx.input import Controls
from renderx.ui import Panel
from renderx.lab import handle_lab, draw_lab, wide_panel, DEMO_VIEWS
from renderx.camera import Camera
from renderx.screenshots import save_screenshot


def key(value): return pygame.event.Event(pygame.KEYDOWN,key=value)


class ShapeTests(unittest.TestCase):
    def test_library_connectivity_and_size(self):
        models=make_library()
        self.assertEqual(len(models),15)
        for name,mesh in models.items():
            with self.subTest(name=name):
                validate_mesh(mesh)
                report=inspect_mesh(mesh)
                self.assertEqual(report['duplicate_edges'],0)
                self.assertEqual(report['invalid_edges'],0)
                self.assertEqual(report['disconnected'],0)
                self.assertLess(len(mesh.vertices),200)
                self.assertIsNotNone(mesh.faces)

    def test_closed_topologies(self):
        for name,mesh in make_library().items():
            if name in ('Plane','Saddle','Ripple','Helix'): continue
            expected=0 if name=='Torus' else 2
            self.assertEqual(len(mesh.vertices)-len(mesh.edges)+len(mesh.faces),expected,name)

    def test_parameter_counts_and_dimensions(self):
        mesh=prism(radius=2,height=3,segments=8)
        self.assertEqual((len(mesh.vertices),len(mesh.edges),len(mesh.faces)),(16,24,10))
        self.assertEqual(inspect_mesh(mesh)['size'],(4,3,4))
        self.assertEqual(len(sphere(segments=8,rings=4).vertices),26)
        self.assertEqual(len(torus(segments=8,rings=6).vertices),48)
        self.assertEqual(len(surface(segments=4).faces),16)
        self.assertEqual(len(helix(segments=24).edges),24)

    def test_invalid_parameters(self):
        for call in (lambda:sphere(radius=-1),lambda:sphere(rings=0),lambda:torus(tube=2),
                     lambda:prism(segments=100000),lambda:surface(kind='oops'),
                     lambda:helix(turns=0),lambda:prism(top_radius=-1)):
            with self.assertRaises(ValueError): call()

    def test_inspector_diagnostics_without_mutation(self):
        mesh=Mesh([(0,0,0),(1,0,0),(2,2,2)],[(0,1)])
        mesh.edges += [(1,0),(0,99)]
        before=deepcopy(mesh)
        report=inspect_mesh(mesh)
        self.assertEqual((report['duplicate_edges'],report['invalid_edges'],report['disconnected']),(1,1,1))
        self.assertEqual(report['center'],(1,1,1))
        self.assertEqual(mesh,before)

    def test_obj_faces_normalization_and_warnings(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.obj'
            path.write_text('v 0 0 0\nv 4 0 0\nv 0 4 0\nusemtl ignored\nf 1 2 3\n')
            mesh=load_obj(path)
            self.assertEqual(mesh.faces,[[0,1,2]])
            self.assertAlmostEqual(mesh.normalization_scale,.5)
            self.assertIn('usemtl',mesh.warnings[0])


class CurriculumTests(unittest.TestCase):
    def test_curriculum_complete(self):
        self.assertEqual(len(LESSONS),14)
        for lesson in LESSONS:
            self.assertEqual(len(lesson),6)
            self.assertTrue(all(lesson))

    def test_challenge_feedback_progress_score_retry(self):
        challenge=Challenge()
        for index,question in enumerate(QUESTIONS):
            challenge.choice=question[2]
            challenge.submit()
            self.assertTrue(challenge.answered)
            self.assertEqual(challenge.score,index+1)
            challenge.choose(1)
            self.assertEqual(challenge.score,index+1)
            challenge.submit()
        self.assertTrue(challenge.done)
        challenge.submit()
        self.assertEqual(challenge.score,10)
        challenge.retry()
        self.assertEqual(challenge,Challenge())
        challenge.choice=1
        challenge.submit()
        self.assertEqual(challenge.score,0)
        self.assertTrue(challenge.answered)

    def test_experiment_known_answers(self):
        self.assertEqual(clipping_experiment(-2)[3],'hidden')
        self.assertEqual(clipping_experiment(2)[3],'complete')
        a,b,clipped,state,t=clipping_experiment(0)
        self.assertEqual(state,'partial')
        self.assertAlmostEqual(t,4/7)
        self.assertEqual(clipped[0][2],.1)
        from math import pi
        normal,alternative=order_experiment((1,0,0),Scene(angles=(0,0,pi/2),position=(1,0,5),scale=2))
        for actual,expected in zip(normal,(1,2,5)): self.assertAlmostEqual(actual,expected)
        for actual,expected in zip(alternative,(0,4,10)): self.assertAlmostEqual(actual,expected)


class FinalInteractionTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init(); pygame.font.init()
        self.models=make_library(); self.scene=Scene(); self.learning=LearningState()
        self.controls=Controls(); self.panel=Panel()

    def tearDown(self): pygame.quit()

    def press(self,value):
        old=self.learning.mode
        handle_lab([key(value)],self.scene,self.models,self.learning,self.controls,
                   self.panel,old,load_sample)

    def test_lesson_navigation_answers_and_clipping(self):
        self.press(pygame.K_F5)
        self.assertEqual(self.learning.mode,'Lesson')
        self.press(pygame.K_LEFTBRACKET)
        self.assertEqual(self.learning.lesson_index,13)
        self.assertEqual(self.scene.shape,'OBJ house')
        self.press(pygame.K_RETURN)
        self.assertEqual(self.learning.lesson_index,0)
        self.press(pygame.K_h)
        self.assertTrue(self.learning.lesson_answer)
        self.learning.lesson_index=11
        self.press(pygame.K_u)
        self.assertAlmostEqual(self.learning.clip_depth,.2)
        self.press(pygame.K_j)
        self.assertAlmostEqual(self.learning.clip_depth,0)

    def test_shape_browser_and_focus(self):
        names=list(self.models)
        for name in names[1:]:
            self.press(pygame.K_n)
            self.assertEqual(self.scene.shape,name)
        self.press(pygame.K_n)
        self.assertEqual(self.scene.shape,'Cube')
        self.controls.focused=False
        self.press(pygame.K_F5)
        self.assertEqual(self.learning.mode,'Explore')

    def test_every_lesson_and_demo_screen_renders(self):
        self.learning.mode='Lesson'
        for i in range(14):
            self.learning.lesson_index=i
            self.learning.lesson_answer=True
            draw_lab(pygame.Surface((1340,740)),self.models['Cube'],self.scene,Camera(),
                     self.learning,self.panel,0)
        self.press(pygame.K_F7)
        for i in range(8):
            self.assertEqual(self.learning.demo_index,i)
            width=1340 if wide_panel(self.learning) else 1120
            draw_lab(pygame.Surface((width,740)),self.models[self.scene.shape],self.scene,Camera(),
                     self.learning,self.panel,0)
            if i<7: self.press(pygame.K_RETURN)
        self.assertTrue(self.controls.screenshot_requested)
        self.assertEqual(self.scene.shape,'OBJ house')

    def test_real_app_all_modes_help_obj_challenge_demo_export_exit(self):
        frames=[[key(pygame.K_F4),key(pygame.K_n)],[key(pygame.K_F5)],
                [key(pygame.K_RIGHTBRACKET),key(pygame.K_h)],
                [key(pygame.K_F6)],[key(pygame.K_k),key(pygame.K_RETURN)],
                [key(pygame.K_RETURN),key(pygame.K_t)],[key(pygame.K_F7)]]
        frames += [[key(pygame.K_RETURN)] for _ in range(7)]
        frames += [[key(pygame.K_F1),key(pygame.K_h)], [key(pygame.K_h),key(pygame.K_o)],
                   [key(pygame.K_F2)],[key(pygame.K_F3)],[key(pygame.K_ESCAPE)]]
        with tempfile.TemporaryDirectory() as folder:
            with patch('pygame.event.get',side_effect=frames), \
                 patch('pygame.key.get_pressed',return_value=defaultdict(int)), \
                 patch('renderx.app.save_screenshot',side_effect=lambda s:save_screenshot(s,folder)):
                with patch('renderx.app.initial_size', return_value=(1360, 900)):
                    run()
            self.assertEqual(len(list(Path(folder).glob('*.png'))),1)
        self.assertFalse(pygame.display.get_init())
