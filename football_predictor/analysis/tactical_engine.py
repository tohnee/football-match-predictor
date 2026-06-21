"""
analysis/tactical_engine.py - 阵型克制与战术匹配分析引擎
===========================================================

足球比赛中的战术风格会显著影响结果：
    - 控球主导型 vs 防守反击型
    - 高位压迫 vs 防线后缩
    - 进攻型边后卫 vs 边锋内切

本引擎支持：
    - 基于阵型字符串（如 "4-3-3"）计算克制关系。
    - 根据预设的战术风格（"possession"/"counter"/"pressing"/"park_bus"/"direct"/"wing_play"）
      计算风格克制矩阵。
    - 返回战术优势值（约 [-2, +2]），供 Rating Engine 折算成分数。

阵型克制矩阵设计原则（相对主队，+表示克制对手）:
    4-3-3 vs 4-4-2:    +0.6（4-3-3 中场控制优势）
    4-3-3 vs 3-5-2:    -0.2（3-5-2 翼卫能压制边锋）
    3-5-2 vs 4-4-2:    +0.4（中路人数优势）
    4-2-3-1 vs 4-3-3:  -0.1
    4-4-2 vs 4-5-1:    +0.3
    默认（未命中）:     0.0

风格克制矩阵（行 vs 列）:
    possession > counter
    counter > pressing
    pressing > park_bus
    park_bus < possession
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from football_predictor.models.team import Team


# ---------------------------------------------------------------------------
# 阵型克制矩阵（symmetric，但值带正负号表示克制）
# ---------------------------------------------------------------------------
FORMATION_MATRIX: Dict[str, Dict[str, float]] = {
    "4-3-3":     {"4-4-2":  0.6, "3-5-2": -0.2, "4-2-3-1":  0.1, "4-5-1":  0.3, "5-3-2":  0.2, "3-4-3":  0.0},
    "4-4-2":     {"4-3-3": -0.6, "3-5-2": -0.4, "4-2-3-1": -0.2, "4-5-1":  0.3, "5-3-2":  0.1, "3-4-3": -0.1},
    "3-5-2":     {"4-3-3":  0.2, "4-4-2":  0.4, "4-2-3-1":  0.3, "4-5-1":  0.2, "5-3-2":  0.1, "3-4-3":  0.2},
    "4-2-3-1":   {"4-3-3": -0.1, "4-4-2":  0.2, "3-5-2":  -0.3, "4-5-1":  0.1, "5-3-2":  0.0, "3-4-3":  0.0},
    "4-5-1":     {"4-3-3": -0.3, "4-4-2": -0.3, "3-5-2":  -0.2, "4-2-3-1": -0.1, "5-3-2": -0.1, "3-4-3": -0.2},
    "5-3-2":     {"4-3-3": -0.2, "4-4-2": -0.1, "3-5-2":  -0.1, "4-2-3-1":  0.0, "4-5-1":  0.1, "3-4-3": -0.2},
    "3-4-3":     {"4-3-3":  0.0, "4-4-2":  0.1, "3-5-2":  -0.2, "4-2-3-1":  0.0, "4-5-1":  0.2, "5-3-2":  0.2},
}

# ---------------------------------------------------------------------------
# 风格克制矩阵
# ---------------------------------------------------------------------------
STYLE_MATRIX: Dict[str, Dict[str, float]] = {
    "possession": {"counter": -0.5, "pressing":  0.3, "park_bus":  0.4, "direct":  0.3, "wing_play":  0.1},
    "counter":    {"possession":  0.5, "pressing":  0.4, "park_bus": -0.3, "direct": -0.2, "wing_play":  0.2},
    "pressing":   {"possession": -0.3, "counter": -0.4, "park_bus":  0.5, "direct":  0.2, "wing_play":  0.2},
    "park_bus":   {"possession": -0.4, "counter":  0.3, "pressing": -0.5, "direct":  0.4, "wing_play": -0.3},
    "direct":     {"possession": -0.3, "counter":  0.2, "pressing": -0.2, "park_bus": -0.4, "wing_play":  0.1},
    "wing_play":  {"possession": -0.1, "counter": -0.2, "pressing": -0.2, "park_bus":  0.3, "direct": -0.1},
}


@dataclass
class TacticalEngine:
    """战术匹配分析引擎。"""

    # 允许每支球队附加独立的战术风格（可通过 set_team_style 注入）
    team_styles: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def set_team_style(self, team_name: str, style: str) -> None:
        """为球队设置战术风格。"""
        valid = set(STYLE_MATRIX.keys())
        if style not in valid:
            raise ValueError(f"未知战术风格: {style!r}; 有效值: {sorted(valid)}")
        self.team_styles[team_name] = style

    # ------------------------------------------------------------------
    def _get_style(self, team: Team) -> Optional[str]:
        """根据球队本身信息推断战术风格。

        优先级：
            1. team_styles 字典中显式设置的风格（通过 set_team_style 注入）
            2. Team 对象自身的 style 属性（由数据层 build_team 写入）
            3. 启发式推断（基于阵型与 Elo，仅作为兜底）
        """
        # 1) 显式注入的风格优先级最高
        if team.name in self.team_styles:
            return self.team_styles[team.name]
        # 2) 读取 Team 对象上由数据层写入的 style 属性
        team_style = getattr(team, "style", "")
        if team_style:
            return team_style
        # 3) 启发式兜底（仅当 style 未指定时）
        if team.formation in ("4-3-3", "3-4-3") and team.elo_rating >= 1900:
            return "possession"
        if team.formation in ("5-3-2", "4-5-1"):
            return "park_bus"
        if team.formation == "3-5-2":
            return "wing_play"
        return None

    # ------------------------------------------------------------------
    def formation_advantage(self, team: Team, opponent: Team) -> float:
        """返回 team 相对 opponent 的阵型克制值。"""
        row = FORMATION_MATRIX.get(team.formation)
        if row is None:
            return 0.0
        return row.get(opponent.formation, 0.0)

    # ------------------------------------------------------------------
    def style_advantage(self, team: Team, opponent: Team) -> float:
        """返回 team 相对 opponent 的风格克制值。"""
        ts = self._get_style(team)
        os_ = self._get_style(opponent)
        if ts is None or os_ is None:
            return 0.0
        return STYLE_MATRIX.get(ts, {}).get(os_, 0.0)

    # ------------------------------------------------------------------
    def tactical_advantage(self, team: Team, opponent: Team) -> float:
        """综合阵型 + 风格，返回大约 [-2, +2] 的优势值。"""
        adv = self.formation_advantage(team, opponent) + self.style_advantage(team, opponent)
        # 裁剪到 [-2, 2]
        return max(-2.0, min(2.0, adv))

    # ------------------------------------------------------------------
    def analyze(self, team: Team, opponent: Team) -> Dict[str, float]:
        """返回完整分析字典（便于调试与报表打印）。"""
        return {
            "formation": self.formation_advantage(team, opponent),
            "style": self.style_advantage(team, opponent),
            "total": self.tactical_advantage(team, opponent),
        }
