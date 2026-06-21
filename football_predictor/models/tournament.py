"""
models/tournament.py - 赛事/赛程模型
======================================

封装一个杯赛或联赛的赛程结构，支持：
    - 小组赛阶段（多组多队）
    - 淘汰赛阶段（1/8、1/4、半决赛、决赛等）
    - 自动推进比赛结果与晋级队伍

使用示例:
    >>> from football_predictor.models.tournament import Tournament
    >>> wc = Tournament(name="World Cup 2026", host="加拿大/美国/墨西哥")
    >>> wc.add_group("A", [team1, team2, team3, team4])
    >>> ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from football_predictor.models.team import Team
from football_predictor.models.match import Match


# ---------------------------------------------------------------------------
# 小组赛
# ---------------------------------------------------------------------------
@dataclass
class Group:
    """一个小组，包含若干球队与已进行的比赛。"""

    name: str
    teams: List[Team] = field(default_factory=list)
    matches: List[Match] = field(default_factory=list)

    # ------------------------------------------------------------------
    def standings(self) -> List[Tuple[Team, int, int, int, int, int, int, int]]:
        """返回小组积分榜 (球队, 积分, 场次, 胜, 平, 负, 进, 失, 净胜)。

        数据以 list[tuple] 形式返回，按积分 -> 净胜球 -> 进球数 排序。
        """
        stats: Dict[str, Dict[str, int]] = {
            t.name: {"p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0}
            for t in self.teams
        }
        for m in self.matches:
            if not m.has_result:
                continue
            h, a = m.home, m.away
            gh, ga = m.result.home_goals, m.result.away_goals
            stats[h.name]["p"] += 3 if gh > ga else (1 if gh == ga else 0)
            stats[a.name]["p"] += 3 if ga > gh else (1 if ga == gh else 0)
            stats[h.name]["w"] += 1 if gh > ga else 0
            stats[a.name]["w"] += 1 if ga > gh else 0
            stats[h.name]["d"] += 1 if gh == ga else 0
            stats[a.name]["d"] += 1 if ga == gh else 0
            stats[h.name]["l"] += 1 if gh < ga else 0
            stats[a.name]["l"] += 1 if ga < gh else 0
            stats[h.name]["gf"] += gh
            stats[h.name]["ga"] += ga
            stats[a.name]["gf"] += ga
            stats[a.name]["ga"] += gh
            for s in (stats[h.name], stats[a.name]):
                s["played"] = s.get("played", 0) + 1

        by_team = {t.name: t for t in self.teams}
        rows = []
        for name, s in stats.items():
            team = by_team[name]
            played = s.get("played", 0)
            rows.append((
                team, s["p"], played, s["w"], s["d"], s["l"],
                s["gf"], s["ga"], s["gf"] - s["ga"],
            ))
        rows.sort(key=lambda r: (-r[1], -(r[8]), -r[6]))
        return rows

    # ------------------------------------------------------------------
    def top_teams(self, n: int = 2) -> List[Team]:
        """返回积分榜前 n 支球队（通常用于计算晋级）。"""
        return [row[0] for row in self.standings()[:n]]

    # ------------------------------------------------------------------
    def add_match(self, match: Match) -> None:
        if match.home not in self.teams or match.away not in self.teams:
            raise ValueError("比赛球队必须在该小组中")
        self.matches.append(match)


# ---------------------------------------------------------------------------
# 淘汰赛轮次
# ---------------------------------------------------------------------------
@dataclass
class KnockoutRound:
    """一轮淘汰赛（如 1/8 决赛），包含多场比赛。"""

    name: str
    matches: List[Match] = field(default_factory=list)

    # ------------------------------------------------------------------
    def winners(self) -> List[Team]:
        """返回本轮胜出的球队列表（根据已有赛果）。"""
        winners: List[Team] = []
        for m in self.matches:
            if not m.has_result:
                continue
            if m.result.winner == "home":
                winners.append(m.home)
            elif m.result.winner == "away":
                winners.append(m.away)
        return winners

    # ------------------------------------------------------------------
    def add_match(self, match: Match) -> None:
        self.matches.append(match)


# ---------------------------------------------------------------------------
# 赛事
# ---------------------------------------------------------------------------
@dataclass
class Tournament:
    """一个完整的赛事。"""

    name: str
    host: str = ""
    groups: Dict[str, Group] = field(default_factory=dict)
    knockout_rounds: List[KnockoutRound] = field(default_factory=list)

    # ------------------------------------------------------------------
    def add_group(self, name: str, teams: List[Team]) -> Group:
        group = Group(name=name, teams=teams)
        self.groups[name] = group
        return group

    # ------------------------------------------------------------------
    def add_knockout_round(self, name: str, matches: Optional[List[Match]] = None) -> KnockoutRound:
        rnd = KnockoutRound(name=name, matches=matches or [])
        self.knockout_rounds.append(rnd)
        return rnd

    # ------------------------------------------------------------------
    def all_matches(self) -> List[Match]:
        all_m: List[Match] = []
        for g in self.groups.values():
            all_m.extend(g.matches)
        for rnd in self.knockout_rounds:
            all_m.extend(rnd.matches)
        return all_m

    # ------------------------------------------------------------------
    def all_teams(self) -> List[Team]:
        teams: List[Team] = []
        seen = set()
        for g in self.groups.values():
            for t in g.teams:
                if t.name not in seen:
                    seen.add(t.name)
                    teams.append(t)
        return teams

    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"Tournament(name={self.name!r}, "
            f"groups={len(self.groups)}, "
            f"knockout_rounds={len(self.knockout_rounds)})"
        )
