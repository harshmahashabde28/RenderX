"""Projection Quest math, progression, clipping gates, and Pygame drawing."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')

from collections import defaultdict
from math import pi, radians, tau
import unittest

import pygame

from renderx.camera import Camera
from renderx.dashboard import Dashboard
from renderx.input import Controls
from renderx.models import make_cube, make_library
from renderx.quest import (CHALLENGES, QuestState,
                           alignment_progress, angle_diff, clipped_edge_count,
                           is_aligned, make_challenge_scene)
from renderx.quest_ui import (draw_comparison_challenge, draw_near_plane_guide,
                              draw_quest_card, draw_quest_progress, _font)
from renderx.scene import Scene
from renderx.ui import Panel


class QuestMathTests(unittest.TestCase):
    def test_angle_distance_wraps_at_full_turn(self):
        self.assertAlmostEqual(angle_diff(0, tau), 0)
        self.assertAlmostEqual(angle_diff(tau - 0.1, 0.1), 0.2)
        self.assertAlmostEqual(angle_diff(0.1, tau - 0.1), 0.2)

    def test_alignment_threshold_is_applied_per_axis(self):
        target = (0.0, pi, 0.0)
        self.assertTrue(is_aligned((tau - radians(10), pi + radians(14), 0.0), target))
        self.assertTrue(is_aligned((radians(15), pi, 0.0), target))
        self.assertFalse(is_aligned((radians(15.1), pi, 0.0), target))
        self.assertGreater(alignment_progress((radians(10), pi, 0), target), 0.9)

    def test_challenge_definitions_are_complete_and_valid(self):
        self.assertEqual(len(CHALLENGES), 3)
        self.assertEqual([challenge.kind for challenge in CHALLENGES],
                         ['align', 'choice', 'choice_gated'])
        for challenge in CHALLENGES:
            self.assertIn(challenge.setup_projection, ('Perspective', 'Orthographic'))
            self.assertGreater(challenge.setup_depth, 0)
            self.assertTrue(challenge.allowed_controls)
            if challenge.choices:
                self.assertIn(challenge.correct, range(len(challenge.choices)))
            else:
                self.assertIsNone(challenge.correct)

    def test_clipping_detector_uses_near_plane_clipper(self):
        mesh, camera = make_cube(), Camera()
        self.assertEqual(clipped_edge_count(mesh, Scene(position=(0, 0, 3)), camera), 0)
        self.assertGreater(clipped_edge_count(mesh, Scene(position=(0, 0, 1.5)), camera), 0)
        self.assertEqual(clipped_edge_count(mesh, Scene(position=(0, 0, 5)), camera), 0)


class QuestStateTests(unittest.TestCase):
    def test_shape_match_unlocks_next_step_and_wraps_angles(self):
        state = QuestState()
        self.assertFalse(state.advance())
        state.observe_alignment((CHALLENGES[0].target_angles[0] + tau,
                                 CHALLENGES[0].target_angles[1],
                                 CHALLENGES[0].target_angles[2]))
        self.assertTrue(state.confirmed)
        self.assertTrue(state.advance())
        self.assertEqual(state.current, 1)
        self.assertFalse(state.confirmed)
        self.assertEqual(state.answer, None)

    def test_depth_challenge_requires_a_farther_move_and_retries(self):
        state = QuestState(current=1)
        self.assertFalse(state.select_answer(0))
        state.observe_depth(CHALLENGES[1].setup_depth + 0.2)
        self.assertFalse(state.depth_tested)
        state.observe_depth(CHALLENGES[1].setup_depth + 0.5)
        self.assertTrue(state.depth_tested)
        self.assertTrue(state.select_answer(1))
        self.assertFalse(state.check_answer())
        self.assertFalse(state.confirmed)
        self.assertFalse(state.last_answer_correct)
        self.assertEqual(state.attempts, 1)
        self.assertTrue(state.select_answer(0))
        self.assertTrue(state.check_answer())
        self.assertTrue(state.confirmed)

    def test_clipping_challenge_gate_and_full_completion(self):
        state = QuestState(current=2)
        self.assertFalse(state.select_answer(0))
        state.observe_clipping(0)
        self.assertFalse(state.clipping_seen)
        state.observe_clipping(2)
        self.assertTrue(state.clipping_seen)
        self.assertTrue(state.select_answer(0))
        self.assertTrue(state.check_answer())
        self.assertTrue(state.advance())
        self.assertTrue(state.done)
        self.assertFalse(state.advance())

    def test_scene_setup_is_deterministic_and_uses_each_challenge(self):
        for challenge in CHALLENGES:
            scene = make_challenge_scene(challenge)
            self.assertEqual(scene.shape, challenge.setup_shape)
            self.assertEqual(scene.projection, challenge.setup_projection)
            self.assertEqual(scene.position[2], challenge.setup_depth)
        self.assertEqual(make_challenge_scene(CHALLENGES[0]).angles,
                         CHALLENGES[0].start_angles)


class QuestDrawingTests(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.target = pygame.Surface((1360, 900))
        self.camera = Camera()
        self.models = make_library()

    def tearDown(self):
        pygame.quit()

    def test_every_challenge_card_and_progress_strip_draws(self):
        for index, challenge in enumerate(CHALLENGES):
            state = QuestState(current=index)
            scene = make_challenge_scene(challenge)
            mesh = self.models[scene.shape]
            clipped = clipped_edge_count(mesh, scene, self.camera)
            if challenge.kind == 'align':
                state.observe_alignment(challenge.target_angles)
            elif challenge.kind == 'choice':
                state.depth_tested = True
            else:
                state.observe_clipping(max(1, clipped))
            draw_quest_card(self.target, state, scene, mesh, self.camera, clipped)
            draw_quest_progress(self.target, state, pygame.Rect(32, 670, 1296, 124),
                                'Move the model to observe the projection.')

        complete = QuestState(current=3)
        draw_quest_card(self.target, complete, Scene(), self.models['Cube'],
                        self.camera)

    def test_comparison_panes_and_near_plane_guide_draw(self):
        scene = make_challenge_scene(CHALLENGES[1])
        result = draw_comparison_challenge(
            self.target, self.models['Cube'], scene, self.camera,
            pygame.Rect(32, 100, 768, 550), pygame.font.Font(None, 19))
        self.assertEqual(set(result), {'Perspective', 'Orthographic'})
        scene.position = (0, 0, 1.0)
        draw_near_plane_guide(self.target, pygame.Rect(32, 100, 768, 550), scene)
        self.assertEqual(self.target.get_clip(), self.target.get_rect())

    def test_font_cache_recovers_after_pygame_shutdown(self):
        first = _font(18)
        pygame.quit()
        second = _font(18)
        self.assertIsNot(first, second)
        self.assertTrue(pygame.font.get_init())


class QuestInteractionTests(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.models = make_library()
        self.state = QuestState()
        self.scene = make_challenge_scene(CHALLENGES[0])
        self.controls = Controls()
        self.dashboard = Dashboard(Panel())
        self.dashboard.active_destination = 'Challenges'

    def tearDown(self):
        pygame.quit()

    def click(self, action):
        self.dashboard.layout(self.scene, self.models, self.state)
        position = self.dashboard.buttons[action].center
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)
        self.dashboard.events([event], self.scene, self.models, self.state,
                              self.controls)

    def test_all_three_challenges_wire_to_the_dashboard(self):
        self.state.observe_alignment(CHALLENGES[0].target_angles)
        self.click(('quest_next',))
        self.assertEqual(self.state.current, 1)

        self.state.depth_tested = True
        self.click(('quest_choice', 0))
        self.click(('quest_check',))
        self.assertTrue(self.state.confirmed)
        self.click(('quest_next',))
        self.assertEqual(self.state.current, 2)

        self.state.observe_clipping(1)
        self.click(('quest_choice', 0))
        self.click(('quest_check',))
        self.assertTrue(self.state.confirmed)
        self.click(('quest_next',))
        self.assertTrue(self.state.done)
        self.click(('quest_back',))
        self.assertEqual(self.dashboard.active_destination, 'Explore')

    def test_challenge_filters_hold_keys_and_mode_toggles(self):
        start = self.scene
        before_position = start.position
        before_projection = start.projection
        pressed = defaultdict(int, {pygame.K_UP: 1, pygame.K_PAGEDOWN: 1})
        self.controls.update(start, [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)],
                             pressed, 0.05, Panel(), (0, 0),
                             allowed_controls=('rotate',))
        self.assertNotEqual(start.angles, CHALLENGES[0].start_angles)
        self.assertEqual(start.position, before_position)
        self.assertEqual(start.projection, before_projection)

        depth_scene = make_challenge_scene(CHALLENGES[1])
        depth_before = depth_scene.angles
        self.controls.update(depth_scene, [], pressed, 0.05, Panel(), (0, 0),
                             allowed_controls=('depth',))
        self.assertEqual(depth_scene.angles, depth_before)
        self.assertGreater(depth_scene.position[2], CHALLENGES[1].setup_depth)

