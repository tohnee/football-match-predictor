"""
models/team.py - 球队与球员数据模型
=====================================

封装一支足球队的核心属性与行为，包含：
    - 基础身份：名称、国家、所属联赛
    - 实力指标：Elo 评分、阵容深度、身价
    - 状态指标：近期状态、最近 N 场比赛结果
    - 人员指标：核心球员、常用阵型
    - 行为：综合评分计算、根据比赛结果更新状态

使用示例:
    >>> from football_predictor.models.team import Team, Player
    >>> team = Team("阿根廷", elo_rating=2050, squad_depth=9, form=8, market_value=1200)
    >>> team.add_player(Player("梅西", position="RW", rating=93, age=39))
    >>> team.update_form("W")   # 胜利
    >>> print(team.get_strength_score())
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# 球员数据类
# ---------------------------------------------------------------------------
@dataclass
class Player:
    """代表一名球员的基础信息。

    Attributes:
        name:     球员姓名。
        position: 位置（如 GK / DF / MF / FW / RW / LW 等）。
        rating:   个人能力评分（通常 50-100 的 FIFA / ELO 风格分值）。
        age:      年龄（可选）。
        status:   状态，如 "normal"（正常）、"injury"（伤停）、"suspend"（停赛）。
    """

    name: str
    position: str = "MF"
    rating: float = 75.0
    age: Optional[int] = None
    status: str = "normal"

    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        """判断该球员是否可以出场（未伤停 / 停赛）。"""
        return self.status in ("normal", "fit", "available")


# ---------------------------------------------------------------------------
# 球队数据类
# ---------------------------------------------------------------------------
@dataclass
class Team:
    """足球队数据模型。

    与 v3.3 框架中的"球队评分"部分直接对应：
        - elo_rating:  整体实力基准
        - squad_depth: 阵容深度
        - form:        近期状态
        - recent_form: 最近比赛结果列表（用于动量计算）

    Attributes:
        name:                  球队名称。
        country:               国家/地区（用于识别国家队 vs 俱乐部）。
        elo_rating:            Elo 评分（通常 1200-2200）。
        squad_depth:           阵容深度 (1-10)，反映替补实力。
        form:                  近期状态 (1-10)，10 为最佳。
        market_value:          全队身价（百万欧元）。
        formation:             常用阵型（如 "4-3-3"、"3-5-2"）。
        key_players:           核心球员列表。
        recent_form:           最近比赛结果列表，元素为 "W" / "D" / "L"。
        home_advantage_factor: 主场优势加成系数（默认 1.04，中性场地时忽略）。
        recent_goals_for:      最近几场比赛的进球数列表（用于进球模型）。
        recent_goals_against:  最近几场比赛的失球数列表（用于进球模型）。
        style:                 球队战术风格，可选值："possession"（控球主导）、
                               "counter"（防守反击）、"pressing"（高位压迫）、
                               "park_bus"（铁桶阵）、"direct"（直接进攻）、
                               "wing_play"（边路进攻）；空字符串表示未指定。
    """

    name: str
    country: str = ""
    elo_rating: float = 1500.0
    squad_depth: float = 5.0
    form: float = 5.0
    market_value: float = 0.0
    formation: str = "4-3-3"
    key_players: List[Player] = field(default_factory=list)
    recent_form: List[str] = field(default_factory=list)
    home_advantage_factor: float = 1.04
    recent_goals_for: List[int] = field(default_factory=list)
    recent_goals_against: List[int] = field(default_factory=list)
    style: str = ""

    # 内部常量 —— 用于评分归一化
    _MAX_ELO: float = 2200.0
    _MIN_ELO: float = 1200.0

    # ------------------------------------------------------------------
    # 核心行为
    # ------------------------------------------------------------------
    def add_player(self, player: Player) -> "Team":
        """添加核心球员，返回 self 以支持链式调用。"""
        if not isinstance(player, Player):
            raise TypeError("player 必须是 Player 实例")
        self.key_players.append(player)
        return self

    # ------------------------------------------------------------------
    def update_form(self, result: str,
                    goals_for: Optional[int] = None,
                    goals_against: Optional[int] = None) -> None:
        """根据比赛结果更新近期状态与比赛历史。

        Args:
            result:        "W"（胜）/ "D"（平）/ "L"（负）。
            goals_for:     该场进球数（可选）。
            goals_against: 该场失球数（可选）。

        规则:
            - 胜利 +1.2，平局 +0.2，失败 -0.8
            - 大比分胜利（净胜 >= 3）额外 +0.3
            - 大比分失利（净负 >= 3）额外 -0.4
            - 结果被裁剪到 [1, 10] 区间
        """
        result = result.upper()
        if result not in ("W", "D", "L"):
            raise ValueError(f"result 必须是 W/D/L，收到 {result!r}")

        delta = {"W": 1.2, "D": 0.2, "L": -0.8}[result]
        if goals_for is not None and goals_against is not None:
            diff = goals_for - goals_against
            if diff >= 3:
                delta += 0.3
            elif diff <= -3:
                delta -= 0.4

        self.form = max(1.0, min(10.0, self.form + delta))

        # 只保留最近 8 场
        self.recent_form.append(result)
        if len(self.recent_form) > 8:
            self.recent_form.pop(0)

        if goals_for is not None:
            self.recent_goals_for.append(int(goals_for))
            if len(self.recent_goals_for) > 8:
                self.recent_goals_for.pop(0)
        if goals_against is not None:
            self.recent_goals_against.append(int(goals_against))
            if len(self.recent_goals_against) > 8:
                self.recent_goals_against.pop(0)

    # ------------------------------------------------------------------
    def get_strength_score(self, weights: Optional[dict] = None) -> float:
        """返回一个 0-10 的综合实力评分。

        对应 v3.3 框架的"球队基础实力"维度。默认权重:
            - Elo 评分      45%
            - 阵容深度      25%
            - 全队身价      15%
            - 核心球员水平  15%

        Args:
            weights: 可选的自定义权重字典（键见内部 default_weights）。

        Returns:
            0-10 的浮点评分。
        """
        default_weights = {
            "elo": 0.45,
            "squad": 0.25,
            "market": 0.15,
            "key_players": 0.15,
        }
        if weights is None:
            weights = default_weights
        else:
            # 合并默认值
            for k, v in default_weights.items():
                weights.setdefault(k, v)

        # 归一化 Elo -> 0-10
        elo_norm = 10.0 * (self.elo_rating - self._MIN_ELO) / (self._MAX_ELO - self._MIN_ELO)
        elo_norm = max(0.0, min(10.0, elo_norm))

        # 归一化身价（参考最大值 2000 百万欧元）
        market_norm = 10.0 * (self.market_value / 2000.0) if self.market_value > 0 else 0.0
        market_norm = min(10.0, market_norm)

        # 核心球员平均评分 -> 0-10
        if self.key_players:
            avg_rating = sum(p.rating for p in self.key_players if p.is_available()) / len(self.key_players)
            kp_norm = (avg_rating - 50.0) / 5.0  # 50 -> 0, 100 -> 10
        else:
            kp_norm = self.squad_depth
        kp_norm = max(0.0, min(10.0, kp_norm))

        score = (
            weights["elo"] * elo_norm
            + weights["squad"] * self.squad_depth
            + weights["market"] * market_norm
            + weights["key_players"] * kp_norm
        )
        return round(max(0.0, min(10.0, score)), 2)

    # ------------------------------------------------------------------
    def recent_form_summary(self) -> Tuple[int, int, int, float]:
        """返回近期比赛 (胜, 平, 负, 近期状态指数) 摘要。"""
        wins = self.recent_form.count("W")
        draws = self.recent_form.count("D")
        losses = self.recent_form.count("L")
        n = max(1, len(self.recent_form))
        index = (wins * 3 + draws) / (3.0 * n) * 10.0  # 0-10
        return wins, draws, losses, round(index, 2)

    # ------------------------------------------------------------------
    def avg_goals_per_game(self) -> Tuple[float, float]:
        """返回 (场均进球, 场均失球)，没有数据时返回 (1.2, 1.2) 默认值。"""
        gf = sum(self.recent_goals_for) / len(self.recent_goals_for) if self.recent_goals_for else 1.2
        ga = sum(self.recent_goals_against) / len(self.recent_goals_against) if self.recent_goals_against else 1.2
        return round(gf, 3), round(ga, 3)

    # ------------------------------------------------------------------
    # 辅助函数
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"Team(name={self.name!r}, country={self.country!r}, "
            f"elo={self.elo_rating:.0f}, form={self.form:.1f})"
        )

    def __str__(self) -> str:
        return f"{self.name} (Elo {self.elo_rating:.0f})"
