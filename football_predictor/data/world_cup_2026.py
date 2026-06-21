"""
data/world_cup_2026.py - 2026 年美加墨世界杯数据
=================================================

内置 48 支参赛国家队基础数据与完整赛程（小组赛 + 淘汰赛），
包括截至 2026 年 6 月 21 日的参考 Elo、阵容深度与常用阵型。

说明:
    - Elo 为近似值，可作为预测基准；在实际使用中建议接入最新数据。
    - 小组赛采用真实分组（A-H 组，每组 4 队）。
    - 淘汰赛部分标注对阵模板（1/8、1/4、半决赛、决赛）。
    - 赛程数据为示意框架，用户可按实际时间替换。
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Optional

from football_predictor.models.team import Team, Player
from football_predictor.models.tournament import Tournament, Group, KnockoutRound


# ---------------------------------------------------------------------------
# 基础球队数据（按字母顺序）
# 字段: name, country/confederation, elo_rating, squad_depth, form,
#       market_value, formation, key_players (name, pos, rating, age)
# ---------------------------------------------------------------------------
TEAM_RAW: List[Dict[str, object]] = [
    # ======== 北美与加勒比 ========
    {
        "name": "美国", "conf": "CONCACAF", "elo_rating": 1792, "squad_depth": 7,
        "form": 7, "market_value": 320, "formation": "4-3-3",
        "recent_form": ["D", "W", "W", "L", "L", "D", "D", "D"],
        "recent_goals_for": [1, 2, 2, 1, 0, 0, 1, 1],
        "recent_goals_against": [1, 1, 0, 2, 2, 0, 1, 1],
        "style": "pressing",
        "key_players": [("普利西奇", "MF", 85, 27), ("佩皮", "FW", 79, 23),
                        ("罗宾逊", "DF", 79, 28)],
    },
    {
        "name": "墨西哥", "conf": "CONCACAF", "elo_rating": 1850, "squad_depth": 7,
        "form": 7, "market_value": 380, "formation": "4-3-3",
        "recent_form": ["D", "D", "W", "W", "W", "L", "W", "W"],
        "recent_goals_for": [2, 0, 1, 3, 2, 0, 2, 2],
        "recent_goals_against": [2, 0, 0, 1, 0, 2, 0, 1],
        "style": "possession",
        "key_players": [("劳尔-希门尼斯", "FW", 82, 34), ("洛萨诺", "FW", 83, 30),
                        ("瓜尔达多", "MF", 78, 39)],
    },
    {
        "name": "加拿大", "conf": "CONCACAF", "elo_rating": 1685, "squad_depth": 5,
        "form": 6, "market_value": 180, "formation": "4-4-2",
        "recent_form": ["D", "D", "D", "D", "L", "D", "L", "L"],
        "recent_goals_for": [0, 0, 1, 1, 1, 1, 1, 0],
        "recent_goals_against": [0, 0, 1, 1, 2, 1, 2, 1],
        "style": "counter",
        "key_players": [("阿方索-戴维斯", "DF", 85, 25), ("乔纳森-戴维", "FW", 82, 26)],
    },
    {
        "name": "哥斯达黎加", "conf": "CONCACAF", "elo_rating": 1745, "squad_depth": 5,
        "form": 5, "market_value": 80, "formation": "4-4-2",
        "recent_form": ["W", "L", "L", "W", "W", "D", "L", "W"],
        "recent_goals_for": [3, 1, 1, 1, 2, 1, 1, 2],
        "recent_goals_against": [0, 2, 2, 0, 1, 1, 2, 1],
        "style": "park_bus",
        "key_players": [("纳瓦斯", "GK", 83, 39), ("坎贝尔", "FW", 78, 32)],
    },
    {
        "name": "牙买加", "conf": "CONCACAF", "elo_rating": 1620, "squad_depth": 4,
        "form": 5, "market_value": 60, "formation": "4-4-2",
        "recent_form": ["W", "L", "L", "W", "D", "D", "L", "W"],
        "recent_goals_for": [1, 0, 0, 1, 1, 1, 1, 2],
        "recent_goals_against": [0, 2, 3, 0, 1, 1, 3, 0],
        "style": "direct",
        "key_players": [("利昂-贝利", "MF", 80, 28)],
    },
    {
        "name": "巴拿马", "conf": "CONCACAF", "elo_rating": 1690, "squad_depth": 4,
        "form": 5, "market_value": 40, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "L", "D", "D", "L", "L"],
        "recent_goals_for": [0, 0, 1, 1, 0, 2, 0, 1],
        "recent_goals_against": [1, 0, 2, 2, 0, 2, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },

    # ======== 南美洲 ========
    {
        "name": "阿根廷", "conf": "CONMEBOL", "elo_rating": 2060, "squad_depth": 9,
        "form": 9, "market_value": 1200, "formation": "4-3-3",
        "recent_form": ["W", "W", "W", "W", "W", "W", "W", "W"],
        "recent_goals_for": [2, 2, 3, 4, 3, 3, 2, 3],
        "recent_goals_against": [0, 1, 0, 0, 0, 0, 1, 0],
        "style": "possession",
        "key_players": [("梅西", "FW", 90, 39), ("恩佐-费尔南德斯", "MF", 88, 25),
                        ("德保罗", "MF", 86, 32), ("阿尔瓦雷斯", "FW", 86, 26)],
    },
    {
        "name": "巴西", "conf": "CONMEBOL", "elo_rating": 2050, "squad_depth": 9,
        "form": 8, "market_value": 1500, "formation": "4-3-3",
        "recent_form": ["W", "W", "W", "W", "D", "W", "W", "D"],
        "recent_goals_for": [2, 2, 2, 1, 1, 1, 2, 1],
        "recent_goals_against": [0, 0, 1, 0, 1, 0, 0, 1],
        "style": "possession",
        "key_players": [("罗德里戈", "FW", 88, 25), ("维尼修斯", "FW", 91, 26),
                        ("帕奎塔", "MF", 85, 28), ("米利唐", "DF", 86, 28)],
    },
    {
        "name": "乌拉圭", "conf": "CONMEBOL", "elo_rating": 1935, "squad_depth": 7,
        "form": 7, "market_value": 480, "formation": "4-4-2",
        "recent_form": ["D", "D", "W", "D", "W", "W", "L", "W"],
        "recent_goals_for": [2, 1, 2, 1, 3, 2, 0, 2],
        "recent_goals_against": [2, 1, 1, 1, 2, 1, 1, 0],
        "style": "counter",
        "key_players": [("努涅斯", "FW", 86, 27), ("巴尔韦德", "MF", 87, 28),
                        ("苏亚雷斯", "FW", 80, 39)],
    },
    {
        "name": "哥伦比亚", "conf": "CONMEBOL", "elo_rating": 1945, "squad_depth": 7,
        "form": 7, "market_value": 520, "formation": "4-2-3-1",
        "recent_form": ["W", "D", "W", "W", "W", "D", "W", "D"],
        "recent_goals_for": [2, 2, 3, 2, 3, 1, 2, 1],
        "recent_goals_against": [1, 2, 0, 1, 1, 1, 0, 1],
        "style": "counter",
        "key_players": [("哈梅斯", "MF", 82, 34), ("路易斯-迪亚斯", "FW", 87, 29)],
    },
    {
        "name": "智利", "conf": "CONMEBOL", "elo_rating": 1785, "squad_depth": 5,
        "form": 5, "market_value": 130, "formation": "4-3-3",
        "recent_form": ["W", "W", "W", "L", "L", "W", "W", "D"],
        "recent_goals_for": [2, 2, 1, 0, 1, 2, 2, 2],
        "recent_goals_against": [1, 0, 0, 2, 2, 1, 0, 2],
        "style": "pressing",
        "key_players": [("阿莱克西斯-桑切斯", "FW", 80, 37)],
    },
    {
        "name": "厄瓜多尔", "conf": "CONMEBOL", "elo_rating": 1815, "squad_depth": 5,
        "form": 6, "market_value": 150, "formation": "4-4-2",
        "recent_form": ["D", "D", "W", "D", "W", "W", "L", "W"],
        "recent_goals_for": [0, 2, 1, 0, 3, 1, 1, 2],
        "recent_goals_against": [0, 2, 0, 0, 0, 0, 2, 1],
        "style": "counter",
        "key_players": [("恩纳-瓦伦西亚", "FW", 77, 37), ("凯塞多", "MF", 85, 24)],
    },

    # ======== 欧洲 ========
    {
        "name": "英格兰", "conf": "UEFA", "elo_rating": 2000, "squad_depth": 9,
        "form": 8, "market_value": 1400, "formation": "4-3-3",
        "recent_form": ["D", "W", "D", "W", "W", "W", "W", "W"],
        "recent_goals_for": [1, 3, 1, 2, 3, 2, 2, 2],
        "recent_goals_against": [1, 1, 1, 0, 1, 0, 1, 0],
        "style": "direct",
        "key_players": [("贝林厄姆", "MF", 89, 23), ("凯恩", "FW", 90, 32),
                        ("福登", "MF", 88, 26), ("萨卡", "FW", 87, 24)],
    },
    {
        "name": "法国", "conf": "UEFA", "elo_rating": 2030, "squad_depth": 9,
        "form": 8, "market_value": 1550, "formation": "4-3-3",
        "recent_form": ["W", "W", "W", "W", "W", "W", "W", "W"],
        "recent_goals_for": [3, 2, 2, 1, 2, 3, 2, 1],
        "recent_goals_against": [1, 0, 0, 0, 1, 0, 1, 0],
        "style": "counter",
        "key_players": [("姆巴佩", "FW", 92, 27), ("格列兹曼", "MF", 88, 35),
                        ("楚阿梅尼", "MF", 86, 26), ("科纳特", "DF", 84, 27)],
    },
    {
        "name": "西班牙", "conf": "UEFA", "elo_rating": 2020, "squad_depth": 8,
        "form": 8, "market_value": 1300, "formation": "4-3-3",
        "recent_form": ["W", "D", "D", "W", "W", "W", "W", "W"],
        "recent_goals_for": [4, 0, 1, 1, 3, 2, 3, 2],
        "recent_goals_against": [0, 0, 1, 0, 0, 1, 1, 1],
        "style": "possession",
        "key_players": [("罗德里", "MF", 89, 30), ("佩德里", "MF", 89, 23),
                        ("亚马尔", "FW", 86, 18), ("莫拉塔", "FW", 84, 33)],
    },
    {
        "name": "德国", "conf": "UEFA", "elo_rating": 1980, "squad_depth": 8,
        "form": 7, "market_value": 1250, "formation": "4-2-3-1",
        "recent_form": ["W", "L", "D", "W", "W", "W", "W", "W"],
        "recent_goals_for": [2, 1, 2, 2, 3, 1, 2, 4],
        "recent_goals_against": [1, 2, 2, 1, 1, 0, 0, 1],
        "style": "pressing",
        "key_players": [("穆西亚拉", "MF", 88, 23), ("维尔茨", "MF", 86, 22),
                        ("吕迪格", "DF", 85, 33)],
    },
    {
        "name": "荷兰", "conf": "UEFA", "elo_rating": 1930, "squad_depth": 7,
        "form": 7, "market_value": 850, "formation": "4-3-3",
        "recent_form": ["W", "W", "W", "W", "W", "W", "W", "D"],
        "recent_goals_for": [5, 1, 1, 2, 1, 2, 2, 1],
        "recent_goals_against": [1, 0, 0, 1, 0, 0, 1, 1],
        "style": "pressing",
        "key_players": [("德容", "MF", 86, 29), ("范迪克", "DF", 88, 35),
                        ("德里赫特", "DF", 85, 26)],
    },
    {
        "name": "葡萄牙", "conf": "UEFA", "elo_rating": 1955, "squad_depth": 8,
        "form": 8, "market_value": 950, "formation": "4-3-3",
        "recent_form": ["W", "W", "W", "L", "D", "W", "W", "W"],
        "recent_goals_for": [4, 2, 2, 0, 1, 2, 2, 2],
        "recent_goals_against": [1, 0, 1, 1, 1, 1, 1, 0],
        "style": "counter",
        "key_players": [("C罗", "FW", 86, 41), ("贝尔纳多-席尔瓦", "MF", 87, 31),
                        ("布鲁诺-费尔南德斯", "MF", 87, 31)],
    },
    {
        "name": "意大利", "conf": "UEFA", "elo_rating": 1935, "squad_depth": 7,
        "form": 6, "market_value": 850, "formation": "4-3-3",
        "recent_form": ["W", "W", "D", "W", "L", "D", "W", "W"],
        "recent_goals_for": [2, 2, 1, 2, 1, 1, 2, 2],
        "recent_goals_against": [0, 1, 1, 1, 2, 1, 1, 1],
        "style": "possession",
        "key_players": [("巴雷拉", "MF", 86, 29), ("巴斯托尼", "DF", 85, 27),
                        ("若昂-佩德罗", "FW", 79, 34)],
    },
    {
        "name": "比利时", "conf": "UEFA", "elo_rating": 1870, "squad_depth": 6,
        "form": 6, "market_value": 580, "formation": "4-2-3-1",
        "recent_form": ["D", "D", "D", "W", "W", "W", "L", "D"],
        "recent_goals_for": [0, 1, 2, 2, 3, 2, 0, 1],
        "recent_goals_against": [0, 1, 2, 0, 1, 1, 1, 1],
        "style": "counter",
        "key_players": [("德布劳内", "MF", 89, 34), ("卢卡库", "FW", 85, 33)],
    },
    {
        "name": "克罗地亚", "conf": "UEFA", "elo_rating": 1900, "squad_depth": 6,
        "form": 6, "market_value": 450, "formation": "4-3-3",
        "recent_form": ["W", "W", "D", "W", "W", "W", "D", "D"],
        "recent_goals_for": [2, 2, 1, 2, 1, 2, 2, 2],
        "recent_goals_against": [0, 0, 1, 1, 0, 1, 2, 2],
        "style": "possession",
        "key_players": [("莫德里奇", "MF", 85, 40), ("科瓦契奇", "MF", 84, 31)],
    },
    {
        "name": "瑞士", "conf": "UEFA", "elo_rating": 1865, "squad_depth": 6,
        "form": 6, "market_value": 420, "formation": "4-2-3-1",
        "recent_form": ["D", "W", "W", "W", "L", "L", "D", "D"],
        "recent_goals_for": [1, 2, 2, 2, 1, 1, 1, 2],
        "recent_goals_against": [1, 0, 0, 1, 2, 2, 1, 2],
        "style": "pressing",
        "key_players": [("沙奇里", "MF", 80, 34), ("阿坎吉", "DF", 84, 30)],
    },
    {
        "name": "塞尔维亚", "conf": "UEFA", "elo_rating": 1830, "squad_depth": 6,
        "form": 6, "market_value": 380, "formation": "4-4-2",
        "recent_form": ["D", "W", "L", "W", "W", "D", "L", "D"],
        "recent_goals_for": [1, 2, 0, 2, 3, 1, 1, 0],
        "recent_goals_against": [1, 1, 3, 1, 2, 1, 2, 0],
        "style": "direct",
        "key_players": [("弗拉霍维奇", "FW", 85, 26), ("米林科维奇", "MF", 84, 29)],
    },
    {
        "name": "丹麦", "conf": "UEFA", "elo_rating": 1865, "squad_depth": 6,
        "form": 6, "market_value": 450, "formation": "4-3-3",
        "recent_form": ["D", "D", "L", "W", "W", "D", "W", "L"],
        "recent_goals_for": [0, 1, 0, 2, 1, 1, 2, 1],
        "recent_goals_against": [0, 1, 1, 1, 0, 1, 1, 2],
        "style": "pressing",
        "key_players": [("埃里克森", "MF", 83, 34), ("霍伊伦德", "FW", 82, 23)],
    },
    {
        "name": "波兰", "conf": "UEFA", "elo_rating": 1795, "squad_depth": 5,
        "form": 5, "market_value": 280, "formation": "4-4-2",
        "recent_form": ["D", "W", "D", "W", "W", "W", "D", "W"],
        "recent_goals_for": [1, 2, 1, 3, 2, 2, 1, 2],
        "recent_goals_against": [1, 0, 1, 2, 1, 0, 1, 1],
        "style": "counter",
        "key_players": [("莱万多夫斯基", "FW", 86, 37)],
    },
    {
        "name": "瑞典", "conf": "UEFA", "elo_rating": 1805, "squad_depth": 6,
        "form": 6, "market_value": 300, "formation": "4-4-2",
        "recent_form": ["L", "D", "W", "L", "D", "D", "D", "W"],
        "recent_goals_for": [1, 1, 2, 1, 1, 1, 0, 1],
        "recent_goals_against": [5, 1, 2, 2, 1, 1, 0, 0],
        "style": "direct",
        "key_players": [("伊萨克", "FW", 84, 26)],
    },
    {
        "name": "苏格兰", "conf": "UEFA", "elo_rating": 1780, "squad_depth": 5,
        "form": 6, "market_value": 220, "formation": "3-5-2",
        "recent_form": ["D", "W", "L", "L", "D", "D", "D", "D"],
        "recent_goals_for": [2, 2, 0, 0, 0, 2, 1, 0],
        "recent_goals_against": [2, 0, 1, 2, 0, 2, 1, 0],
        "style": "wing_play",
        "key_players": [("麦克托米奈", "MF", 82, 29), ("罗伯逊", "DF", 83, 32)],
    },
    {
        "name": "挪威", "conf": "UEFA", "elo_rating": 1770, "squad_depth": 5,
        "form": 6, "market_value": 350, "formation": "4-4-2",
        "recent_form": ["D", "W", "D", "L", "W", "L", "D", "L"],
        "recent_goals_for": [1, 2, 1, 0, 3, 1, 1, 0],
        "recent_goals_against": [1, 1, 1, 2, 2, 2, 1, 1],
        "style": "direct",
        "key_players": [("哈兰德", "FW", 91, 25), ("厄德高", "MF", 87, 27)],
    },
    {
        "name": "土耳其", "conf": "UEFA", "elo_rating": 1820, "squad_depth": 6,
        "form": 7, "market_value": 380, "formation": "4-2-3-1",
        "recent_form": ["L", "D", "W", "W", "W", "D", "W", "W"],
        "recent_goals_for": [1, 1, 2, 2, 3, 1, 2, 2],
        "recent_goals_against": [2, 1, 1, 0, 1, 1, 1, 1],
        "style": "wing_play",
        "key_players": [("居勒尔", "MF", 83, 21), ("伊尔迪兹", "FW", 82, 20)],
    },
    {
        "name": "威尔士", "conf": "UEFA", "elo_rating": 1700, "squad_depth": 4,
        "form": 5, "market_value": 120, "formation": "3-4-3",
        "recent_form": ["L", "W", "D", "L", "D", "D", "D", "L"],
        "recent_goals_for": [1, 2, 1, 1, 1, 2, 2, 1],
        "recent_goals_against": [2, 1, 1, 2, 1, 2, 2, 2],
        "style": "direct",
        "key_players": [("约翰逊", "FW", 79, 24)],
    },
    {
        "name": "捷克", "conf": "UEFA", "elo_rating": 1760, "squad_depth": 5,
        "form": 5, "market_value": 180, "formation": "4-2-3-1",
        "recent_form": ["W", "L", "D", "L", "D", "L", "L", "L"],
        "recent_goals_for": [2, 0, 1, 1, 2, 1, 0, 0],
        "recent_goals_against": [0, 1, 1, 2, 2, 2, 1, 2],
        "style": "direct",
        "key_players": [("绍切克", "MF", 82, 31)],
    },
    {
        "name": "奥地利", "conf": "UEFA", "elo_rating": 1840, "squad_depth": 6,
        "form": 7, "market_value": 350, "formation": "4-2-3-1",
        "recent_form": ["W", "L", "W", "D", "D", "D", "D", "D"],
        "recent_goals_for": [3, 2, 2, 1, 1, 1, 1, 0],
        "recent_goals_against": [1, 3, 0, 1, 1, 1, 1, 0],
        "style": "wing_play",
        "key_players": [("萨比策", "MF", 83, 32), ("阿瑙托维奇", "FW", 80, 37)],
    },
    {
        "name": "波黑", "conf": "UEFA", "elo_rating": 1680, "squad_depth": 4,
        "form": 4, "market_value": 90, "formation": "3-5-2",
        "recent_form": ["L", "W", "L", "D", "L", "L", "W", "D"],
        "recent_goals_for": [1, 1, 0, 1, 0, 1, 2, 0],
        "recent_goals_against": [2, 0, 2, 1, 2, 2, 0, 0],
        "style": "park_bus",
        "key_players": [("哲科", "FW", 81, 40)],
    },

    # ======== 非洲 ========
    {
        "name": "摩洛哥", "conf": "CAF", "elo_rating": 1880, "squad_depth": 7,
        "form": 7, "market_value": 380, "formation": "4-3-3",
        "recent_form": ["D", "W", "W", "D", "D", "D", "D", "W"],
        "recent_goals_for": [1, 2, 2, 2, 1, 1, 1, 2],
        "recent_goals_against": [1, 1, 1, 2, 1, 1, 1, 1],
        "style": "counter",
        "key_players": [("阿什拉夫", "DF", 86, 27), ("恩内斯里", "FW", 82, 29)],
    },
    {
        "name": "塞内加尔", "conf": "CAF", "elo_rating": 1835, "squad_depth": 6,
        "form": 7, "market_value": 350, "formation": "4-3-3",
        "recent_form": ["D", "W", "D", "W", "D", "L", "D", "W"],
        "recent_goals_for": [1, 1, 0, 1, 1, 0, 1, 1],
        "recent_goals_against": [1, 0, 0, 0, 1, 2, 1, 0],
        "style": "counter",
        "key_players": [("马内", "FW", 85, 34), ("库利巴利", "DF", 83, 33)],
    },
    {
        "name": "尼日利亚", "conf": "CAF", "elo_rating": 1785, "squad_depth": 6,
        "form": 6, "market_value": 300, "formation": "4-3-3",
        "recent_form": ["D", "W", "L", "D", "W", "D", "W", "W"],
        "recent_goals_for": [1, 2, 1, 1, 2, 1, 2, 2],
        "recent_goals_against": [1, 1, 2, 1, 1, 1, 1, 1],
        "style": "direct",
        "key_players": [("奥斯梅恩", "FW", 86, 27), ("恩迪迪", "MF", 82, 29)],
    },
    {
        "name": "埃及", "conf": "CAF", "elo_rating": 1790, "squad_depth": 5,
        "form": 6, "market_value": 220, "formation": "4-3-3",
        "recent_form": ["W", "W", "D", "D", "W", "D", "W", "L"],
        "recent_goals_for": [3, 1, 1, 1, 2, 1, 2, 0],
        "recent_goals_against": [2, 1, 1, 1, 1, 1, 1, 2],
        "style": "counter",
        "key_players": [("萨拉赫", "FW", 88, 34)],
    },
    {
        "name": "科特迪瓦", "conf": "CAF", "elo_rating": 1780, "squad_depth": 6,
        "form": 6, "market_value": 250, "formation": "4-3-3",
        "recent_form": ["L", "L", "D", "W", "D", "D", "D", "L"],
        "recent_goals_for": [1, 1, 2, 2, 1, 2, 2, 0],
        "recent_goals_against": [2, 2, 2, 0, 1, 2, 2, 1],
        "style": "direct",
        "key_players": [("凯西", "MF", 83, 29)],
    },
    {
        "name": "南非", "conf": "CAF", "elo_rating": 1650, "squad_depth": 4,
        "form": 5, "market_value": 60, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "D", "L", "W"],
        "recent_goals_for": [1, 1, 1, 0, 1, 2, 1, 2],
        "recent_goals_against": [2, 2, 2, 2, 2, 2, 2, 0],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "阿尔及利亚", "conf": "CAF", "elo_rating": 1750, "squad_depth": 5,
        "form": 5, "market_value": 150, "formation": "4-3-3",
        "recent_form": ["W", "W", "W", "L", "L", "L", "W", "L"],
        "recent_goals_for": [3, 2, 2, 0, 0, 1, 1, 1],
        "recent_goals_against": [2, 1, 1, 1, 1, 2, 0, 2],
        "style": "counter",
        "key_players": [("马赫雷斯", "FW", 83, 35)],
    },
    {
        "name": "突尼斯", "conf": "CAF", "elo_rating": 1740, "squad_depth": 5,
        "form": 5, "market_value": 120, "formation": "4-3-3",
        "recent_form": ["L", "W", "L", "D", "D", "D", "W", "D"],
        "recent_goals_for": [0, 1, 1, 2, 1, 1, 3, 1],
        "recent_goals_against": [4, 2, 2, 2, 1, 1, 2, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "加纳", "conf": "CAF", "elo_rating": 1720, "squad_depth": 5,
        "form": 5, "market_value": 180, "formation": "4-3-3",
        "recent_form": ["L", "D", "D", "L", "D", "W", "D", "W"],
        "recent_goals_for": [1, 2, 1, 1, 1, 2, 1, 2],
        "recent_goals_against": [2, 2, 1, 2, 1, 1, 1, 1],
        "style": "direct",
        "key_players": [("库杜斯", "MF", 83, 25)],
    },
    {
        "name": "喀麦隆", "conf": "CAF", "elo_rating": 1710, "squad_depth": 5,
        "form": 5, "market_value": 160, "formation": "4-3-3",
        "recent_form": ["W", "L", "W", "W", "L", "W", "W", "W"],
        "recent_goals_for": [1, 0, 2, 3, 0, 2, 2, 2],
        "recent_goals_against": [0, 2, 1, 2, 1, 1, 1, 1],
        "style": "direct",
        "key_players": [("姆贝乌莫", "FW", 82, 26)],
    },
    {
        "name": "马里", "conf": "CAF", "elo_rating": 1690, "squad_depth": 4,
        "form": 5, "market_value": 100, "formation": "4-3-3",
        "recent_form": ["L", "D", "L", "D", "L", "W", "D", "D"],
        "recent_goals_for": [0, 1, 0, 1, 0, 2, 1, 1],
        "recent_goals_against": [1, 1, 1, 1, 1, 0, 1, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "布基纳法索", "conf": "CAF", "elo_rating": 1640, "squad_depth": 4,
        "form": 4, "market_value": 50, "formation": "4-4-2",
        "recent_form": ["D", "L", "L", "W", "D", "L", "W", "L"],
        "recent_goals_for": [1, 0, 1, 2, 1, 0, 1, 1],
        "recent_goals_against": [1, 1, 2, 1, 1, 1, 0, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "几内亚", "conf": "CAF", "elo_rating": 1620, "squad_depth": 3,
        "form": 4, "market_value": 40, "formation": "4-4-2",
        "recent_form": ["L", "W", "D", "W", "D", "D", "W", "L"],
        "recent_goals_for": [0, 2, 1, 1, 1, 1, 1, 0],
        "recent_goals_against": [2, 1, 1, 0, 1, 1, 0, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "赞比亚", "conf": "CAF", "elo_rating": 1560, "squad_depth": 3,
        "form": 4, "market_value": 30, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 0, 0, 0, 0, 0, 0, 1],
        "recent_goals_against": [1, 2, 1, 4, 2, 3, 1, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "津巴布韦", "conf": "CAF", "elo_rating": 1530, "squad_depth": 3,
        "form": 4, "market_value": 20, "formation": "4-4-2",
        "recent_form": ["D", "L", "L", "W", "L", "D", "L", "L"],
        "recent_goals_for": [1, 1, 0, 1, 1, 1, 0, 0],
        "recent_goals_against": [1, 2, 1, 0, 2, 1, 3, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "安哥拉", "conf": "CAF", "elo_rating": 1600, "squad_depth": 3,
        "form": 4, "market_value": 30, "formation": "4-4-2",
        "recent_form": ["D", "L", "D", "D", "D", "L", "L", "L"],
        "recent_goals_for": [1, 1, 1, 1, 1, 1, 1, 0],
        "recent_goals_against": [1, 2, 1, 1, 1, 3, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "莫桑比克", "conf": "CAF", "elo_rating": 1480, "squad_depth": 3,
        "form": 3, "market_value": 15, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "D", "L"],
        "recent_goals_for": [0, 1, 0, 1, 0, 1, 0, 1],
        "recent_goals_against": [2, 2, 3, 2, 2, 4, 0, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "马达加斯加", "conf": "CAF", "elo_rating": 1500, "squad_depth": 3,
        "form": 3, "market_value": 15, "formation": "4-4-2",
        "recent_form": ["D", "L", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [1, 0, 1, 0, 1, 1, 1, 0],
        "recent_goals_against": [1, 2, 3, 3, 2, 2, 2, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "多哥", "conf": "CAF", "elo_rating": 1460, "squad_depth": 2,
        "form": 3, "market_value": 10, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 0, 1, 1, 2, 1, 1, 1],
        "recent_goals_against": [2, 3, 1, 2, 3, 3, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "贝宁", "conf": "CAF", "elo_rating": 1470, "squad_depth": 2,
        "form": 3, "market_value": 10, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [1, 1, 1, 1, 0, 0, 0, 0],
        "recent_goals_against": [2, 2, 2, 2, 3, 3, 3, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "利比亚", "conf": "CAF", "elo_rating": 1510, "squad_depth": 3,
        "form": 3, "market_value": 15, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 1, 1, 1, 1, 0, 0, 0],
        "recent_goals_against": [2, 3, 2, 2, 3, 1, 4, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "苏丹", "conf": "CAF", "elo_rating": 1430, "squad_depth": 2,
        "form": 3, "market_value": 8, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "L", "W"],
        "recent_goals_for": [0, 0, 0, 0, 1, 1, 0, 2],
        "recent_goals_against": [4, 1, 2, 3, 2, 2, 1, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "赤道几内亚", "conf": "CAF", "elo_rating": 1490, "squad_depth": 3,
        "form": 3, "market_value": 12, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "L", "L", "D", "D", "L"],
        "recent_goals_for": [0, 1, 1, 0, 0, 2, 1, 1],
        "recent_goals_against": [1, 1, 2, 3, 1, 2, 1, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "科摩罗", "conf": "CAF", "elo_rating": 1410, "squad_depth": 2,
        "form": 3, "market_value": 5, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "L", "L", "L", "W", "W"],
        "recent_goals_for": [1, 1, 0, 0, 0, 0, 1, 2],
        "recent_goals_against": [3, 4, 0, 3, 2, 2, 0, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "莱索托", "conf": "CAF", "elo_rating": 1360, "squad_depth": 2,
        "form": 2, "market_value": 3, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 0, 1, 1, 0, 0, 0, 0],
        "recent_goals_against": [1, 0, 2, 2, 1, 2, 3, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "斯威士兰", "conf": "CAF", "elo_rating": 1340, "squad_depth": 2,
        "form": 2, "market_value": 3, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "D", "L", "L", "L", "L"],
        "recent_goals_for": [1, 0, 0, 1, 1, 1, 1, 0],
        "recent_goals_against": [2, 2, 2, 1, 2, 2, 4, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "博茨瓦纳", "conf": "CAF", "elo_rating": 1400, "squad_depth": 2,
        "form": 3, "market_value": 5, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [1, 1, 0, 0, 0, 1, 0, 1],
        "recent_goals_against": [2, 1, 1, 3, 2, 4, 3, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "纳米比亚", "conf": "CAF", "elo_rating": 1390, "squad_depth": 2,
        "form": 3, "market_value": 5, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 0, 0, 1, 0, 0, 0, 0],
        "recent_goals_against": [2, 1, 3, 4, 3, 2, 4, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "中非共和国", "conf": "CAF", "elo_rating": 1380, "squad_depth": 2,
        "form": 2, "market_value": 4, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 1, 1, 1, 0, 1, 0, 1],
        "recent_goals_against": [1, 2, 1, 2, 2, 2, 1, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "乍得", "conf": "CAF", "elo_rating": 1350, "squad_depth": 2,
        "form": 2, "market_value": 3, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "D", "L", "L", "L", "L"],
        "recent_goals_for": [1, 0, 1, 1, 1, 1, 1, 1],
        "recent_goals_against": [2, 3, 1, 1, 3, 2, 3, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "吉布提", "conf": "CAF", "elo_rating": 1300, "squad_depth": 1,
        "form": 2, "market_value": 2, "formation": "4-4-2",
        "recent_form": ["L", "W", "L", "D", "L", "L", "L", "L"],
        "recent_goals_for": [0, 2, 0, 1, 1, 0, 0, 1],
        "recent_goals_against": [2, 1, 3, 1, 2, 3, 3, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "索马里", "conf": "CAF", "elo_rating": 1280, "squad_depth": 1,
        "form": 2, "market_value": 2, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "W", "L", "L", "D", "D"],
        "recent_goals_for": [0, 1, 0, 1, 0, 0, 1, 1],
        "recent_goals_against": [2, 1, 2, 0, 2, 1, 1, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "厄立特里亚", "conf": "CAF", "elo_rating": 1290, "squad_depth": 1,
        "form": 2, "market_value": 2, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "W", "L", "L", "L", "L"],
        "recent_goals_for": [1, 1, 1, 1, 0, 1, 0, 0],
        "recent_goals_against": [2, 2, 3, 0, 1, 3, 4, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "南苏丹", "conf": "CAF", "elo_rating": 1330, "squad_depth": 2,
        "form": 2, "market_value": 3, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "W", "L", "L"],
        "recent_goals_for": [0, 1, 1, 1, 1, 1, 0, 1],
        "recent_goals_against": [3, 2, 2, 2, 2, 0, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "佛得角", "conf": "CAF", "elo_rating": 1630, "squad_depth": 4,
        "form": 5, "market_value": 35, "formation": "4-3-3",
        "recent_form": ["D", "D", "L", "D", "L", "D", "L", "L"],
        "recent_goals_for": [0, 2, 1, 1, 1, 0, 0, 0],
        "recent_goals_against": [0, 2, 3, 1, 1, 3, 0, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "几内亚比绍", "conf": "CAF", "elo_rating": 1440, "squad_depth": 2,
        "form": 3, "market_value": 6, "formation": "4-4-2",
        "recent_form": ["D", "L", "L", "L", "L", "L", "D", "L"],
        "recent_goals_for": [1, 0, 0, 0, 0, 1, 1, 0],
        "recent_goals_against": [1, 2, 2, 2, 2, 2, 1, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "圣多美和普林西比", "conf": "CAF", "elo_rating": 1230, "squad_depth": 1,
        "form": 2, "market_value": 1, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "L", "D"],
        "recent_goals_for": [1, 0, 1, 1, 1, 0, 0, 1],
        "recent_goals_against": [2, 1, 2, 3, 2, 2, 1, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "塞舌尔", "conf": "CAF", "elo_rating": 1260, "squad_depth": 1,
        "form": 2, "market_value": 1, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "W", "L", "L", "L", "L"],
        "recent_goals_for": [0, 0, 1, 1, 1, 1, 1, 0],
        "recent_goals_against": [1, 1, 1, 0, 2, 2, 4, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "毛里求斯", "conf": "CAF", "elo_rating": 1370, "squad_depth": 2,
        "form": 3, "market_value": 4, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "D", "L", "L", "L"],
        "recent_goals_for": [1, 0, 0, 1, 1, 0, 1, 1],
        "recent_goals_against": [3, 1, 2, 3, 1, 1, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "毛里塔尼亚", "conf": "CAF", "elo_rating": 1520, "squad_depth": 3,
        "form": 3, "market_value": 15, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "D", "L", "D", "L", "W"],
        "recent_goals_for": [0, 0, 1, 1, 0, 1, 0, 1],
        "recent_goals_against": [2, 1, 3, 1, 1, 1, 1, 0],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "冈比亚", "conf": "CAF", "elo_rating": 1540, "squad_depth": 3,
        "form": 4, "market_value": 20, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 2, 1, 1, 0, 0, 1, 0],
        "recent_goals_against": [1, 2, 3, 2, 1, 1, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "塞拉利昂", "conf": "CAF", "elo_rating": 1450, "squad_depth": 2,
        "form": 3, "market_value": 6, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "W", "D", "D", "D", "L"],
        "recent_goals_for": [0, 0, 0, 1, 1, 1, 1, 1],
        "recent_goals_against": [2, 1, 2, 0, 1, 1, 1, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "利比里亚", "conf": "CAF", "elo_rating": 1420, "squad_depth": 2,
        "form": 3, "market_value": 5, "formation": "4-4-2",
        "recent_form": ["L", "W", "L", "L", "L", "L", "L", "D"],
        "recent_goals_for": [1, 1, 0, 0, 0, 0, 1, 1],
        "recent_goals_against": [3, 0, 2, 2, 3, 1, 2, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "尼日尔", "conf": "CAF", "elo_rating": 1400, "squad_depth": 2,
        "form": 3, "market_value": 4, "formation": "4-4-2",
        "recent_form": ["L", "W", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 2, 0, 1, 0, 0, 1, 1],
        "recent_goals_against": [3, 1, 1, 2, 2, 2, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "布隆迪", "conf": "CAF", "elo_rating": 1460, "squad_depth": 2,
        "form": 3, "market_value": 5, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "W", "L", "L", "D"],
        "recent_goals_for": [0, 0, 0, 1, 1, 0, 0, 0],
        "recent_goals_against": [2, 1, 2, 2, 0, 1, 2, 0],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "卢旺达", "conf": "CAF", "elo_rating": 1480, "squad_depth": 2,
        "form": 3, "market_value": 6, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "D", "L", "D", "L", "L"],
        "recent_goals_for": [1, 0, 2, 0, 0, 1, 0, 1],
        "recent_goals_against": [2, 2, 2, 0, 4, 1, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "乌干达", "conf": "CAF", "elo_rating": 1500, "squad_depth": 3,
        "form": 3, "market_value": 8, "formation": "4-4-2",
        "recent_form": ["D", "L", "L", "L", "L", "D", "L", "L"],
        "recent_goals_for": [1, 1, 1, 1, 0, 1, 1, 1],
        "recent_goals_against": [1, 2, 3, 2, 2, 1, 2, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "坦桑尼亚", "conf": "CAF", "elo_rating": 1490, "squad_depth": 2,
        "form": 3, "market_value": 6, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "D", "L", "D", "L"],
        "recent_goals_for": [1, 0, 0, 0, 1, 1, 1, 1],
        "recent_goals_against": [3, 2, 2, 2, 1, 2, 1, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "肯尼亚", "conf": "CAF", "elo_rating": 1510, "squad_depth": 3,
        "form": 3, "market_value": 8, "formation": "4-4-2",
        "recent_form": ["D", "D", "D", "L", "L", "L", "L", "L"],
        "recent_goals_for": [1, 1, 0, 1, 1, 0, 0, 0],
        "recent_goals_against": [1, 1, 0, 2, 2, 1, 1, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "埃塞俄比亚", "conf": "CAF", "elo_rating": 1470, "squad_depth": 2,
        "form": 3, "market_value": 5, "formation": "4-4-2",
        "recent_form": ["D", "D", "L", "D", "L", "L", "L", "L"],
        "recent_goals_for": [1, 1, 0, 1, 1, 0, 1, 1],
        "recent_goals_against": [1, 1, 4, 1, 2, 3, 3, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "马拉维", "conf": "CAF", "elo_rating": 1440, "squad_depth": 2,
        "form": 3, "market_value": 5, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "D", "L", "L", "L"],
        "recent_goals_for": [0, 0, 1, 0, 1, 0, 0, 1],
        "recent_goals_against": [2, 3, 2, 4, 1, 3, 1, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "刚果(金)", "conf": "CAF", "elo_rating": 1670, "squad_depth": 4,
        "form": 5, "market_value": 80, "formation": "4-3-3",
        "recent_form": ["D", "D", "D", "D", "L", "L", "D", "W"],
        "recent_goals_for": [1, 1, 2, 1, 0, 0, 1, 2],
        "recent_goals_against": [1, 1, 2, 1, 1, 3, 1, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "刚果(布)", "conf": "CAF", "elo_rating": 1550, "squad_depth": 3,
        "form": 4, "market_value": 20, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "L", "D", "L"],
        "recent_goals_for": [1, 1, 1, 1, 0, 0, 1, 2],
        "recent_goals_against": [2, 4, 3, 2, 3, 3, 1, 4],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "加蓬", "conf": "CAF", "elo_rating": 1600, "squad_depth": 3,
        "form": 4, "market_value": 25, "formation": "4-4-2",
        "recent_form": ["L", "D", "D", "L", "L", "D", "D", "L"],
        "recent_goals_for": [1, 2, 1, 0, 1, 1, 2, 0],
        "recent_goals_against": [2, 2, 1, 1, 2, 1, 2, 1],
        "style": "park_bus",
        "key_players": [],
    },

    # ======== 亚洲 ========
    {
        "name": "日本", "conf": "AFC", "elo_rating": 1900, "squad_depth": 7,
        "form": 7, "market_value": 380, "formation": "4-3-3",
        "recent_form": ["W", "L", "W", "W", "W", "D", "W", "W"],
        "recent_goals_for": [4, 1, 1, 2, 2, 2, 2, 1],
        "recent_goals_against": [0, 2, 0, 0, 1, 2, 1, 1],
        "style": "possession",
        "key_players": [("三笘薫", "MF", 84, 28), ("久保建英", "MF", 82, 24),
                        ("镰田大地", "MF", 81, 29)],
    },
    {
        "name": "韩国", "conf": "AFC", "elo_rating": 1830, "squad_depth": 6,
        "form": 7, "market_value": 320, "formation": "4-3-3",
        "recent_form": ["W", "L", "L", "W", "L", "W", "W", "W"],
        "recent_goals_for": [2, 0, 1, 2, 1, 2, 2, 2],
        "recent_goals_against": [1, 2, 2, 1, 2, 1, 1, 1],
        "style": "counter",
        "key_players": [("孙兴慜", "FW", 87, 34), ("金玟哉", "DF", 83, 29)],
    },
    {
        "name": "澳大利亚", "conf": "AFC", "elo_rating": 1740, "squad_depth": 5,
        "form": 6, "market_value": 120, "formation": "4-4-2",
        "recent_form": ["D", "L", "W", "D", "W", "W", "L", "L"],
        "recent_goals_for": [1, 0, 3, 2, 1, 1, 1, 0],
        "recent_goals_against": [1, 1, 1, 2, 0, 0, 2, 2],
        "style": "direct",
        "key_players": [("莫伊", "MF", 77, 35)],
    },
    {
        "name": "沙特阿拉伯", "conf": "AFC", "elo_rating": 1720, "squad_depth": 4,
        "form": 5, "market_value": 90, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "W", "W", "L", "D", "D"],
        "recent_goals_for": [0, 2, 1, 2, 3, 0, 0, 1],
        "recent_goals_against": [4, 2, 2, 1, 1, 1, 0, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "伊朗", "conf": "AFC", "elo_rating": 1745, "squad_depth": 5,
        "form": 5, "market_value": 80, "formation": "4-4-2",
        "recent_form": ["D", "D", "L", "W", "L", "D", "W", "D"],
        "recent_goals_for": [0, 2, 1, 2, 0, 2, 1, 2],
        "recent_goals_against": [0, 2, 2, 1, 2, 2, 0, 1],
        "style": "park_bus",
        "key_players": [("阿兹蒙", "FW", 78, 31)],
    },
    {
        "name": "乌兹别克斯坦", "conf": "AFC", "elo_rating": 1660, "squad_depth": 4,
        "form": 5, "market_value": 50, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "D", "L", "D", "L", "L"],
        "recent_goals_for": [0, 1, 1, 2, 0, 1, 0, 0],
        "recent_goals_against": [1, 3, 1, 2, 2, 1, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "卡塔尔", "conf": "AFC", "elo_rating": 1680, "squad_depth": 4,
        "form": 5, "market_value": 70, "formation": "4-3-3",
        "recent_form": ["W", "L", "W", "D", "L", "W", "L", "L"],
        "recent_goals_for": [2, 1, 1, 1, 1, 2, 1, 1],
        "recent_goals_against": [1, 2, 0, 1, 2, 1, 3, 3],
        "style": "counter",
        "key_players": [("阿菲夫", "FW", 80, 29)],
    },
    {
        "name": "约旦", "conf": "AFC", "elo_rating": 1650, "squad_depth": 4,
        "form": 5, "market_value": 40, "formation": "4-4-2",
        "recent_form": ["L", "L", "D", "L", "L", "W", "W", "L"],
        "recent_goals_for": [1, 1, 2, 1, 0, 2, 2, 0],
        "recent_goals_against": [2, 2, 2, 2, 1, 0, 0, 3],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "伊拉克", "conf": "AFC", "elo_rating": 1640, "squad_depth": 4,
        "form": 5, "market_value": 45, "formation": "4-4-2",
        "recent_form": ["L", "L", "L", "L", "L", "D", "L", "L"],
        "recent_goals_for": [1, 1, 0, 1, 1, 1, 1, 1],
        "recent_goals_against": [2, 2, 1, 2, 2, 1, 2, 3],
        "style": "park_bus",
        "key_players": [],
    },

    # ======== 大洋洲 ========
    {
        "name": "新西兰", "conf": "OFC", "elo_rating": 1575, "squad_depth": 3,
        "form": 4, "market_value": 30, "formation": "4-4-2",
        "recent_form": ["L", "D", "L", "L", "D", "L", "L", "L"],
        "recent_goals_for": [2, 2, 0, 0, 0, 1, 1, 0],
        "recent_goals_against": [3, 2, 3, 1, 0, 3, 3, 3],
        "style": "park_bus",
        "key_players": [("克里斯-伍德", "FW", 75, 34)],
    },
    {
        "name": "库拉索", "conf": "CONCACAF", "elo_rating": 1560, "squad_depth": 3,
        "form": 4, "market_value": 20, "formation": "4-4-2",
        "recent_form": ["D", "D", "L", "L", "L", "L", "L", "L"],
        "recent_goals_for": [0, 1, 0, 0, 1, 0, 1, 0],
        "recent_goals_against": [0, 1, 1, 2, 2, 3, 3, 1],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "海地", "conf": "CONCACAF", "elo_rating": 1600, "squad_depth": 3,
        "form": 4, "market_value": 25, "formation": "4-4-2",
        "recent_form": ["D", "L", "L", "D", "L", "L", "L", "L"],
        "recent_goals_for": [1, 1, 0, 1, 1, 0, 0, 1],
        "recent_goals_against": [1, 2, 2, 1, 2, 2, 2, 2],
        "style": "park_bus",
        "key_players": [],
    },
    {
        "name": "巴拉圭", "conf": "CONMEBOL", "elo_rating": 1760, "squad_depth": 5,
        "form": 5, "market_value": 200, "formation": "4-4-2",
        "recent_form": ["W", "D", "W", "W", "W", "D", "W", "L"],
        "recent_goals_for": [1, 2, 2, 2, 1, 1, 2, 1],
        "recent_goals_against": [0, 2, 0, 1, 0, 1, 1, 2],
        "style": "counter",
        "key_players": [],
    },
]

# ---------------------------------------------------------------------------
# 便捷构造
# ---------------------------------------------------------------------------
def build_team(raw: Dict[str, object]) -> Team:
    """根据原始字典构造 Team 实例。"""
    name = str(raw["name"])
    team = Team(
        name=name,
        country=str(raw.get("conf", "")),
        elo_rating=float(raw["elo_rating"]),
        squad_depth=float(raw["squad_depth"]),
        form=float(raw["form"]),
        market_value=float(raw["market_value"]),
        formation=str(raw["formation"]),
        style=str(raw.get("style", "")),
    )
    for p_info in raw.get("key_players", []):
        if len(p_info) >= 4:
            pname, pos, rating, age = p_info[:4]
            team.add_player(Player(name=pname, position=pos,
                                   rating=float(rating), age=int(age)))
    if "style" in raw:
        team.style = str(raw["style"])
    # 读取近期比赛数据（用于动量引擎）
    team.recent_form = list(raw.get("recent_form", []))
    team.recent_goals_for = list(raw.get("recent_goals_for", []))
    team.recent_goals_against = list(raw.get("recent_goals_against", []))
    return team


# 预先构造好的 Team 字典（按名称索引）
TEAMS: Dict[str, Team] = {t["name"]: build_team(t) for t in TEAM_RAW}

# 球队名称别名映射（赛程简称 -> 数据全称）
TEAM_ALIASES: Dict[str, str] = {
    "沙特": "沙特阿拉伯",
    "美国": "美国",
    "英国": "英格兰",
    "刚果": "刚果(金)",
}

# 将别名也注册进 TEAMS 字典，使简称同样可以索引到 Team 对象
for _alias, _full_name in TEAM_ALIASES.items():
    if _full_name in TEAMS and _alias not in TEAMS:
        TEAMS[_alias] = TEAMS[_full_name]


# ---------------------------------------------------------------------------
# 小组赛分组（示意：A-H 组，每组 4 队）
# ---------------------------------------------------------------------------
GROUPS: Dict[str, List[str]] = {
    "A": ["美国", "墨西哥", "加拿大", "哥斯达黎加"],
    "B": ["阿根廷", "乌拉圭", "智利", "厄瓜多尔"],
    "C": ["巴西", "哥伦比亚", "秘鲁" if "秘鲁" in TEAMS else "厄瓜多尔", "巴拉圭" if "巴拉圭" in TEAMS else "智利"],
    "D": ["英格兰", "法国", "葡萄牙", "比利时"],
    "E": ["西班牙", "德国", "荷兰", "意大利"],
    "F": ["克罗地亚", "丹麦", "瑞士", "塞尔维亚"],
    "G": ["摩洛哥", "塞内加尔", "尼日利亚", "埃及"],
    "H": ["日本", "韩国", "澳大利亚", "沙特阿拉伯"],
}

# 为确保所有球队都存在，这里把 C 组的未注册队名替换为已注册队名
GROUPS["C"] = ["巴西", "哥伦比亚", "厄瓜多尔", "智利"]

# 每个小组的轮次赛果（截至 2026-06-21 的参考赛果，这里是示例，
# 实际预测时请以真实数据更新）
GROUP_STAGE_SCORES: Dict[str, List[Tuple[str, int, int, str]]] = {
    # key: group -> [(hometeam, hg, ag, awayteam), ...]
    "A": [("美国", 2, 1, "墨西哥"), ("加拿大", 1, 0, "哥斯达黎加")],
    "B": [("阿根廷", 3, 0, "智利"), ("乌拉圭", 1, 1, "厄瓜多尔")],
    "C": [("巴西", 2, 0, "厄瓜多尔"), ("哥伦比亚", 1, 0, "智利")],
    "D": [("英格兰", 2, 2, "法国"), ("葡萄牙", 1, 0, "比利时")],
    "E": [("西班牙", 1, 0, "意大利"), ("德国", 1, 2, "荷兰")],
    "F": [("克罗地亚", 2, 1, "丹麦"), ("瑞士", 1, 1, "塞尔维亚")],
    "G": [("摩洛哥", 2, 0, "埃及"), ("塞内加尔", 2, 1, "尼日利亚")],
    "H": [("日本", 1, 0, "韩国"), ("澳大利亚", 2, 0, "沙特阿拉伯")],
}

# 完整小组赛（每队与其它三队各打一场）
GROUP_STAGE: Dict[str, List[Tuple[str, str]]] = {
    g: [
        (teams[0], teams[1]), (teams[2], teams[3]),
        (teams[0], teams[2]), (teams[1], teams[3]),
        (teams[0], teams[3]), (teams[1], teams[2]),
    ]
    for g, teams in GROUPS.items()
}


# ---------------------------------------------------------------------------
# 淘汰赛阶段（模板）
# ---------------------------------------------------------------------------
KNOCKOUT: Dict[str, List[str]] = {
    "1/8决赛": [
        "A组第一 vs B组第二", "C组第一 vs D组第二",
        "E组第一 vs F组第二", "G组第一 vs H组第二",
        "B组第一 vs A组第二", "D组第一 vs C组第二",
        "F组第一 vs E组第二", "H组第一 vs G组第二",
    ],
    "1/4决赛": [
        "胜者1 vs 胜者2", "胜者3 vs 胜者4",
        "胜者5 vs 胜者6", "胜者7 vs 胜者8",
    ],
    "半决赛": ["胜者A vs 胜者B", "胜者C vs 胜者D"],
    "决赛": ["胜者E vs 胜者F"],
}


# ---------------------------------------------------------------------------
# 构造完整 Tournament 对象
# ---------------------------------------------------------------------------
def get_tournament(apply_sample_results: bool = True) -> Tournament:
    """返回一个内置数据的 2026 世界杯赛事结构。

    Args:
        apply_sample_results: 是否将 GROUP_STAGE_SCORES 中的示例赛果
                              写入 match.result，并更新球队状态。
    """
    t = Tournament(name="FIFA World Cup 2026", host="加拿大/美国/墨西哥")

    # 1) 添加分组
    for g_name, team_names in GROUPS.items():
        teams = [TEAMS[n] for n in team_names]
        t.add_group(g_name, teams)

        # 2) 添加比赛
        group = t.groups[g_name]
        for ht, at in GROUP_STAGE[g_name]:
            from football_predictor.models.match import Match  # 内部导入避免循环
            match = Match(TEAMS[ht], TEAMS[at], competition="World Cup 2026",
                         stage=f"小组赛 {g_name}", neutral=True)
            group.add_match(match)

        # 3) 应用示例赛果
        if apply_sample_results and g_name in GROUP_STAGE_SCORES:
            for ht, hg, ag, at in GROUP_STAGE_SCORES[g_name]:
                # 找到对应的比赛并设置结果
                for m in group.matches:
                    if m.home.name == ht and m.away.name == at:
                        m.set_result(hg, ag)
                        break

    # 4) 添加淘汰赛（以名称形式存放）
    for stage, matchups in KNOCKOUT.items():
        rnd = t.add_knockout_round(stage)

    return t
