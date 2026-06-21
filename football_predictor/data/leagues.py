"""
data/leagues.py - 联赛数据（示例框架）
===========================================

提供常见联赛的基础数据接口与样本球队，便于演示用。
"""

from __future__ import annotations

from typing import Dict, List

from football_predictor.models.team import Team, Player


# 英超（示例部分球队）
EPL_TEAMS: List[Dict[str, object]] = [
    {
        "name": "曼城", "country": "England", "elo_rating": 2050,
        "squad_depth": 9, "form": 9, "market_value": 1300, "formation": "4-3-3",
        "key_players": [("哈兰德", "FW", 91, 25), ("罗德里", "MF", 89, 30),
                        ("福登", "MF", 88, 26)],
    },
    {
        "name": "阿森纳", "country": "England", "elo_rating": 2000,
        "squad_depth": 9, "form": 9, "market_value": 1200, "formation": "4-3-3",
        "key_players": [("萨卡", "FW", 87, 24), ("厄德高", "MF", 87, 27)],
    },
    {
        "name": "利物浦", "country": "England", "elo_rating": 1995,
        "squad_depth": 8, "form": 8, "market_value": 1150, "formation": "4-3-3",
        "key_players": [("萨拉赫", "FW", 89, 34)],
    },
]


def build_league_team(raw: Dict[str, object]) -> Team:
    team = Team(
        name=raw["name"], country=raw.get("country", ""),
        elo_rating=float(raw["elo_rating"]),
        squad_depth=float(raw["squad_depth"]), form=float(raw["form"]),
        market_value=float(raw["market_value"]),
        formation=raw["formation"],
    )
    for p in raw.get("key_players", []):
        team.add_player(Player(name=p[0], position=p[1], rating=float(p[2]), age=int(p[3])))
    return team


LEAGUES: Dict[str, List[Team]] = {
    "EPL": [build_league_team(t) for t in EPL_TEAMS],
}
