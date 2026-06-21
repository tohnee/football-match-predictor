"""
analysis/prediction_engine.py - 比分预测引擎 v4.0
=====================================================

v4.0 重大更新：
    1. [P0-1] 修复 Elo 双重计算：_base_lambda 不再使用 Elo 因子，
       实力差完全由评分引擎的 rating_adjustment 处理
    2. [P1-1] 引入防守建模：lambda 计算同时考虑进攻方场均进球
       和防守方场均失球
    3. [P2-1] 引入 Dixon-Coles 低比分修正：0-0/1-0/0-1 概率被
       适当提升，更符合足球实际
    4. [P2-2] 小组赛轮次效应：第1轮保守、第2轮正常、第3轮开放
    5. [新增] 环境与心理引擎：海拔、气候、旅行疲劳、教练压力、
       球员士气、赛事阶段压力、外界期望

核心流程:
    1. 基础 lambda = 加权(球队进攻力, 对手防守力) * 阶段系数
    2. 评分引擎修正（rating diff → lambda scaling + 碾压系数）
    3. 战术微调
    4. 环境与心理修正
    5. Dixon-Coles Poisson 分布计算比分概率
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from football_predictor.models.team import Team
from football_predictor.analysis.rating_engine import RatingEngine
from football_predictor.analysis.tactical_engine import TacticalEngine
from football_predictor.analysis.momentum_engine import MomentumEngine
from football_predictor.analysis.environment_engine import EnvironmentEngine
from football_predictor.utils.math_utils import (
    poisson_pmf,
    outcome_probabilities,
    outcome_probabilities_dc,
    most_probable_scoreline,
    over_under_probability,
    clamp,
)


# ---------------------------------------------------------------------------
# 基础参数
# ---------------------------------------------------------------------------
# 中立场地基准（淘汰赛/决赛）
BASE_NEUTRAL_GOALS = 1.35
# 小组赛基础 lambda（更开放）
GROUP_STAGE_NEUTRAL_GOALS = 1.60

# 评分差 → lambda 乘数
RATING_MULTIPLIER_KO = 0.12       # 淘汰赛
RATING_MULTIPLIER_GROUP = 0.16    # 小组赛

# 碾压系数（v4.1: 提高上限，支持梯度碾压）
DOMINATION_THRESHOLD = 1.5
DOMINATION_BOOST = 0.25           # 评分差 1.5-2.5
DOMINATION_BOOST_HEAVY = 0.40     # 评分差 2.5+（超级碾压，如西班牙vs沙特）
DOMINATION_HEAVY_THRESHOLD = 2.5

# Dixon-Coles 修正参数
DC_RHO = 0.03

# 小组赛轮次系数（v4.1: 第2轮实际更开放）
GROUP_ROUND_MULTIPLIER = {
    1: 0.92,   # 第1轮：试探，偏保守
    2: 1.08,   # 第2轮：必须抢分，更开放（实际赛果验证）
    3: 1.12,   # 第3轮：已出线轮换/已淘汰放手一搏，最开放
}


@dataclass
class PredictionEngine:
    """比分预测引擎 v4.0。

    支持阶段化预测策略：
        - group_stage=True: 小组赛模式，lambda 更激进，强队碾压效应放大
        - group_stage=False: 淘汰赛/决赛模式，保持保守稳定

    新增参数：
        - group_round: 小组赛轮次 (1/2/3)，影响 lambda 系数
        - dc_rho: Dixon-Coles 修正参数
        - environment_engine: 环境与心理引擎
    """

    rating_engine: Optional[RatingEngine] = None
    tactical_engine: Optional[TacticalEngine] = None
    momentum_engine: Optional[MomentumEngine] = None
    environment_engine: Optional[EnvironmentEngine] = None
    # 阶段标记
    group_stage: bool = False
    group_round: int = 2  # 小组赛轮次 1/2/3
    # Dixon-Coles 参数
    dc_rho: float = DC_RHO

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
        if self.environment_engine is None:
            self.environment_engine = EnvironmentEngine()

    # ------------------------------------------------------------------
    # [P0-1 + P1-1] 基础 lambda 计算（不再使用 Elo 因子，引入防守建模）
    # ------------------------------------------------------------------
    def _base_lambda(self, home: Team, away: Team, neutral: bool
                    ) -> Tuple[float, float]:
        """计算基础 lambda。

        v4.0 改进：
        1. 不再使用 Elo 因子（避免与评分引擎双重计算）
        2. 引入防守建模：主队 lambda = 进攻力 + 对手防守弱点
        3. 小组赛轮次系数
        """
        # 球队进攻力：近期场均进球
        h_gf, h_ga = home.avg_goals_per_game()
        a_gf, a_ga = away.avg_goals_per_game()

        # 基础进球期望（不再用 Elo 因子）
        if self.group_stage:
            base = GROUP_STAGE_NEUTRAL_GOALS
            # 小组赛轮次系数
            round_mult = GROUP_ROUND_MULTIPLIER.get(self.group_round, 1.0)
            base *= round_mult
        else:
            base = BASE_NEUTRAL_GOALS if neutral else 1.45

        # [P1-1] 防守建模：
        # 主队 lambda = 0.5 * base + 0.3 * 主队进攻力 + 0.2 * 客队防守弱点
        # 客队 lambda = 0.5 * base + 0.3 * 客队进攻力 + 0.2 * 主队防守弱点
        #
        # 防守弱点 = 对手场均失球 / 1.5（归一化，1.5为平均失球）
        # 防守弱点 > 1 表示对手防守差，进球期望增加
        h_attack_factor = h_gf / 1.3   # 主队进攻力（1.3为平均进球）
        a_defense_weak = a_ga / 1.3    # 客队防守弱点
        a_attack_factor = a_gf / 1.3   # 客队进攻力
        h_defense_weak = h_ga / 1.3    # 主队防守弱点

        lam_h = 0.5 * base + 0.3 * base * h_attack_factor + 0.2 * base * a_defense_weak
        lam_a = 0.5 * base + 0.3 * base * a_attack_factor + 0.2 * base * h_defense_weak

        # 确保最小值
        lam_h = max(0.3, lam_h)
        lam_a = max(0.2, lam_a)

        return round(lam_h, 4), round(lam_a, 4)

    # ------------------------------------------------------------------
    # 评分修正（含碾压系数）
    # ------------------------------------------------------------------
    def _apply_rating_adjustment(self, lam_h: float, lam_a: float,
                                home_rating: float, away_rating: float
                                ) -> Tuple[float, float]:
        """根据评分差对 lambda 做缩放修正。

        这是唯一使用实力差的地方（P0-1 修复：不再在 _base_lambda 中用 Elo）。
        """
        diff = home_rating - away_rating
        multiplier = RATING_MULTIPLIER_GROUP if self.group_stage else RATING_MULTIPLIER_KO

        factor_h = 1.0 + diff * multiplier / 5.0
        factor_a = 1.0 - diff * multiplier / 5.0
        factor_h = clamp(factor_h, 0.5, 1.8)
        factor_a = clamp(factor_a, 0.5, 1.8)

        lam_h = lam_h * factor_h
        lam_a = lam_a * factor_a

        # 碾压系数（v4.1: 梯度碾压）
        if diff >= DOMINATION_HEAVY_THRESHOLD:
            # 超级碾压（如西班牙vs沙特）：大幅提升强队lambda
            boost = DOMINATION_BOOST_HEAVY if self.group_stage else DOMINATION_BOOST_HEAVY * 0.6
            lam_h = lam_h * (1.0 + boost)
        elif diff >= DOMINATION_THRESHOLD:
            boost = DOMINATION_BOOST if self.group_stage else DOMINATION_BOOST * 0.6
            lam_h = lam_h * (1.0 + boost)
        if diff <= -DOMINATION_HEAVY_THRESHOLD:
            boost = DOMINATION_BOOST_HEAVY if self.group_stage else DOMINATION_BOOST_HEAVY * 0.6
            lam_a = lam_a * (1.0 + boost)
        elif diff <= -DOMINATION_THRESHOLD:
            boost = DOMINATION_BOOST if self.group_stage else DOMINATION_BOOST * 0.6
            lam_a = lam_a * (1.0 + boost)

        return round(lam_h, 4), round(lam_a, 4)

    # ------------------------------------------------------------------
    # 战术微调
    # ------------------------------------------------------------------
    def _apply_tactical_bias(self, lam_h: float, lam_a: float,
                            home: Team, away: Team) -> Tuple[float, float]:
        """根据战术分析微调 lambda。"""
        assert self.tactical_engine is not None
        adv_h = self.tactical_engine.tactical_advantage(home, away)
        adv_a = self.tactical_engine.tactical_advantage(away, home)
        factor_h = 1.0 + adv_h * 0.08
        factor_a = 1.0 + adv_a * 0.08
        return round(lam_h * factor_h, 4), round(lam_a * factor_a, 4)

    # ------------------------------------------------------------------
    # [新增] 环境与心理修正
    # ------------------------------------------------------------------
    def _apply_environment_adjustment(
        self, lam_h: float, lam_a: float,
        home: Team, away: Team,
        city: str = "", stage: str = "group",
    ) -> Tuple[float, float]:
        """根据环境与心理因素微调 lambda。

        正 delta → 球队状态好 → lambda 提升
        负 delta → 球队受影响 → lambda 降低
        """
        assert self.environment_engine is not None
        env_h = self.environment_engine.total_environment_adjustment(
            home, away, city=city, stage=stage)
        env_a = self.environment_engine.total_environment_adjustment(
            away, home, city=city, stage=stage)

        # delta 映射到 lambda 乘数：[-1, +1] → [0.85, 1.15]
        factor_h = 1.0 + env_h * 0.15
        factor_a = 1.0 + env_a * 0.15

        return round(lam_h * factor_h, 4), round(lam_a * factor_a, 4)

    # ------------------------------------------------------------------
    # 预测接口
    # ------------------------------------------------------------------
    def compute_lambdas(self, home: Team, away: Team, *,
                        neutral: bool = False,
                        city: str = "",
                        stage: str = "group",
                        home_context: Optional[Dict[str, float]] = None,
                        away_context: Optional[Dict[str, float]] = None
                        ) -> Tuple[float, float, Dict[str, float]]:
        """返回 (lambda_home, lambda_away, intermediate_data)。"""
        # 1. 基础 lambda（P0-1 + P1-1）
        lam_h, lam_a = self._base_lambda(home, away, neutral)
        data: Dict[str, float] = {"base_lambda_h": lam_h, "base_lambda_a": lam_a}

        # 2. 评分修正
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
        data["tactical_lambda_h"] = lam_h
        data["tactical_lambda_a"] = lam_a

        # 4. 环境与心理修正
        lam_h, lam_a = self._apply_environment_adjustment(
            lam_h, lam_a, home, away, city=city, stage=stage)
        data["final_lambda_h"] = lam_h
        data["final_lambda_a"] = lam_a
        data["momentum_delta_home"] = details["home"]["momentum_delta"]
        data["momentum_delta_away"] = details["away"]["momentum_delta"]

        # 环境详情
        assert self.environment_engine is not None
        env_h_detail = self.environment_engine.total_environment_adjustment(
            home, away, city=city, stage=stage)
        env_a_detail = self.environment_engine.total_environment_adjustment(
            away, home, city=city, stage=stage)
        data["env_delta_home"] = env_h_detail
        data["env_delta_away"] = env_a_detail

        return lam_h, lam_a, data

    # ------------------------------------------------------------------
    def predict_score(self, home: Team, away: Team, *,
                    neutral: bool = False,
                    city: str = "",
                    stage: str = "group",
                    home_context: Optional[Dict[str, float]] = None,
                    away_context: Optional[Dict[str, float]] = None,
                    ) -> Dict[str, object]:
        """对一场比赛进行比分预测。

        Args:
            home:        主队。
            away:        客队。
            neutral:     是否中立场地。
            city:        比赛城市（用于环境因素）。
            stage:       赛事阶段 ("group"/"round16"/"quarter"/"semi"/"final")。
            home_context: 主队临场变量。
            away_context: 客队临场变量。

        Returns:
            预测结果字典。
        """
        lam_h, lam_a, data = self.compute_lambdas(
            home, away, neutral=neutral, city=city, stage=stage,
            home_context=home_context, away_context=away_context)

        # [P2-1] Dixon-Coles 修正
        rho = self.dc_rho
        hw, draw, aw = outcome_probabilities_dc(lam_h, lam_a, dc_rho=rho)
        top = most_probable_scoreline(lam_h, lam_a, top_n=5, dc_rho=rho)
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
            "env_delta_home": data.get("env_delta_home", 0.0),
            "env_delta_away": data.get("env_delta_away", 0.0),
            "score_probability_range": self._describe_range(lam_h, lam_a, rho),
        }
        return result

    # ------------------------------------------------------------------
    def _describe_range(self, lam_h: float, lam_a: float,
                        dc_rho: float = 0.0,
                        confidence: float = 0.95) -> List[str]:
        """返回概率覆盖至少 `confidence` 的比分区间描述。"""
        scores: List[Tuple[int, int, float]] = []
        for h in range(11):
            for a in range(11):
                p = poisson_pmf(h, lam_h) * poisson_pmf(a, lam_a)
                if dc_rho > 0:
                    from football_predictor.utils.math_utils import _dixon_coles_tau
                    p *= _dixon_coles_tau(h, a, lam_h, lam_a, dc_rho)
                if p > 1e-4:
                    scores.append((h, a, p))
        # 归一化
        total_p = sum(s[2] for s in scores)
        if total_p > 0:
            scores = [(h, a, p / total_p) for h, a, p in scores]
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
                    city: str = "",
                    stage: str = "group",
                    ) -> "Prediction":
        """返回一个结构化对象（用于漂亮地打印）。"""
        data = self.predict_score(home, away, neutral=neutral,
                                  city=city, stage=stage)
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
            "最可能比分 (Dixon-Coles 修正):",
        ]
        top_scores = d.get("top_scores", [])
        for rank, (h, a, p) in enumerate(top_scores, start=1):
            lines.append(f"  {rank}. {h}-{a}  {p*100:5.2f}%")
        lines.append("")
        lines.append(f"动量修正: 主队 {d['momentum_delta_home']:+.2f}  "
                     f"客队 {d['momentum_delta_away']:+.2f}")
        lines.append(f"环境修正: 主队 {d.get('env_delta_home', 0):+.3f}  "
                     f"客队 {d.get('env_delta_away', 0):+.3f}")
        return "\n".join(lines)
