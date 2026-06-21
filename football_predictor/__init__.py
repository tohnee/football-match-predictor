"""
Football Predictor - 深度优化的足球比分预测引擎
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

一个基于多维度评分、战术匹配与动力情绪修正的开源足球预测框架。

核心组件:
    - models:        数据模型（球队、比赛、赛事）
    - analysis:      分析引擎（评分、战术、动力、预测）
    - data:          内置数据（2026世界杯、联赛）
    - utils:         工具函数（格式化、概率计算）

使用示例:
    >>> from football_predictor import Team, Match, PredictionEngine
    >>> home = Team("阿根廷", elo_rating=2050, squad_depth=9, form=8)
    >>> away = Team("法国", elo_rating=2030, squad_depth=9, form=8)
    >>> match = Match(home, away, neutral=True)
    >>> engine = PredictionEngine()
    >>> print(engine.predict_score(home, away, neutral=True))

:copyright: (c) 2026 Football Predictor Team
:license: MIT
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Football Predictor Team"

# 便捷顶层导出，方便使用
from football_predictor.models.team import Team, Player
from football_predictor.models.match import Match, MatchResult
from football_predictor.models.tournament import Tournament, Group, KnockoutRound
from football_predictor.analysis.rating_engine import RatingEngine
from football_predictor.analysis.tactical_engine import TacticalEngine
from football_predictor.analysis.momentum_engine import MomentumEngine
from football_predictor.analysis.prediction_engine import PredictionEngine

__all__ = [
    "__version__",
    "__author__",
    "Team",
    "Player",
    "Match",
    "MatchResult",
    "Tournament",
    "Group",
    "KnockoutRound",
    "RatingEngine",
    "TacticalEngine",
    "MomentumEngine",
    "PredictionEngine",
]
