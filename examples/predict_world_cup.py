"""
examples/predict_world_cup.py - 2026 世界杯预测示例
=====================================================

演示如何利用内置的 2026 世界杯数据：
    - 预测焦点比赛（如阿根廷 vs 法国）
    - 预测某场小组赛
    - 输出某队晋级概率的启发式估计

使用:
    $ python examples/predict_world_cup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from football_predictor import PredictionEngine
from football_predictor.data.world_cup_2026 import TEAMS, get_tournament


def demo_final() -> None:
    """模拟预测 '阿根廷 vs 法国' 焦点战。"""
    print("=" * 60)
    print(">>> 世界杯焦点战预测: 阿根廷 vs 法国 (中立场地)")
    print("=" * 60)
    engine = PredictionEngine()
    pred = engine.predict_match(TEAMS["阿根廷"], TEAMS["法国"], neutral=True)
    print(pred)
    print()


def demo_group_matches() -> None:
    """展示 B 组各比赛的预测结果。"""
    t = get_tournament()
    engine = PredictionEngine()
    group = t.groups["B"]
    print("=" * 60)
    print(f">>> B 组比赛预测 (球队: {[tm.name for tm in group.teams]})")
    print("=" * 60)
    for m in group.matches:
        pred = engine.predict_match(m.home, m.away, neutral=True)
        print(pred)
        print("-" * 60)


def demo_group_standings() -> None:
    """输出某组的积分榜。"""
    t = get_tournament(apply_sample_results=True)
    print("\n>>> B 组积分榜（基于示例赛果）")
    print(f"{'球队':<12}{'积分':<6}{'胜':<4}{'平':<4}{'负':<4}{'进球':<6}{'失球':<6}")
    print("-" * 50)
    standings = t.groups["B"].standings()
    for team, pts, played, w, d, l, gf, ga, gd in standings:
        print(f"{team.name:<12}{pts:<6}{w:<4}{d:<4}{l:<4}{gf:<6}{ga:<6}")


if __name__ == "__main__":
    demo_final()
    demo_group_matches()
    demo_group_standings()
