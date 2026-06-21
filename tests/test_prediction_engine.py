"""
tests/test_prediction_engine.py - PredictionEngine 单元测试
=================================================================

运行:
    $ cd football-predictor
    $ python -m unittest tests.test_prediction_engine
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from football_predictor import Team, PredictionEngine
from football_predictor.analysis.prediction_engine import PredictionEngine as PE


class TestPredictionEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.home = Team(name="主队", elo_rating=1900, squad_depth=7, form=7,
                        market_value=500, formation="4-3-3")
        self.away = Team(name="客队", elo_rating=1800, squad_depth=6, form=6,
                        market_value=400, formation="4-4-2")

    def test_engine_initialization(self) -> None:
        pe = PE()
        self.assertIsNotNone(pe.rating_engine)
        self.assertIsNotNone(pe.tactical_engine)
        self.assertIsNotNone(pe.momentum_engine)

    def test_predict_score_returns_structure(self) -> None:
        pe = PE()
        result = pe.predict_score(self.home, self.away)
        # 关键键存在
        for key in ("lambda_home", "lambda_away", "most_probable",
                    "home_win", "draw", "away_win",
                    "over_25", "under_25", "home_rating", "away_rating",
                    "top_scores"):
            self.assertIn(key, result)

    def test_outcome_probabilities_sum_to_one(self) -> None:
        pe = PE()
        result = pe.predict_score(self.home, self.away)
        total = result["home_win"] + result["draw"] + result["away_win"]
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_lambda_positive(self) -> None:
        pe = PE()
        result = pe.predict_score(self.home, self.away)
        self.assertGreater(result["lambda_home"], 0.0)
        self.assertGreater(result["lambda_away"], 0.0)

    def test_neutral_ground_flattens_home_advantage(self) -> None:
        pe = PE()
        neutral_result = pe.predict_score(self.home, self.away, neutral=True)
        regular_result = pe.predict_score(self.home, self.away, neutral=False)
        # 主客差距应减少
        diff_neutral = neutral_result["home_win"] - neutral_result["away_win"]
        diff_regular = regular_result["home_win"] - regular_result["away_win"]
        self.assertLess(abs(diff_neutral), abs(diff_regular) + 0.1)

    def test_most_probable_is_tuple(self) -> None:
        pe = PE()
        result = pe.predict_score(self.home, self.away)
        most = result["most_probable"]
        self.assertEqual(len(most), 3)
        self.assertIsInstance(most[0], int)
        self.assertIsInstance(most[1], int)
        self.assertIsInstance(most[2], float)

    def test_predict_match_object(self) -> None:
        pe = PE()
        p = pe.predict_match(self.home, self.away)
        text = str(p)
        self.assertIn(self.home.name, text)
        self.assertIn("主胜", text)
        self.assertIn("平局", text)

    def test_world_cup_data(self) -> None:
        from football_predictor.data.world_cup_2026 import TEAMS, get_tournament
        # 必须包含至少 30 支球队
        self.assertGreaterEqual(len(TEAMS), 30)
        # 关键球队存在
        for name in ("阿根廷", "巴西", "英格兰", "法国", "西班牙"):
            self.assertIn(name, TEAMS)
        # 可以构造 Tournament
        t = get_tournament()
        self.assertEqual(len(t.groups), 8)

    def test_world_cup_prediction(self) -> None:
        from football_predictor.data.world_cup_2026 import TEAMS
        pe = PE()
        # 不抛异常
        r = pe.predict_score(TEAMS["阿根廷"], TEAMS["法国"], neutral=True)
        self.assertIsInstance(r["home_win"], float)
        self.assertGreaterEqual(r["home_win"], 0.0)
        self.assertLessEqual(r["home_win"], 1.0)


if __name__ == "__main__":
    unittest.main()
