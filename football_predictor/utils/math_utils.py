"""
utils/math_utils.py - Poisson 分布与概率相关辅助函数
=====================================================

提供泊松分布与足球比分预测所需的数学基础。为了让项目保持零外部
依赖即可运行，这里实现了一个纯 Python 的泊松 PMF/CDF 近似；若系统
安装了 scipy，则会自动使用 scipy.stats.poisson 以获得更高精度。

核心函数:
    - poisson_pmf(k, lam):            P(X = k)
    - poisson_cdf(k, lam):            P(X <= k)
    - match_probability(lam_h, lam_a, gh, ga):
      精确的 (gh, ga) 比分联合概率（假设独立）
    - outcome_probabilities(lam_h, lam_a):
      返回 {胜, 平, 负} 三种结果的累积概率
    - most_probable_scoreline(lam_h, lam_a, top_n):
      返回最可能的 top_n 个比分
    - over_under_probability(lam_h, lam_a, threshold):
      总进球数大于 threshold 的概率
    - elo_win_probability(elo_diff, k_factor_scale=400):
      经典 Elo 胜率

设计说明:
    - 计算 "2-1" 这样的比分概率时，我们同时计算主队进 2 球、
      客队进 1 球的联合概率，即 poisson_pmf(2, lam_h) * poisson_pmf(1, lam_a)。
    - 对平局与胜/负概率，我们计算一个 0..MAX_GOALS 的二维求和表格，
      MAX_GOALS 默认取 8，对于 lambda <= 3.0 的情形误差可以忽略。
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 基础数学工具
# ---------------------------------------------------------------------------
def clamp(x: float, lo: float, hi: float) -> float:
    """将 x 限制在 [lo, hi] 区间。"""
    return max(lo, min(hi, x))


def lerp(a: float, b: float, t: float) -> float:
    """线性插值。"""
    return a + (b - a) * t


# ---------------------------------------------------------------------------
# Poisson 分布
# ---------------------------------------------------------------------------
# 若 scipy 可用则使用其高精度实现，否则使用纯 Python 版本
try:  # pragma: no cover - 可选依赖
    from scipy.stats import poisson as _sp  # type: ignore

    def poisson_pmf(k: int, lam: float) -> float:
        if lam <= 0 or k < 0:
            return 0.0 if k != 0 else 1.0 if lam == 0 else 0.0
        return float(_sp.pmf(k, lam))

    def poisson_cdf(k: int, lam: float) -> float:
        if lam <= 0:
            return 1.0
        return float(_sp.cdf(k, lam))

except Exception:  # pragma: no cover
    def poisson_pmf(k: int, lam: float) -> float:
        """纯 Python 版 Poisson PMF。

        使用对数域计算以避免大 k 时的数值溢出。
        """
        if lam <= 0 or k < 0:
            return 0.0 if k != 0 else 1.0 if lam == 0 else 0.0
        # log P(k; lam) = -lam + k*ln(lam) - ln(k!)
        log_p = -lam + k * math.log(lam) - math.lgamma(k + 1)
        return math.exp(log_p)

    def poisson_cdf(k: int, lam: float) -> float:
        if lam <= 0:
            return 1.0
        if k < 0:
            return 0.0
        # 使用递推：P(0) + P(1) + ... + P(k)
        cdf = 0.0
        pmf = math.exp(-lam)
        cdf += pmf
        for i in range(1, int(k) + 1):
            pmf = pmf * lam / i
            cdf += pmf
        return cdf


# ---------------------------------------------------------------------------
def draw_probability(lam_h: float, lam_a: float, max_goals: int = 8) -> float:
    """计算平局概率。"""
    if lam_h <= 0 or lam_a <= 0:
        return 0.0
    p = 0.0
    for k in range(max_goals + 1):
        p += poisson_pmf(k, lam_h) * poisson_pmf(k, lam_a)
    return p


# ---------------------------------------------------------------------------
def match_probability(lam_h: float, lam_a: float,
                      home_goals: int, away_goals: int) -> float:
    """返回精确比分 (home_goals, away_goals) 的概率。"""
    return poisson_pmf(home_goals, lam_h) * poisson_pmf(away_goals, lam_a)


# ---------------------------------------------------------------------------
def outcome_probabilities(lam_h: float, lam_a: float,
                          max_goals: int = 8) -> Tuple[float, float, float]:
    """返回 (主胜概率, 平局概率, 客胜概率)。"""
    home_w, draw, away_w = 0.0, 0.0, 0.0
    for h in range(max_goals + 1):
        ph = poisson_pmf(h, lam_h)
        for a in range(max_goals + 1):
            pa = poisson_pmf(a, lam_a)
            joint = ph * pa
            if h > a:
                home_w += joint
            elif h < a:
                away_w += joint
            else:
                draw += joint
    # 归一化防止浮点截断导致 != 1.0
    total = home_w + draw + away_w
    if total <= 0:
        return 0.333, 0.334, 0.333
    return home_w / total, draw / total, away_w / total


# ---------------------------------------------------------------------------
def most_probable_scoreline(lam_h: float, lam_a: float,
                            top_n: int = 5,
                            max_goals: int = 8,
                            dc_rho: float = 0.0) -> List[Tuple[int, int, float]]:
    """返回最可能的 top_n 个比分，按概率降序。

    Args:
        dc_rho: Dixon-Coles 修正参数。当 > 0 时，对低比分（0-0, 1-0, 0-1, 1-1）
                应用修正因子 τ，更符合足球实际。

    Returns:
        List[(home_goals, away_goals, probability)]
    """
    results: List[Tuple[int, int, float]] = []
    for h in range(max_goals + 1):
        ph = poisson_pmf(h, lam_h)
        if ph < 1e-5:
            continue
        for a in range(max_goals + 1):
            pa = poisson_pmf(a, lam_a)
            if pa < 1e-5:
                continue
            p = ph * pa
            # Dixon-Coles 低比分修正
            if dc_rho > 0:
                p *= _dixon_coles_tau(h, a, lam_h, lam_a, dc_rho)
            results.append((h, a, p))
    # 归一化（Dixon-Coles 修正后概率不再和为1）
    total = sum(r[2] for r in results)
    if total > 0:
        results = [(h, a, p / total) for h, a, p in results]
    results.sort(key=lambda t: t[2], reverse=True)
    return results[:top_n]


# ---------------------------------------------------------------------------
def _dixon_coles_tau(h: int, a: int, lam_h: float, lam_a: float,
                     rho: float) -> float:
    """Dixon-Coles 低比分修正因子 τ。

    当双方进球都 <= 1 时，根据 lambda 大小调整概率：
    - 0-0: τ = 1 - lam_h * lam_a * rho （增大）
    - 1-0: τ = 1 + lam_a * rho         （增大）
    - 0-1: τ = 1 + lam_h * rho         （增大）
    - 1-1: τ = 1 - rho                 （减小）

    rho 通常取 0.01 ~ 0.05。
    """
    if h == 0 and a == 0:
        return 1.0 - lam_h * lam_a * rho
    elif h == 0 and a == 1:
        return 1.0 + lam_h * rho
    elif h == 1 and a == 0:
        return 1.0 + lam_a * rho
    elif h == 1 and a == 1:
        return 1.0 - rho
    return 1.0


# ---------------------------------------------------------------------------
def outcome_probabilities_dc(lam_h: float, lam_a: float,
                             dc_rho: float = 0.0,
                             max_goals: int = 8) -> Tuple[float, float, float]:
    """带 Dixon-Coles 修正的胜负平概率。"""
    home_w, draw, away_w = 0.0, 0.0, 0.0
    for h in range(max_goals + 1):
        ph = poisson_pmf(h, lam_h)
        for a in range(max_goals + 1):
            pa = poisson_pmf(a, lam_a)
            joint = ph * pa
            if dc_rho > 0:
                joint *= _dixon_coles_tau(h, a, lam_h, lam_a, dc_rho)
            if h > a:
                home_w += joint
            elif h < a:
                away_w += joint
            else:
                draw += joint
    total = home_w + draw + away_w
    if total <= 0:
        return 0.333, 0.334, 0.333
    return home_w / total, draw / total, away_w / total


# ---------------------------------------------------------------------------
def over_under_probability(lam_h: float, lam_a: float,
                           total_goals: float,
                           max_goals: int = 15) -> Tuple[float, float]:
    """返回 (Over, Under) 总进球数概率。

    Under = P(总进球数 < total_goals)，Over = 1 - Under。
    """
    lam_total = lam_h + lam_a
    under = poisson_cdf(int(math.floor(total_goals - 1e-9)), lam_total)
    # 手工累加以避免 CDF 近似误差
    under2 = sum(poisson_pmf(k, lam_total) for k in range(int(total_goals)))
    under = max(under, under2)
    return (1.0 - under), under


# ---------------------------------------------------------------------------
def poisson_compare(lam_h: float, lam_a: float) -> Dict[str, float]:
    """聚合版本：一次性返回胜/平/负、最可能比分、大小球判断。"""
    hw, d, aw = outcome_probabilities(lam_h, lam_a)
    scores = most_probable_scoreline(lam_h, lam_a, top_n=3)
    over, under = over_under_probability(lam_h, lam_a, 2.5)
    return {
        "home_win": hw,
        "draw": d,
        "away_win": aw,
        "top_scores": scores,
        "over_25": over,
        "under_25": under,
    }


# ---------------------------------------------------------------------------
# Elo 胜率
# ---------------------------------------------------------------------------
def elo_win_probability(elo_diff: float, scale: float = 400.0) -> float:
    """经典 Elo 胜率公式： 1 / (1 + 10^(-elo_diff/scale))。"""
    return 1.0 / (1.0 + 10 ** (-elo_diff / scale))
