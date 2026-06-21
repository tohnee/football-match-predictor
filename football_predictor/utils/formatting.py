"""
utils/formatting.py - 输出格式化工具
=======================================

将引擎输出的原始数值（概率、评分、比分）格式化为对人类友好的
文本与表格，便于在日志、报告和示例中直接使用。
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Iterable


# ---------------------------------------------------------------------------
def format_percent(value: float, precision: int = 1) -> str:
    """将 0-1 的浮点数格式化为 "xx.x%"。"""
    return f"{value * 100:.{precision}f}%"


# ---------------------------------------------------------------------------
def format_scoreline(home_goals: int, away_goals: int,
                     probability: float | None = None) -> str:
    base = f"{home_goals}-{away_goals}"
    if probability is not None:
        return f"{base} ({format_percent(probability)})"
    return base


# ---------------------------------------------------------------------------
def format_scoreline_table(top_scores: List[Tuple[int, int, float]],
                           header: str = "最可能比分") -> str:
    """把比分列表打印为简单表格。"""
    lines = [f"=== {header} ==="]
    lines.append(f"{'排名':<6}{'比分':<12}{'概率':<10}")
    lines.append("-" * 28)
    for rank, (h, a, prob) in enumerate(top_scores, start=1):
        lines.append(f"{rank:<6}{h}-{a:<10}{format_percent(prob):<10}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
def pprint_rating(team_name: str, scores: Dict[str, float],
                  final: float) -> str:
    """打印球队多维度评分概览。"""
    lines = [f"=== {team_name} 综合评分 ===",
             f"{'维度':<12}{'得分 (1-10)':<15}{'权重':<10}"]
    lines.append("-" * 37)
    weights = {
        "overall": 0.20,
        "form": 0.20,
        "home_away": 0.10,
        "tactical": 0.15,
        "squad": 0.15,
        "mental": 0.10,
        "context": 0.10,
    }
    for dim in ("overall", "form", "home_away", "tactical", "squad",
                "mental", "context"):
        v = scores.get(dim, 0.0)
        w = weights.get(dim, 0.0)
        lines.append(f"{dim:<12}{v:<15.2f}{w*100:<10.0f}%")
    lines.append("-" * 37)
    lines.append(f"{'最终评分':<12}{final:<15.2f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
def bullet_list(items: Iterable[str]) -> str:
    """将可迭代对象转成子弹列表。"""
    return "\n".join(f"- {it}" for it in items)
