"""
tests/test_rating_engine.py - RatingEngine 单元测试
======================================================
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from football_predictor import Team, RatingEngine, MomentumEngine


class TestRatingEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.strong = Team(name="强队", elo_rating=2050, squad_depth=9,
                           form=8, market_value=1000, formation="4-3-3")
        self.weak = Team(name="弱队", elo_rating=1600, squad_depth=4,
                         form=5, market_value=100, formation="4-4-2")

    def test_basic_rating_in_range(self) -> None:
        engine = RatingEngine()
        strong_score, weak_score, _ = engine.rate_match(self.strong, self.weak, neutral=True)
        self.assertGreaterEqual(strong_score, 1.0)
        self.assertLessEqual(strong_score, 10.0)
        self.assertGreater(strong_score, weak_score)

    def test_details_contains_all_dimensions(self) -> None:
        engine = RatingEngine()
        _, _, details = engine.rate_match(self.strong, self.weak, neutral=True)
        for side in ("home", "away"):
            for key in ("score", "dimensions", "momentum_delta"):
                self.assertIn(key, details[side])
            dims = details[side]["dimensions"]
            for dim in ("overall", "form", "home_away", "tactical",
                        "squad", "mental", "context"):
                self.assertIn(dim, dims)

    def test_team_strength_score(self) -> None:
        s = self.strong.get_strength_score()
        self.assertGreaterEqual(s, 0.0)
        self.assertLessEqual(s, 10.0)
        # 强队综合评分 > 弱队
        self.assertGreater(s, self.weak.get_strength_score())

    def test_team_update_form(self) -> None:
        team = Team(name="x", elo_rating=1600)
        initial_form = team.form
        # 连续胜利
        team.update_form("W", 2, 1)
        team.update_form("W", 3, 0)
        self.assertGreater(team.form, initial_form)
        # 连续失败
        team.update_form("L", 0, 3)
        team.update_form("L", 0, 5)
        self.assertLess(team.form, initial_form + 2)
        self.assertEqual(team.recent_form, ["W", "W", "L", "L"])


class TestMomentumEngine(unittest.TestCase):

    def test_rebound_effect_on_streak(self) -> None:
        losing_team = Team(name="连败队", elo_rating=1600)
        opponent = Team(name="对手", elo_rating=1800)
        for _ in range(4):
            losing_team.update_form("L", 0, 2)
        eng = MomentumEngine()
        self.assertGreater(eng.check_rebound_effect(losing_team, opponent), 0)

    def test_blowout_illusion_after_huge_win(self) -> None:
        team = Team(name="大胜队", elo_rating=1800)
        team.update_form("W", 5, 0)
        eng = MomentumEngine()
        self.assertLess(eng.check_blowout_illusion(team), 0)

    def test_emotional_stack(self) -> None:
        team = Team(name="t", elo_rating=1700)
        team.update_form("W", 2, 1)
        team.update_form("W", 2, 1)
        team.update_form("W", 2, 1)
        eng = MomentumEngine()
        self.assertGreater(eng.check_emotional_stack(team), 0)


if __name__ == "__main__":
    unittest.main()
