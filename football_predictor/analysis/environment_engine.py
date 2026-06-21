"""
analysis/environment_engine.py - 环境压力与心理状态引擎
=========================================================

足球比赛中，球员的发挥不仅取决于技战术，还受到环境因素和心理状态的
显著影响。本引擎量化以下因素：

环境因素:
    - altitude:        海拔效应（高海拔缺氧，体能下降，进球可能减少或增加）
    - climate:         气候适应（湿热/干冷对不适应球队的影响）
    - travel_fatigue:  旅行疲劳（长途飞行后的恢复时间）
    - crowd_support:   现场氛围（主场或中立场地观众倾向）

心理因素:
    - coach_pressure:  教练压力（帅位不稳 → 球员紧张/保守）
    - player_morale:   球员士气（更衣室氛围、续约传闻等）
    - tournament_stage: 赛事阶段压力（小组赛 vs 淘汰赛 vs 决赛）
    - expectation:     外界期望（被看好的一方可能紧张或激发）

所有方法返回一个 [-1.0, +1.0] 的 delta 值，正值表示对球队有利
（提升 lambda 或评分），负值表示不利。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from football_predictor.models.team import Team


# ---------------------------------------------------------------------------
# 城市环境数据（2026世界杯举办城市）
# ---------------------------------------------------------------------------
CITY_ENVIRONMENT: Dict[str, Dict[str, float]] = {
    # 城市: {altitude(米), humidity(0-1), temp_c(摄氏度)}
    "墨西哥城":     {"altitude": 2240, "humidity": 0.45, "temp_c": 22},
    "瓜达拉哈拉":   {"altitude": 1566, "humidity": 0.50, "temp_c": 25},
    "蒙特雷":       {"altitude": 537,  "humidity": 0.55, "temp_c": 33},
    "多伦多":       {"altitude": 76,   "humidity": 0.60, "temp_c": 24},
    "温哥华":       {"altitude": 70,   "humidity": 0.65, "temp_c": 20},
    "洛杉矶":       {"altitude": 93,   "humidity": 0.55, "temp_c": 26},
    "旧金山湾区":   {"altitude": 16,   "humidity": 0.65, "temp_c": 19},
    "西雅图":       {"altitude": 53,   "humidity": 0.70, "temp_c": 21},
    "达拉斯":       {"altitude": 131,  "humidity": 0.60, "temp_c": 35},
    "休斯顿":       {"altitude": 15,   "humidity": 0.75, "temp_c": 34},
    "堪萨斯城":     {"altitude": 274,  "humidity": 0.60, "temp_c": 32},
    "亚特兰大":     {"altitude": 315,  "humidity": 0.60, "temp_c": 31},
    "迈阿密":       {"altitude": 2,    "humidity": 0.75, "temp_c": 31},
    "波士顿":       {"altitude": 43,   "humidity": 0.60, "temp_c": 24},
    "费城":         {"altitude": 12,   "humidity": 0.60, "temp_c": 28},
    "纽约/新泽西":  {"altitude": 10,   "humidity": 0.60, "temp_c": 27},
}

# 默认环境（未找到城市时）
DEFAULT_ENV = {"altitude": 100, "humidity": 0.55, "temp_c": 25}


@dataclass
class EnvironmentEngine:
    """环境压力与心理状态分析引擎。

    所有方法返回 [-1.0, +1.0] 的 delta 值。
    """

    # 高海拔阈值（米）
    altitude_threshold: float = 1000.0
    # 高温阈值（摄氏度）
    heat_threshold: float = 30.0
    # 高湿阈值
    humidity_threshold: float = 0.70

    # ------------------------------------------------------------------
    # 环境因素
    # ------------------------------------------------------------------
    def altitude_effect(self, city: str, team: Team) -> float:
        """海拔效应。

        高海拔（>1000米）对所有球队都有体能影响，但对不适应的球队影响更大。
        墨西哥城（2240m）和瓜达拉哈拉（1566m）是高海拔城市。
        中北美洲球队（美国、墨西哥、加拿大）对高海拔更适应。
        """
        env = CITY_ENVIRONMENT.get(city, DEFAULT_ENV)
        alt = env["altitude"]

        if alt < self.altitude_threshold:
            return 0.0

        # 高海拔影响程度（0-1）
        severity = min(1.0, (alt - self.altitude_threshold) / 1500.0)

        # 中北美洲球队更适应
        conf = getattr(team, "country", "")
        if conf in ("CONCACAF",):
            return -0.1 * severity  # 轻微影响
        # 南美球队也有一定适应
        if conf in ("CONMEBOL",):
            return -0.2 * severity
        # 欧洲/亚洲/非洲球队受影响大
        return -0.4 * severity

    # ------------------------------------------------------------------
    def climate_effect(self, city: str, team: Team) -> float:
        """气候适应效应。

        高温高湿对北欧球队影响大，对热带/亚热带球队影响小。
        """
        env = CITY_ENVIRONMENT.get(city, DEFAULT_ENV)
        temp = env["temp_c"]
        humidity = env["humidity"]

        if temp < self.heat_threshold and humidity < self.humidity_threshold:
            return 0.0

        # 高温高湿严重程度
        heat_severity = 0.0
        if temp >= self.heat_threshold:
            heat_severity += (temp - self.heat_threshold) / 10.0  # 每超10度+1
        if humidity >= self.humidity_threshold:
            heat_severity += (humidity - self.humidity_threshold) * 3.0
        heat_severity = min(1.0, heat_severity)

        conf = getattr(team, "country", "")
        # 非洲、中北美、南美球队更适应高温
        if conf in ("CAF", "CONCACAF", "CONMEBOL"):
            return -0.1 * heat_severity
        # 亚洲球队部分适应
        if conf in ("AFC",):
            return -0.2 * heat_severity
        # 北欧球队（挪威、瑞典、丹麦、苏格兰等）受影响大
        cold_countries = {"挪威", "瑞典", "丹麦", "苏格兰", "冰岛", "芬兰"}
        if team.name in cold_countries:
            return -0.5 * heat_severity
        # 其他欧洲球队
        if conf in ("UEFA",):
            return -0.3 * heat_severity
        return -0.2 * heat_severity

    # ------------------------------------------------------------------
    def travel_fatigue_effect(self, team: Team, city: str,
                              prev_city: Optional[str] = None) -> float:
        """旅行疲劳效应。

        如果球队上一场比赛在另一个城市，长途旅行会导致疲劳。
        """
        if prev_city is None or prev_city == city:
            return 0.0

        # 简化：跨城市旅行 = -0.1 到 -0.2
        # 跨时区旅行更严重（东西向）
        return -0.15

    # ------------------------------------------------------------------
    # 心理因素
    # ------------------------------------------------------------------
    def coach_pressure_effect(self, team: Team,
                              pressure_level: float = 0.0) -> float:
        """教练压力效应。

        Args:
            team: 球队
            pressure_level: 教练压力等级 0-1（0=无压力，1=极度压力）

        高压下球员可能：
        - 过于紧张 → 发挥失常（负delta）
        - 但也有"背水一战"的激发效应（正delta）
        这里取净效应为轻微负面。
        """
        if pressure_level <= 0:
            return 0.0
        # 净效应：压力越大，负面影响越大，但有10%的激发可能
        return -0.3 * min(1.0, pressure_level)

    # ------------------------------------------------------------------
    def player_morale_effect(self, team: Team,
                             morale_level: float = 0.5) -> float:
        """球员士气效应。

        Args:
            morale_level: 球员士气 0-1（0=极低，1=极高，0.5=正常）

        士气高的球队进攻更积极，士气低的球队保守。
        """
        # 将 0-1 映射到 [-0.4, +0.4]
        return (morale_level - 0.5) * 0.8

    # ------------------------------------------------------------------
    def tournament_stage_pressure(self, team: Team,
                                  stage: str = "group") -> float:
        """赛事阶段压力效应。

        Args:
            stage: "group"（小组赛）/ "round16"（16强）/ "quarter"（8强）
                   / "semi"（半决赛）/ "final"（决赛）

        越到后期压力越大，但强队（Elo高）更能承受压力。
        """
        stage_pressure = {
            "group": 0.1,
            "round16": 0.3,
            "quarter": 0.5,
            "semi": 0.7,
            "final": 1.0,
        }
        pressure = stage_pressure.get(stage, 0.1)

        # 强队抗压能力强
        if team.elo_rating >= 1950:
            return 0.1 * pressure  # 轻微正面（大赛经验）
        elif team.elo_rating >= 1800:
            return -0.1 * pressure  # 轻微负面
        else:
            return -0.3 * pressure  # 弱队压力下发挥失常

    # ------------------------------------------------------------------
    def expectation_effect(self, team: Team, opponent: Team) -> float:
        """外界期望效应。

        被广泛看好的一方可能：
        - 过于自信 → 轻敌（负delta）
        - 但也有"实力碾压"的自信（正delta）
        净效应取决于实力差距大小。
        """
        elo_diff = team.elo_rating - opponent.elo_rating
        if abs(elo_diff) < 100:
            return 0.0  # 势均力敌，无期望偏差

        if elo_diff > 0:
            # 被看好的一方：轻微轻敌风险
            return -0.05 * min(1.0, elo_diff / 300.0)
        else:
            # 不被看好的一方：可能有"光脚不怕穿鞋"的激发
            return 0.1 * min(1.0, abs(elo_diff) / 300.0)

    # ------------------------------------------------------------------
    # 汇总
    # ------------------------------------------------------------------
    def total_environment_adjustment(
        self,
        team: Team,
        opponent: Team,
        city: str = "",
        stage: str = "group",
        prev_city: Optional[str] = None,
        coach_pressure: float = 0.0,
        player_morale: float = 0.5,
    ) -> float:
        """返回球队总环境+心理修正值（[-1.0, +1.0]）。

        这个值可以直接作为 lambda 的乘法因子偏移或评分维度的加减项。
        """
        alt = self.altitude_effect(city, team) if city else 0.0
        clim = self.climate_effect(city, team) if city else 0.0
        travel = self.travel_fatigue_effect(team, city, prev_city)
        coach = self.coach_pressure_effect(team, coach_pressure)
        morale = self.player_morale_effect(team, player_morale)
        stage_p = self.tournament_stage_pressure(team, stage)
        expect = self.expectation_effect(team, opponent)

        total = alt + clim + travel + coach + morale + stage_p + expect
        return round(max(-1.0, min(1.0, total)), 3)

    # ------------------------------------------------------------------
    def detailed_report(
        self,
        team: Team,
        opponent: Team,
        city: str = "",
        stage: str = "group",
        prev_city: Optional[str] = None,
        coach_pressure: float = 0.0,
        player_morale: float = 0.5,
    ) -> Dict[str, float]:
        """返回详细的环境+心理修正报告（调试用）。"""
        return {
            "altitude": self.altitude_effect(city, team) if city else 0.0,
            "climate": self.climate_effect(city, team) if city else 0.0,
            "travel_fatigue": self.travel_fatigue_effect(team, city, prev_city),
            "coach_pressure": self.coach_pressure_effect(team, coach_pressure),
            "player_morale": self.player_morale_effect(team, player_morale),
            "stage_pressure": self.tournament_stage_pressure(team, stage),
            "expectation": self.expectation_effect(team, opponent),
            "total": self.total_environment_adjustment(
                team, opponent, city, stage, prev_city,
                coach_pressure, player_morale,
            ),
        }
