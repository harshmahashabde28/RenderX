"""Gameplay rules, entity movement, and score persistence."""

from collections import defaultdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

from renderx.shooter.entities.box import Box
from renderx.shooter.entities.enemy import Enemy
from renderx.shooter.entities.player import Player
from renderx.shooter.logic import (DIFFICULTIES, aabb_overlap,
                                   clamp_frame_time, enemy_count_for_wave)
from renderx.shooter.storage import load_best, save_if_best


class ShooterRulesTests(unittest.TestCase):
    def test_wave_size_grows_and_difficulty_profiles_change_pressure(self):
        self.assertEqual([enemy_count_for_wave(n) for n in range(1, 5)],
                         [3, 5, 7, 9])
        self.assertLess(DIFFICULTIES["EASY"].enemy_speed,
                        DIFFICULTIES["NORMAL"].enemy_speed)
        self.assertLess(DIFFICULTIES["NORMAL"].enemy_speed,
                        DIFFICULTIES["HARD"].enemy_speed)
        self.assertGreater(DIFFICULTIES["EASY"].enemy_fire_interval,
                           DIFFICULTIES["HARD"].enemy_fire_interval)

    def test_ground_collision_edges_and_frame_time_clamp(self):
        self.assertTrue(aabb_overlap(0, 0, 2, 2, 1, 1, 2, 2))
        self.assertFalse(aabb_overlap(0, 0, 2, 2, 2, 0, 2, 2))
        self.assertEqual(clamp_frame_time(-1), 0)
        self.assertEqual(clamp_frame_time(1), .05)
        self.assertAlmostEqual(clamp_frame_time(.02), .02)


class ShooterEntityTests(unittest.TestCase):
    def test_player_moves_slides_against_cover_and_dashes_on_cooldown(self):
        player = Player()
        keys = defaultdict(int)
        keys[pygame.K_d] = 1
        obstacle = Box(1.8, 0)
        obstacle.width = obstacle.depth = 2.7
        player.move(keys, .1, [obstacle], 68)
        self.assertEqual(player.x, 0)
        self.assertTrue(player.dash(keys))
        player.move(keys, .1, [], 68)
        self.assertGreater(player.x, 2.0)
        self.assertFalse(player.dash(keys))
        self.assertLessEqual(player.x, 68)

    def test_enemy_approaches_and_reports_lethal_hits(self):
        enemy = Enemy(20, 0, health=2, speed=3.0)
        enemy.update(.5, 0, 0, [], 68)
        self.assertLess(enemy.x, 20)
        self.assertFalse(enemy.hit())
        self.assertTrue(enemy.hit())


class ScorePersistenceTests(unittest.TestCase):
    def test_best_score_is_saved_atomically_and_bad_data_is_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "field-operations.json"
            with patch("renderx.shooter.storage.score_path", return_value=path):
                self.assertEqual(load_best()["score"], 0)
                best = save_if_best(900, 4, "HARD")
                self.assertEqual(best, {"score": 900, "wave": 4,
                                        "difficulty": "HARD"})
                self.assertEqual(save_if_best(200, 2, "EASY"), best)
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), best)
                path.write_text("{invalid", encoding="utf-8")
                self.assertEqual(load_best()["score"], 0)


if __name__ == "__main__":
    unittest.main()
