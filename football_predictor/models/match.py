"""
models/match.py - 比赛与比赛结果模型
=======================================

封装一场足球比赛的元数据与 (可选) 赛果，供分析引擎与预测引擎使用。

使用示例:
    >>> from football_predictor.models.team import Team
    >>> from football_predictor.models.match import Match
    >>> arg = Team("阿根廷", elo_rating=2050, form=8, squad_depth=9)
    >>> fra = Team("法国",   elo_rating=2030, form=8, squad_depth=9)
    >>> m = Match(arg, fra, date="2026-06-25", neutral=True, competition="World Cup 2026")
    >>> print(m)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Tuple, List, Dict, Any

from football_predictor.models.team import Team


# ---------------------------------------------------------------------------
# 比赛结果
# ---------------------------------------------------------------------------
@dataclass
class MatchResult:
    """表示一场比赛的最终结果。"""

    home_goals: int
    away_goals: int
    home_scorers: List[str] = field(default_factory=list)
    away_scorers: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    @property
    def winner(self) -> str:
        """返回 "home" / "away" / "draw"。"""
        if self.home_goals > self.away_goals:
            return "home"
        if self.home_goals < self.away_goals:
            return "away"
        return "draw"

    # ------------------------------------------------------------------
    def as_tuple(self) -> Tuple[int, int]:
        return self.home_goals, self.away_goals

    def __str__(self) -> str:
        return f"{self.home_goals}-{self.away_goals}"


# ---------------------------------------------------------------------------
# 比赛
# ---------------------------------------------------------------------------
@dataclass
class Match:
    """一场足球比赛。

    Attributes:
        home:         主队。
        away:         客队。
        date:         比赛日期（字符串或 date 类型均可）。
        neutral:      是否在中立场地进行（True 时取消主场优势）。
        competition:  赛事名称。
        stage:        阶段（如 "小组赛"、"1/8决赛"）。
        venue:        球场名称。
        result:       已产生的比赛结果（可选）。
        context:      自定义比赛上下文（如"保级战"、"出线生死战"）。
    """

    home: Team
    away: Team
    date: str = ""
    neutral: bool = False
    competition: str = ""
    stage: str = ""
    venue: str = ""
    result: Optional[MatchResult] = None
    context: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    @property
    def has_result(self) -> bool:
        return self.result is not None

    # ------------------------------------------------------------------
    def set_result(self, home_goals: int, away_goals: int) -> "Match":
        """设置比赛结果。

        同时更新双方近期状态与进球历史。
        """
        if home_goals < 0 or away_goals < 0:
            raise ValueError("进球数不能为负数")
        self.result = MatchResult(home_goals, away_goals)

        # 根据结果更新状态
        if home_goals > away_goals:
            self.home.update_form("W", home_goals, away_goals)
            self.away.update_form("L", away_goals, home_goals)
        elif home_goals < away_goals:
            self.home.update_form("L", home_goals, away_goals)
            self.away.update_form("W", away_goals, home_goals)
        else:
            self.home.update_form("D", home_goals, away_goals)
            self.away.update_form("D", away_goals, home_goals)
        return self

    # ------------------------------------------------------------------
    def elo_difference(self) -> float:
        """主客队 Elo 差。"""
        return self.home.elo_rating - self.away.elo_rating

    # ------------------------------------------------------------------
    def parsed_date(self) -> Optional[date]:
        """尝试解析 date 字符串为 datetime.date。"""
        if not self.date:
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(self.date, fmt).date()
            except ValueError:
                continue
        return None

    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        res = f" ({self.result})" if self.result else ""
        return f"Match({self.home.name} vs {self.away.name}{res}, neutral={self.neutral})"

    def __str__(self) -> str:
        if self.result:
            return f"{self.home.name} {self.result} {self.away.name}"
        return f"{self.home.name} vs {self.away.name}"
