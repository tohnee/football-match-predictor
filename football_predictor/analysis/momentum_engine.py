"""
analysis/momentum_engine.py - 动力与情绪效应修正引擎
=======================================================

对应 v3.3 框架中的"动力/情绪效应修正系数"章节：
    - check_rebound_effect:   反弹效应（连败后触底反弹）
    - check_bottom_effect:    触底反弹（极度沮丧后的精神力量）
    - check_blowout_illusion: 大胜幻觉（上一场大胜后容易松懈）
    - check_emotional_stack:  情绪叠加（连胜带来的心理加成）
    - check_derby_or_final:   特殊比赛情绪（决赛、德比）
    - total_adjustment:       汇总得到最终 +/- 调整值

所有方法均返回一个 1-10 评分系统的 delta 值，供 Rating Engine
直接加到某个维度上。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from football_predictor.models.team import Team


@dataclass
class MomentumEngine:
    """动力与情绪效应分析引擎。"""

    # 可通过 config 调节各个子效应的最大/最小幅度
    max_rebound: float = 1.2
    max_bottom: float = 1.5
    max_blowout: float = -1.2
    max_streak_bonus: float = 1.0
    max_lose_streak: float = -1.0
    final_game_bonus: float = 0.8

    # ------------------------------------------------------------------
    # 1. 反弹效应（连败 3+ 场后，精神力量 +）
    # ------------------------------------------------------------------
    def check_rebound_effect(self, team: Team, opponent: Team) -> float:
        """连败 >= 3 场时触发正反弹 +，且对手越强反弹越大。"""
        recent = team.recent_form[-5:]  # 最近 5 场
        consecutive_loss = 0
        for result in reversed(recent):
            if result == "L":
                consecutive_loss += 1
            else:
                break
        if consecutive_loss >= 3:
            # 基本反弹 + 对手 Elo 越高、反弹越强（最多 +1.2）
            delta = 0.4 + min(0.8, (opponent.elo_rating - 1500) / 800)
            return min(self.max_rebound, delta)
        return 0.0

    # ------------------------------------------------------------------
    # 2. 触底反弹（最近 5 场全输，且失球很多）
    # ------------------------------------------------------------------
    def check_bottom_effect(self, team: Team, opponent: Team) -> float:
        """极端情况下的精神力量爆发。"""
        recent = team.recent_form[-5:]
        if len(recent) < 3:
            return 0.0
        lose_ratio = recent.count("L") / len(recent)
        if lose_ratio >= 0.8:
            # 场均失球越多，底部越深 -> 反弹越强
            if team.recent_goals_against:
                avg_ga = sum(team.recent_goals_against[-3:]) / max(1, min(3, len(team.recent_goals_against)))
            else:
                avg_ga = 1.0
            delta = 0.5 + min(1.0, (avg_ga - 1.5) * 0.5)
            return min(self.max_bottom, delta)
        return 0.0

    # ------------------------------------------------------------------
    # 3. 大胜幻觉（上一场大比分胜利，容易轻敌）
    # ------------------------------------------------------------------
    def check_blowout_illusion(self, team: Team) -> float:
        """上一场大胜且进球 >= 3 且净胜 >= 3 时产生负面修正。"""
        if not team.recent_form or team.recent_form[-1] != "W":
            return 0.0
        if team.recent_goals_for and team.recent_goals_against:
            last_gf = team.recent_goals_for[-1]
            last_ga = team.recent_goals_against[-1]
            if last_gf >= 3 and (last_gf - last_ga) >= 3:
                return max(self.max_blowout, -0.8)
        return 0.0

    # ------------------------------------------------------------------
    # 4. 情绪叠加（连胜带来的心理加成，连负带来的心理减分）
    # ------------------------------------------------------------------
    def check_emotional_stack(self, team: Team) -> float:
        """基于最近 3-5 场的胜负序列，计算心理加成。"""
        recent = team.recent_form[-4:]
        if not recent:
            return 0.0
        if len(recent) < 2:
            return 0.0
        wins = recent.count("W")
        losses = recent.count("L")
        if wins == len(recent):  # 全胜
            return min(self.max_streak_bonus, 0.6 + 0.2 * len(recent))
        if losses == len(recent):  # 全负
            return max(self.max_lose_streak, -0.6 - 0.2 * len(recent))
        # 一般情况：胜场比例线性映射
        ratio = wins / len(recent)
        return round((ratio - 0.5) * 1.2, 3)

    # ------------------------------------------------------------------
    # 5. 大赛/决赛加成（根据外部 context 传递）
    # ------------------------------------------------------------------
    def check_special_game(self, context: Optional[Dict[str, float]] = None) -> float:
        if not context:
            return 0.0
        return context.get("final_game_bonus", 0.0) + context.get("derby_bonus", 0.0)

    # ------------------------------------------------------------------
    # 6. 黑马检测（v4.1: 近期对强队不败/爆冷，提升信心）
    # ------------------------------------------------------------------
    def check_cinderella_effect(self, team: Team, opponent: Team) -> float:
        """检测球队近期是否有'黑马'表现。

        触发条件：最近比赛中面对Elo比自己高200+的球队取得不败（W或D）。
        效果：提升球队信心和评分（+0.3 ~ +1.0）。

        佛得角案例：Elo 1630，首轮0-0逼平西班牙(Elo 2020)，次轮2-2战平乌拉圭(Elo 1900)。
        """
        if not team.recent_form or not team.recent_goals_for:
            return 0.0

        cinderella_bonus = 0.0
        # 检查最近3场比赛
        check_range = min(3, len(team.recent_form))
        for i in range(check_range):
            result = team.recent_form[i]
            if result in ("W", "D"):
                # 模拟检测：如果对手Elo比本队高200+且取得不败
                # 这里用近期失球作为代理指标：强队交锋中失球少=防守出色
                if team.recent_goals_against and i < len(team.recent_goals_against):
                    ga = team.recent_goals_against[i]
                    gf = team.recent_goals_for[i]
                    # 不败且失球<=2 → 可能是对强队的好结果
                    if ga <= 2 and (result == "W" or (result == "D" and ga <= 1)):
                        # 根据球队Elo越低，黑马效应越强
                        if team.elo_rating < 1700:
                            cinderella_bonus = max(cinderella_bonus, 0.8)
                        elif team.elo_rating < 1800:
                            cinderella_bonus = max(cinderella_bonus, 0.5)
                        elif team.elo_rating < 1900:
                            cinderella_bonus = max(cinderella_bonus, 0.3)
        return round(cinderella_bonus, 3)

    # ------------------------------------------------------------------
    # 汇总
    # ------------------------------------------------------------------
    def total_adjustment(self, team: Team, opponent: Team,
                         context: Optional[Dict[str, float]] = None) -> float:
        """返回球队总动量修正值（加性，用于 1-10 评分维度）。"""
        rebound = self.check_rebound_effect(team, opponent)
        bottom = self.check_bottom_effect(team, opponent)
        blowout = self.check_blowout_illusion(team)
        stack = self.check_emotional_stack(team)
        special = self.check_special_game(context)
        cinderella = self.check_cinderella_effect(team, opponent)

        # 反弹与底部不同时触发（取较大值）
        base = max(rebound, bottom)
        total = base + blowout + stack + special + cinderella

        # 裁剪到 [-1.5, +1.5]
        return round(max(-1.5, min(1.5, total)), 3)

    # ------------------------------------------------------------------
    def detailed_report(self, team: Team, opponent: Team,
                       context: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """返回详细的分项修正值（调试用）。"""
        return {
            "rebound": self.check_rebound_effect(team, opponent),
            "bottom": self.check_bottom_effect(team, opponent),
            "blowout_illusion": self.check_blowout_illusion(team),
            "emotional_stack": self.check_emotional_stack(team),
            "special": self.check_special_game(context),
            "total": self.total_adjustment(team, opponent, context),
        }
