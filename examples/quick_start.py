"""
examples/quick_start.py - 快速入门示例
===========================================

演示如何创建两支球队、运行评分/预测引擎并打印结果。

使用:
    $ python examples/quick_start.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 确保能 import 本仓库的 football_predictor
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from football_predictor import Team, PredictionEngine
from football_predictor.models.match import Match


def main() -> None:
    # 1) 创建两支球队
    home = Team(
        name="曼城", country="England",
        elo_rating=2050, squad_depth=9, form=9,
        market_value=1300, formation="4-3-3",
    )
    away = Team(
        name="阿森纳", country="England",
        elo_rating=2000, squad_depth=8, form=8,
        market_value=1200, formation="4-3-3",
    )
    # 为 home 注入一些近期战绩（用于测试动量引擎）
    for _ in range(3):
        home.update_form("W", 3, 1)
    away.update_form("L", 0, 2)
    away.update_form("W", 3, 1)
    away.update_form("D", 1, 1)

    # 2) 构造比赛对象（可选，展示 Match API）
    match = Match(home, away, competition="English Premier League", stage="第30轮")
    print(">>>", match, "\n")

    # 3) 预测
    engine = PredictionEngine()
    prediction = engine.predict_match(home, away)
    print(prediction)

    # 4) 直接使用 predict_score 返回字典
    print("\n--- 原始数据字典 ---")
    data = engine.predict_score(home, away)
    for k, v in data.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
