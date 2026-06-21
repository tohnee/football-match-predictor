"""
analysis/prediction_engine.py - 比分预测引擎
===============================================

基于 Poisson 分布的进球模型，结合实力差、主客场与动量修正，
生成概率区间而非单点预测。

核心流程:
    1. 根据双方 Elo 计算基础强度系数 lambda_h, lambda_a
    2. 根据近期场均进球进行校准
    3. 根据 Rating Engine 评分差修正（scaling）
    4. 调用 Poisson 分布计算胜/平/负、最可能比分与大小球概率
    5. 输出概率区间（置信区间）

使用示例:
    >>> from football_predictor.analysis.prediction_engine import PredictionEngine
    >>> engine = PredictionEngine()
    >>> result = engine.predict_score(home_team, away_team)
    >>> print(result["most_probable"])  # (2, 1)
    >>> print(result["home_win"])       # 0.48
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from football_predictor.models.team import Team
from football_predictor.analysis.rating_engine import RatingEngine
from football_predictor.analysis.tactical_engine import TacticalEngine
from football_predictor.analysis.momentum_engine import MomentumEngine
from football_predictor.utils.math_utils import (
    poisson_pmf,
    outcome_probabilities,
    most_probable_scoreline,
    over_under_probability,
    elo_win_probability,
    clamp,
    lerp,
)


# 世界平均主队进球（作为 lambda 基准）
BASE_HOME_GOALS = 1.45
BASE_AWAY_GOALS = 1.18
# 中立场地基准
BASE_NEUTRAL_GOALS = 1.30

# 小组赛阶段激进参数
GROUP_STAGE_NEUTRAL_GOALS = 1.65       # 小组赛基础 lambda 更高
GROUP_STAGE_RATING_MULTIPLIER = 0.14   # 评分差影响更大
GROUP_STAGE_DOMINATION_THRESHOLD = 1.5  # 评分差超过此值触发碾压系数
GROUP_STAGE_DOMINATION_BOOST = 0.25    # 碾压系数：强队 lambda 额外加成


@dataclass
class PredictionEngine:
    """比分预测引擎。

    支持阶段化预测策略：
        - group_stage=True: 小组赛模式，lambda 更激进，强队碾压效应放大
        - group_stage=False: 淘汰赛/决赛模式，保持保守稳定
    """

    rating_engine: Optional[RatingEngine] = None
    tactical_engine: Optional[TacticalEngine] = None
    momentum_engine: Optional[MomentumEngine] = None
    base_home_goals: float = BASE_HOME_GOALS
    base_away_goals: float = BASE_AWAY_GOALS
    base_neutral_goals: float = BASE_NEUTRAL_GOALS
    # 评分差每增加 1 分，进球 lambda 乘数增加
    rating_multiplier: float = 0.10
    # 阶段标记：小组赛 = True，淘汰赛/决赛 = False
    group_stage: bool = False

    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        if self.rating_engine is None:
            self.rating_engine = RatingEngine(
                tactical_engine=self.tactical_engine,
                momentum_engine=self.momentum_engine,
            )
        if self.tactical_engine is None:
            self.tactical_engine = self.rating_engine.tactical_engine
        if self.momentum_engine is None:
            self.momentum_engine = self.rating_engine.momentum_engine

    # ------------------------------------------------------------------
    # 基础 lambda 计算
    # ------------------------------------------------------------------
    def _base_lambda(self, home: Team, away: Team, neutral: bool
                    ) -> Tuple[float, float]:
        """根据 Elo 与历史场均进球，计算基础 lambda。

        小组赛阶段使用更高的基础 lambda，让比赛更开放。
        """
        # Elo 胜率差异
        elo_diff = home.elo_rating - away.elo_rating
        win_p_home = elo_win_probability(elo_diff)  # 主队胜率（理论）
        win_p_away = 1.0 - win_p_home

        # 取近期场均进球作为校准
        h_gf, _ = home.avg_goals_per_game()
        a_ga_unused = 0.0
        _, a_gf = away.avg_goals_per_game()  # type: ignore[assignment]
        # 客队防守实力：主队进球参考 away 的失球平均
        # 这里我们用一种启发式：主队 lambda = Elo 因子 * base_goals
        elo_factor_h = 0.6 + 0.8 * win_p_home  # 0.6 ~ 1.4
        elo_factor_a = 0.6 + 0.8 * win_p_away

        # 小组赛阶段使用更高的基础 lambda
        base_h = GROUP_STAGE_NEUTRAL_GOALS if (self.group_stage and neutral) else self.base_home_goals
        base_a = GROUP_STAGE_NEUTRAL_GOALS if (self.group_stage and neutral) else self.base_away_goals
        if not self.group_stage and neutral:
            base_h = self.base_neutral_goals
            base_a = self.base_neutral_goals

        if neutral:
            lam_h = base_h * elo_factor_h
            lam_a = base_a * elo_factor_a
        else:
            lam_h = base_h * elo_factor_h
            lam_a = base_a * elo_factor_a

        # 再与近期场均进球做加权平均（如果有数据的话）
        if home.recent_goals_for:
            lam_h = 0.6 * lam_h + 0.4 * h_gf
        if away.recent_goals_for:
            lam_a = 0.6 * lam_a + 0.4 * a_gf  # type: ignore[arg-type]

        return round(lam_h, 4), round(lam_a, 4)

    # ------------------------------------------------------------------
    def _apply_rating_adjustment(self, lam_h: float, lam_a: float,
                                home_rating: float, away_rating: float
                                ) -> Tuple[float, float]:
        """根据 1-10 评分差对 lambda 做缩放修正。

        小组赛阶段：评分差影响更大，且强队获得额外碾压加成。
        """
        diff = home_rating - away_rating  # 范围约 [-9, +9]
        # 小组赛使用更大的 rating_multiplier
        multiplier = GROUP_STAGE_RATING_MULTIPLIER if self.group_stage else self.rating_multiplier

        # 映射到 [0.7, 1.5] 左右的乘法因子
        factor_h = 1.0 + diff * multiplier / 5.0
        factor_a = 1.0 - diff * multiplier / 5.0
        factor_h = clamp(factor_h, 0.5, 1.8)
        factor_a = clamp(factor_a, 0.5, 1.8)

        lam_h = lam_h * factor_h
        lam_a = lam_a * factor_a

        # 小组赛碾压系数：评分差足够大时，强队 lambda 进一步放大
        if self.group_stage and diff >= GROUP_STAGE_DOMINATION_THRESHOLD:
            lam_h = lam_h * (1.0 + GROUP_STAGE_DOMINATION_BOOST)
        if self.group_stage and diff <= -GROUP_STAGE_DOMINATION_THRESHOLD:
            lam_a = lam_a * (1.0 + GROUP_STAGE_DOMINATION_BOOST)

        return round(lam_h, 4), round(lam_a, 4)

    # ------------------------------------------------------------------
    def _apply_tactical_bias(self, lam_h: float, lam_a: float,
                            home: Team, away: Team) -> Tuple[float, float]:
        """根据战术分析微调 lambda（例如反击球队对控球球队时会提高客队进球）。"""
        assert self.tactical_engine is not None
        adv_h = self.tactical_engine.tactical_advantage(home, away)
        adv_a = self.tactical_engine.tactical_advantage(away, home)
        factor_h = 1.0 + adv_h * 0.06
        factor_a = 1.0 + adv_a * 0.06
        return round(lam_h * factor_h, 4), round(lam_a * factor_a, 4)

    # ------------------------------------------------------------------
    # 预测接口
    # ------------------------------------------------------------------
    def compute_lambdas(self, home: Team, away: Team, *,
                        neutral: bool = False,
                        home_context: Optional[Dict[str, float]] = None,
                        away_context: Optional[Dict[str, float]] = None
                        ) -> Tuple[float, float, Dict[str, float]]:
        """返回 (lambda_home, lambda_away, intermediate_data)。"""
        # 1. 基础 lambda
        lam_h, lam_a = self._base_lambda(home, away, neutral)
        data: Dict[str, float] = {"base_lambda_h": lam_h, "base_lambda_a": lam_a}

        # 2. 评分
        assert self.rating_engine is not None
        home_score, away_score, details = self.rating_engine.rate_match(
            home, away, neutral=neutral,
            home_context=home_context, away_context=away_context)
        data["home_rating"] = home_score
        data["away_rating"] = away_score
        data["rating_diff"] = round(home_score - away_score, 3)

        lam_h, lam_a = self._apply_rating_adjustment(lam_h, lam_a, home_score, away_score)
        data["rating_adjusted_lambda_h"] = lam_h
        data["rating_adjusted_lambda_a"] = lam_a

        # 3. 战术微调
        lam_h, lam_a = self._apply_tactical_bias(lam_h, lam_a, home, away)
        data["final_lambda_h"] = lam_h
        data["final_lambda_a"] = lam_a
        data["momentum_delta_home"] = details["home"]["momentum_delta"]
        data["momentum_delta_away"] = details["away"]["momentum_delta"]

        return lam_h, lam_a, data

    # ------------------------------------------------------------------
    def predict_score(self, home: Team, away: Team, *,
                    neutral: bool = False,
                    home_context: Optional[Dict[str, float]] = None,
                    away_context: Optional[Dict[str, float]] = None,
                    ) -> Dict[str, object]:
        """对一场比赛进行比分预测。

        Args:
            home:        主队。
            away:        客队。
            neutral:     是否中立场地。
            home_context: 主队临场变量（伤停、疲劳、保级压力等）。
            away_context: 客队临场变量。

        Returns:
            一个字典，包含:
                - "lambda_home", "lambda_away": 最终 Poisson 参数
                - "most_probable":             最可能比分 (h, a, p)
                - "second_probable":           次可能比分 (h, a, p)
                - "top_scores":                Top-N 比分列表
                - "home_win", "draw", "away_win": 胜负平概率
                - "over_25", "under_25":       大小球概率
                - "home_rating", "away_rating": 两队综合评分
                - "rating_diff":               评分差
                - "momentum_delta_home/away":  动量修正值
                - "score_probability_range":   95% 最可能比分区间描述
        """
        lam_h, lam_a, data = self.compute_lambdas(
            home, away, neutral=neutral,
            home_context=home_context, away_context=away_context)

        # 计算胜负平
        hw, draw, aw = outcome_probabilities(lam_h, lam_a)
        # 最可能的比分
        top = most_probable_scoreline(lam_h, lam_a, top_n=5)
        over25, under25 = over_under_probability(lam_h, lam_a, 2.5)

        result: Dict[str, object] = {
            "lambda_home": lam_h,
            "lambda_away": lam_a,
            "most_probable": top[0] if top else (1, 1, 0.0),
            "second_probable": top[1] if len(top) > 1 else None,
            "top_scores": top,
            "home_win": round(hw, 4),
            "draw": round(draw, 4),
            "away_win": round(aw, 4),
            "over_25": round(over25, 4),
            "under_25": round(under25, 4),
            "home_rating": data["home_rating"],
            "away_rating": data["away_rating"],
            "rating_diff": data["rating_diff"],
            "momentum_delta_home": data.get("momentum_delta_home", 0.0),
            "momentum_delta_away": data.get("momentum_delta_away", 0.0),
            "score_probability_range": self._describe_range(lam_h, lam_a),
        }
        return result

    # ------------------------------------------------------------------
    def _describe_range(self, lam_h: float, lam_a: float,
                        confidence: float = 0.95) -> List[str]:
        """返回概率覆盖至少 `confidence` 的比分区间描述。"""
        # 收集所有比分概率，降序累加直到覆盖 confidence
        scores: List[Tuple[int, int, float]] = []
        for h in range(11):
            for a in range(11):
                p = poisson_pmf(h, lam_h) * poisson_pmf(a, lam_a)
                if p > 1e-4:
                    scores.append((h, a, p))
        scores.sort(key=lambda t: t[2], reverse=True)
        total = 0.0
        ranges: List[str] = []
        for h, a, p in scores:
            total += p
            ranges.append(f"{h}-{a}: {p*100:.2f}%")
            if total >= confidence:
                break
        ranges.append(f"[累计覆盖 {total*100:.1f}%]")
        return ranges

    # ------------------------------------------------------------------
    # 便捷 API
    # ------------------------------------------------------------------
    def predict_match(self, home: Team, away: Team, *,
                    neutral: bool = False,
                    ) -> "Prediction":
        """返回一个结构化对象（用于漂亮地打印）。"""
        data = self.predict_score(home, away, neutral=neutral)
        return Prediction(home=home, away=away, neutral=neutral, data=data)


@dataclass
class Prediction:
    """对 PredictionEngine 结果的封装，提供漂亮 __str__。"""

    home: Team
    away: Team
    neutral: bool = False
    data: Dict[str, object] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def __str__(self) -> str:
        d = self.data
        lines = [
            f"=== {self.home.name} vs {self.away.name}"
            f"{' (中立)' if self.neutral else ''} ===",
            f"综合评分: {d['home_rating']} vs {d['away_rating']}  "
            f"(差: {d['rating_diff']:+.2f})",
            f"Poisson λ:  主队 {d['lambda_home']:.3f}  |  客队 {d['lambda_away']:.3f}",
            "",
            "结果概率:",
            f"  主胜  {d['home_win']*100:5.1f}%   平局  {d['draw']*100:5.1f}%"
            f"   客胜  {d['away_win']*100:5.1f}%",
            f"  大球(>2.5) {d['over_25']*100:5.1f}%   小球 {d['under_25']*100:5.1f}%",
            "",
            "最可能比分:",
        ]
        top_scores = d.get("top_scores", [])
        for rank, (h, a, p) in enumerate(top_scores, start=1):
            lines.append(f"  {rank}. {h}-{a}  {p*100:5.2f}%")
        lines.append("")
        lines.append(f"动量修正: 主队 {d['momentum_delta_home']:+.2f}  "
                     f"客队 {d['momentum_delta_away']:+.2f}")
        return "\n".join(lines)
