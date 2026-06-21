"""
data/__init__.py - 内置数据包
===============================
"""

from football_predictor.data.world_cup_2026 import (
    TEAMS as WC_TEAMS,
    GROUP_STAGE as WC_GROUP_STAGE,
    KNOCKOUT as WC_KNOCKOUT,
    get_tournament,
    build_team,
)

__all__ = [
    "WC_TEAMS",
    "WC_GROUP_STAGE",
    "WC_KNOCKOUT",
    "get_tournament",
    "build_team",
]
