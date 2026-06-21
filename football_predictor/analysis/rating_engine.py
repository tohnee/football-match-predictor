"""
analysis/rating_engine.py - 七维度实力评分引擎
===============================================

对应 v3.3 框架中的"七维度评分表"。

七个维度（权重）:
    1. 整体实力 overall      (权重 20%) —— Elo + 身价)
    2. 近期状态 form       (权重 20%)
    3. 主客场 home_away  (权重 10% —— 主场加成)
    4. 战术匹配 tactical  (权重 15% —— 阵型克制)
    5. 阵容完整 squad     (权重 15%)
    6. 心理因素 mental    (权重 10% —— 大赛经验、伤停)
    7. 临场变量 context  (权重 10% —— 伤停、赛程压力)

最终输出 1-10 分制评分，并可附加动力引擎 (Momentum Engine) 产生
的 +/- 修正值。

使用示例:
    >>> from football_predictor.analysis.rating_engine import RatingEngine
    >>> engine = RatingEngine()
    >>> home_score, away_score, details = engine.rate_match(home_team, away_team)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional

from football_predictor.models.team import Team
from football_predictor.analysis.tactical_engine import TacticalEngine
from football_predictor.analysis.momentum_engine import MomentumEngine


# 七维度权重
DIMENSIONS: Dict[str, float] = {
    "overall": 0.20,
    "form": 0.20,
    "home_away": 0.10,
    "tactical": 0.15,
    "squad": 0.15,
    "mental": 0.10,
    "context": 0.10,
}


@dataclass
class RatingEngine:
    """负责为每支球队计算综合实力评分。

    Attributes:
        weights: 可自定义维度权重字典。
        apply_momentum: 是否启用动力/情绪修正。
        apply_tactical: 是否启用战术匹配修正。
    """

    weights: Dict[str, float] = field(default_factory=lambda: dict(DIMENSIONS))
    apply_momentum: bool = True
    apply_tactical: bool = True
    tactical_engine: Optional[TacticalEngine] = None
    momentum_engine: Optional[MomentumEngine] = None

    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if self.tactical_engine is None:
            self.tactical_engine = TacticalEngine()
        if self.momentum_engine is None:
            self.momentum_engine = MomentumEngine()

    # ------------------------------------------------------------------
    # 单维度评分
    # ------------------------------------------------------------------
    def _overall_score(self, team: Team) -> float:
        """整体实力维度: 综合 Elo + 身价。"""
        return team.get_strength_score()

    # ------------------------------------------------------------------
    def _form_score(self, team: Team) -> float:
        """近期状态维度: 直接基于 form 字段与最近 8 场战绩。"""
        _, _, _, index = team.recent_form_summary()
        # 混合 form 与近期胜率
        return 0.5 * team.form + 0.5 * index

    # ------------------------------------------------------------------
    def _home_away_score(self, team: Team, is_home: bool, neutral: bool) -> float:
        """主客场维度: 主队在非中立场地获得加成。"""
        base = 5.0
        if neutral:
            return base
        if is_home:
            # 主场加成：基于 home_advantage_factor，归一到 1.0->5，4 分左右
            bonus = (team.home_advantage_factor - 1.0) * 50.0
            return min(10.0, base + bonus)
        # 客场：减去少量客场劣势
        return max(0.0, base - 1.0)

    # ------------------------------------------------------------------
    def _tactical_score(self, team: Team, opponent: Team) -> float:
        """战术匹配维度（依赖 TacticalEngine 的输出）。"""
        assert self.tactical_engine is not None
        # 返回 0-10 分数
        adv = self.tactical_engine.tactical_advantage(team, opponent)
        # 把 [-2, +2] 映射到 [4, 8]，中间 6
        score = 6.0 + adv * 1.0
        return max(0.0, min(10.0, score))

    # ------------------------------------------------------------------
    def _squad_score(self, team: Team) -> float:
        """阵容完整维度。"""
        base = team.squad_depth
        # 若核心球员中有伤停/停赛，额外扣 1 分
        if team.key_players:
            unavailable = sum(1 for p in team.key_players if not p.is_available())
            base -= unavailable * 1.0
        return max(0.0, min(10.0, base))

    # ------------------------------------------------------------------
    def _mental_score(self, team: Team, opponent: Team,
                    momentum_delta: float) -> float:
        """心理因素维度：结合动力引擎输出。"""
        # 以 5 为基准 + 动量修正值
        score = 5.0 + momentum_delta
        return max(0.0, min(10.0, score))

    # ------------------------------------------------------------------
    def _context_score(self, team: Team, context: Dict[str, float]) -> float:
        """临场变量维度（伤停、赛程压力等上下文字典）。"""
        base = 5.0
        base += context.get("injury_penalty", 0.0)
        base += context.get("fatigue", 0.0)
        base += context.get("must_win_bonus", 0.0)
        base += context.get("derby_factor", 0.0)
        return max(0.0, min(10.0, base))

    # ------------------------------------------------------------------
    # 综合评分接口
    # ------------------------------------------------------------------
    def rate_team(self, team: Team, opponent: Team, *,
                  is_home: bool,
                  neutral: bool = False,
                  context: Optional[Dict[str, float]] = None,
                  momentum_delta: float = 0.0) -> Tuple[float, Dict[str, float]]:
        """为单支球队计算综合评分。

        Args:
            team:         需要评分的球队。
            opponent:     对手球队（用于战术匹配与动量）。
            is_home:      是否为主队。
            neutral:      是否中立场地。
            context:      临场变量字典。
            momentum_delta: 动力引擎提供的修正值。

        Returns:
            (final_score, dimension_dict)
        """
        context = context or {}
        dims: Dict[str, float] = {
            "overall": self._overall_score(team),
            "form": self._form_score(team),
            "home_away": self._home_away_score(team, is_home, neutral),
            "tactical": self._tactical_score(team, opponent) if self.apply_tactical else 5.0,
            "squad": self._squad_score(team),
            "mental": self._mental_score(team, opponent, momentum_delta),
            "context": self._context_score(team, context),
        }
        final = sum(dims[k] * w for k, w in self.weights.items())
        final = max(1.0, min(10.0, final))
        return round(final, 3), {k: round(v, 3) for k, v in dims.items()}

    # ------------------------------------------------------------------
    def rate_match(self, home: Team, away: Team, *,
                    neutral: bool = False,
                    home_context: Optional[Dict[str, float]] = None,
                    away_context: Optional[Dict[str, float]] = None,
                    ) -> Tuple[float, float, Dict[str, Dict[str, float]]]:
        """对一场比赛的两支球队同时评分，并输出详细信息。

        Returns:
            (home_final, away_final, details)
        details 是一个包含 "home" 与 "away" 字段的字典，每个字段
            是 "score" 与 "dimensions" 字典。
        """
        # 动量修正
        if self.apply_momentum and self.momentum_engine is not None:
            home_mom = self.momentum_engine.total_adjustment(home, away)
            away_mom = self.momentum_engine.total_adjustment(away, home)
        else:
            home_mom, away_mom = 0.0, 0.0

        home_score, home_dims = self.rate_team(
            home, away, is_home=True, neutral=neutral,
            context=home_context, momentum_delta=home_mom)
        away_score, away_dims = self.rate_team(
            away, home, is_home=False, neutral=neutral,
            context=away_context, momentum_delta=away_mom)

        details = {
            "home": {"score": home_score, "dimensions": home_dims,
                      "momentum_delta": home_mom},
            "away": {"score": away_score, "dimensions": away_dims,
                      "momentum_delta": away_mom},
        }
        return home_score, away_score, details

    # ------------------------------------------------------------------
    def apply_momentum_adjustment(self, score: float,
                               adjustment: float) -> float:
        """将动量调整值 [-1.5, +1.5] 映射到评分修正量。"""
        return max(1.0, min(10.0, score + adjustment))
