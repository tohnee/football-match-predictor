#!/usr/bin/env python3
"""
daily_predictor.py - 每日比赛预测脚本
=====================================

用于定时任务（cron）自动预测"今天夜晚、次日凌晨、次日上午"的
2026世界杯比赛。

时区处理:
    - 比赛时间以竞彩官方/实际开赛时间为准（北京时间）
    - 直接按北京时间输出，无需时区转换
    - 6月21日-7月19日世界杯期间，比赛多在北京时间凌晨到上午进行

使用方式:
    python daily_predictor.py [--date YYYY-MM-DD]

输出:
    打印预测报告到 stdout，可重定向到文件或邮件
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, date, timedelta, timezone
from typing import List, Tuple, Optional

from football_predictor.models.match import Match
from football_predictor.models.team import Team
from football_predictor.analysis.rating_engine import RatingEngine
from football_predictor.analysis.momentum_engine import MomentumEngine
from football_predictor.analysis.tactical_engine import TacticalEngine
from football_predictor.analysis.prediction_engine import PredictionEngine
from football_predictor.data.world_cup_2026 import TEAMS, TEAM_ALIASES, get_tournament


# ---------------------------------------------------------------------------
# 2026世界杯实际赛程（北京时间，来源：竞彩官方/实际开赛时间）
# ---------------------------------------------------------------------------
# 格式: (日期, 北京时间, 主队, 客队, 球场, 城市)
WORLD_CUP_SCHEDULE_BEIJING: List[Tuple[str, str, str, str, str, str]] = [
    # === 6月11日 ===
    ("2026-06-11", "20:00", "墨西哥", "南非", "Mexico City Stadium", "墨西哥城"),
    ("2026-06-11", "23:00", "韩国", "捷克", "Guadalajara Stadium", "瓜达拉哈拉"),

    # === 6月12日 ===
    ("2026-06-12", "02:00", "加拿大", "波黑", "Toronto Stadium", "多伦多"),
    ("2026-06-12", "05:00", "美国", "巴拉圭", "Los Angeles Stadium", "洛杉矶"),

    # === 6月13日 ===
    ("2026-06-13", "02:00", "海地", "苏格兰", "Boston Stadium", "波士顿"),
    ("2026-06-13", "05:00", "澳大利亚", "土耳其", "BC Place Vancouver", "温哥华"),
    ("2026-06-13", "08:00", "巴西", "摩洛哥", "New York New Jersey Stadium", "纽约/新泽西"),
    ("2026-06-13", "11:00", "卡塔尔", "瑞士", "San Francisco Bay Area Stadium", "旧金山湾区"),

    # === 6月14日 ===
    ("2026-06-14", "02:00", "科特迪瓦", "厄瓜多尔", "Philadelphia Stadium", "费城"),
    ("2026-06-14", "05:00", "德国", "库拉索", "Houston Stadium", "休斯顿"),
    ("2026-06-14", "08:00", "荷兰", "日本", "Dallas Stadium", "达拉斯"),
    ("2026-06-14", "11:00", "瑞典", "突尼斯", "Estadio Monterrey", "蒙特雷"),

    # === 6月15日 ===
    ("2026-06-15", "02:00", "伊朗", "新西兰", "Los Angeles Stadium", "洛杉矶"),
    ("2026-06-15", "05:00", "比利时", "埃及", "Seattle Stadium", "西雅图"),
    ("2026-06-15", "08:00", "沙特", "乌拉圭", "Miami Stadium", "迈阿密"),
    ("2026-06-15", "11:00", "西班牙", "佛得角", "Atlanta Stadium", "亚特兰大"),

    # === 6月16日 ===
    ("2026-06-16", "02:00", "法国", "塞内加尔", "New York New Jersey Stadium", "纽约/新泽西"),
    ("2026-06-16", "05:00", "伊拉克", "挪威", "Boston Stadium", "波士顿"),
    ("2026-06-16", "08:00", "阿根廷", "阿尔及利亚", "Kansas City Stadium", "堪萨斯城"),
    ("2026-06-16", "11:00", "奥地利", "约旦", "San Francisco Bay Area Stadium", "旧金山湾区"),

    # === 6月17日 ===
    ("2026-06-17", "02:00", "葡萄牙", "刚果(金)", "Houston Stadium", "休斯顿"),
    ("2026-06-17", "05:00", "乌兹别克斯坦", "哥伦比亚", "Mexico City Stadium", "墨西哥城"),
    ("2026-06-17", "08:00", "加纳", "巴拿马", "Toronto Stadium", "多伦多"),
    ("2026-06-17", "11:00", "英格兰", "克罗地亚", "Dallas Stadium", "达拉斯"),

    # === 6月18日 ===
    ("2026-06-18", "02:00", "捷克", "南非", "Atlanta Stadium", "亚特兰大"),
    ("2026-06-18", "05:00", "瑞士", "波黑", "Los Angeles Stadium", "洛杉矶"),
    ("2026-06-18", "08:00", "加拿大", "卡塔尔", "BC Place Vancouver", "温哥华"),
    ("2026-06-18", "11:00", "墨西哥", "韩国", "Guadalajara Stadium", "瓜达拉哈拉"),

    # === 6月19日 ===
    ("2026-06-19", "02:00", "巴西", "海地", "Philadelphia Stadium", "费城"),
    ("2026-06-19", "05:00", "苏格兰", "摩洛哥", "Boston Stadium", "波士顿"),
    ("2026-06-19", "08:00", "土耳其", "巴拉圭", "San Francisco Bay Area Stadium", "旧金山湾区"),
    ("2026-06-19", "11:00", "美国", "澳大利亚", "Seattle Stadium", "西雅图"),

    # === 6月20日 ===
    ("2026-06-20", "02:00", "德国", "科特迪瓦", "Toronto Stadium", "多伦多"),
    ("2026-06-20", "05:00", "厄瓜多尔", "库拉索", "Kansas City Stadium", "堪萨斯城"),
    ("2026-06-20", "08:00", "荷兰", "瑞典", "Houston Stadium", "休斯顿"),
    ("2026-06-20", "11:00", "突尼斯", "日本", "BC Place Vancouver", "温哥华"),

    # === 6月21日（今晚）===
    ("2026-06-21", "00:00", "西班牙", "沙特", "Atlanta Stadium", "亚特兰大"),
    ("2026-06-21", "03:00", "比利时", "伊朗", "Los Angeles Stadium", "洛杉矶"),
    ("2026-06-21", "06:00", "乌拉圭", "佛得角", "Miami Stadium", "迈阿密"),
    ("2026-06-21", "09:00", "新西兰", "埃及", "BC Place Vancouver", "温哥华"),

    # === 6月22日（明天）===
    ("2026-06-22", "00:00", "阿根廷", "奥地利", "Dallas Stadium", "达拉斯"),
    ("2026-06-22", "03:00", "约旦", "阿尔及利亚", "San Francisco Bay Area Stadium", "旧金山湾区"),
    ("2026-06-22", "06:00", "挪威", "塞内加尔", "New York New Jersey Stadium", "纽约/新泽西"),
    ("2026-06-22", "09:00", "法国", "伊拉克", "Philadelphia Stadium", "费城"),

    # === 6月23日 ===
    ("2026-06-23", "00:00", "葡萄牙", "乌兹别克斯坦", "Houston Stadium", "休斯顿"),
    ("2026-06-23", "03:00", "哥伦比亚", "刚果(金)", "Guadalajara Stadium", "瓜达拉哈拉"),
    ("2026-06-23", "06:00", "英格兰", "加纳", "Boston Stadium", "波士顿"),
    ("2026-06-23", "09:00", "巴拿马", "克罗地亚", "Toronto Stadium", "多伦多"),

    # === 6月24日 ===
    ("2026-06-24", "00:00", "瑞士", "加拿大", "BC Place Vancouver", "温哥华"),
    ("2026-06-24", "03:00", "波黑", "卡塔尔", "Seattle Stadium", "西雅图"),
    ("2026-06-24", "06:00", "苏格兰", "巴西", "Miami Stadium", "迈阿密"),
    ("2026-06-24", "09:00", "摩洛哥", "海地", "Atlanta Stadium", "亚特兰大"),

    # === 6月25日 ===
    ("2026-06-25", "00:00", "库拉索", "科特迪瓦", "Philadelphia Stadium", "费城"),
    ("2026-06-25", "03:00", "厄瓜多尔", "德国", "New York New Jersey Stadium", "纽约/新泽西"),
    ("2026-06-25", "06:00", "日本", "瑞典", "Dallas Stadium", "达拉斯"),
    ("2026-06-25", "09:00", "突尼斯", "荷兰", "Kansas City Stadium", "堪萨斯城"),

    # === 6月26日 ===
    ("2026-06-26", "00:00", "乌拉圭", "西班牙", "Guadalajara Stadium", "瓜达拉哈拉"),
    ("2026-06-26", "03:00", "佛得角", "沙特", "Houston Stadium", "休斯顿"),
    ("2026-06-26", "06:00", "埃及", "伊朗", "Seattle Stadium", "西雅图"),
    ("2026-06-26", "09:00", "新西兰", "比利时", "BC Place Vancouver", "温哥华"),

    # === 6月27日 ===
    ("2026-06-27", "00:00", "阿尔及利亚", "奥地利", "Kansas City Stadium", "堪萨斯城"),
    ("2026-06-27", "03:00", "约旦", "阿根廷", "Dallas Stadium", "达拉斯"),
    ("2026-06-27", "06:00", "哥伦比亚", "葡萄牙", "Miami Stadium", "迈阿密"),
    ("2026-06-27", "09:00", "刚果(金)", "乌兹别克斯坦", "Atlanta Stadium", "亚特兰大"),
    ("2026-06-27", "20:00", "克罗地亚", "加纳", "Philadelphia Stadium", "费城"),
    ("2026-06-27", "22:00", "巴拿马", "英格兰", "New York New Jersey Stadium", "纽约/新泽西"),

    # === 6月28日 - 淘汰赛开始 ===
    ("2026-06-28", "03:00", "A组第二", "B组第二", "Los Angeles Stadium", "洛杉矶"),

    # === 6月29日 ===
    ("2026-06-29", "01:00", "E组第一", "A/B/C/D/F组第三", "Boston Stadium", "波士顿"),
    ("2026-06-29", "04:00", "F组第一", "C组第二", "Estadio Monterrey", "蒙特雷"),
    ("2026-06-29", "08:00", "C组第一", "F组第二", "Houston Stadium", "休斯顿"),

    # === 6月30日 ===
    ("2026-06-30", "01:00", "I组第一", "C/D/F/G/H组第三", "New York New Jersey Stadium", "纽约/新泽西"),
    ("2026-06-30", "04:00", "E组第二", "I组第二", "Dallas Stadium", "达拉斯"),
    ("2026-06-30", "08:00", "A组第一", "C/E/F/H/I组第三", "Mexico City Stadium", "墨西哥城"),

    # === 7月1日 ===
    ("2026-07-01", "01:00", "L组第一", "E/H/I/J/K组第三", "Atlanta Stadium", "亚特兰大"),
    ("2026-07-01", "04:00", "D组第一", "B/E/F/I/J组第三", "San Francisco Bay Area Stadium", "旧金山湾区"),
    ("2026-07-01", "08:00", "G组第一", "A/E/H/I/J组第三", "Seattle Stadium", "西雅图"),

    # === 7月2日 ===
    ("2026-07-02", "01:00", "K组第二", "L组第二", "Toronto Stadium", "多伦多"),
    ("2026-07-02", "04:00", "H组第一", "J组第二", "Los Angeles Stadium", "洛杉矶"),
    ("2026-07-02", "08:00", "B组第一", "E/F/G/I/J组第三", "BC Place Vancouver", "温哥华"),

    # === 7月3日 ===
    ("2026-07-03", "01:00", "J组第一", "H组第二", "Miami Stadium", "迈阿密"),
    ("2026-07-03", "04:00", "K组第一", "D/E/I/J/L组第三", "Kansas City Stadium", "堪萨斯城"),
    ("2026-07-03", "08:00", "D组第二", "G组第二", "Dallas Stadium", "达拉斯"),

    # === 7月4-7日 1/8决赛 ===
    ("2026-07-04", "01:00", "74胜者", "77胜者", "Philadelphia Stadium", "费城"),
    ("2026-07-04", "04:00", "73胜者", "75胜者", "Houston Stadium", "休斯顿"),
    ("2026-07-05", "01:00", "76胜者", "78胜者", "New York New Jersey Stadium", "纽约/新泽西"),
    ("2026-07-05", "04:00", "79胜者", "80胜者", "Mexico City Stadium", "墨西哥城"),
    ("2026-07-06", "01:00", "83胜者", "84胜者", "Dallas Stadium", "达拉斯"),
    ("2026-07-06", "04:00", "81胜者", "82胜者", "Seattle Stadium", "西雅图"),
    ("2026-07-07", "01:00", "86胜者", "88胜者", "Atlanta Stadium", "亚特兰大"),
    ("2026-07-07", "04:00", "85胜者", "87胜者", "BC Place Vancouver", "温哥华"),

    # === 7月9-11日 1/4决赛 ===
    ("2026-07-09", "01:00", "89胜者", "90胜者", "Boston Stadium", "波士顿"),
    ("2026-07-10", "01:00", "93胜者", "94胜者", "Los Angeles Stadium", "洛杉矶"),
    ("2026-07-11", "01:00", "99胜者", "92胜者", "Miami Stadium", "迈阿密"),
    ("2026-07-11", "04:00", "95胜者", "96胜者", "Kansas City Stadium", "堪萨斯城"),

    # === 7月14-15日 半决赛 ===
    ("2026-07-14", "01:00", "97胜者", "98胜者", "Dallas Stadium", "达拉斯"),
    ("2026-07-15", "01:00", "99胜者", "100胜者", "Atlanta Stadium", "亚特兰大"),

    # === 7月18日 三四名 ===
    ("2026-07-18", "01:00", "101负者", "102负者", "Miami Stadium", "迈阿密"),

    # === 7月19日 决赛 ===
    ("2026-07-19", "01:00", "101胜者", "102胜者", "New York New Jersey Stadium", "纽约/新泽西"),
]


# ---------------------------------------------------------------------------
# 预测引擎初始化
# ---------------------------------------------------------------------------
RATING = RatingEngine()
MOMENTUM = MomentumEngine()
TACTICAL = TacticalEngine()
PREDICTION = PredictionEngine()


def _parse_time(time_str: str) -> int:
    """将 'HH:MM' 转为小时整数。"""
    return int(time_str.split(":")[0])


def get_matches_for_period(
    base_date: date,
    period: str = "tonight_early_morning_morning"
) -> List[Tuple[str, str, str, str, str, str]]:
    """
    获取指定日期"今天+明天"的比赛。

    世界杯期间比赛均在北京时间凌晨到上午进行（00:00-12:00）。
    定时任务每晚18:00运行时，"今天"的比赛指 base_date 当天 00:00-12:00 的场次，
    "明天"的比赛指 base_date + 1 天 00:00-12:00 的场次。
    """
    matches: List[Tuple[str, str, str, str, str, str]] = []

    # "今天"的比赛 (base_date, 00:00-12:00)
    for d, t, h, a, v, c in WORLD_CUP_SCHEDULE_BEIJING:
        match_date = datetime.strptime(d, "%Y-%m-%d").date()
        hour = _parse_time(t)
        if match_date == base_date and 0 <= hour <= 12:
            matches.append((d, t, h, a, v, c))

    # "明天"的比赛 (base_date + 1, 00:00-12:00)
    next_day = base_date + timedelta(days=1)
    for d, t, h, a, v, c in WORLD_CUP_SCHEDULE_BEIJING:
        match_date = datetime.strptime(d, "%Y-%m-%d").date()
        hour = _parse_time(t)
        if match_date == next_day and 0 <= hour <= 12:
            matches.append((d, t, h, a, v, c))

    return matches


def predict_match(home_name: str, away_name: str) -> dict:
    """对一场比赛进行预测，返回结构化结果。"""
    # 处理占位符（淘汰赛阶段）
    if "胜者" in home_name or "负者" in home_name or "组" in home_name:
        return {
            "home": home_name,
            "away": away_name,
            "status": "placeholder",
            "note": "淘汰赛对阵尚未确定，无法预测",
        }

    # 获取球队对象（支持别名）
    home = TEAMS.get(home_name) or TEAMS.get(TEAM_ALIASES.get(home_name, ""))
    away = TEAMS.get(away_name) or TEAMS.get(TEAM_ALIASES.get(away_name, ""))

    if home is None or away is None:
        return {
            "home": home_name,
            "away": away_name,
            "status": "missing_team",
            "note": f"球队数据缺失: {home_name if home is None else away_name}",
        }

    # 执行预测
    prediction = PREDICTION.predict_match(home, away, neutral=True)
    result = prediction.data

    # 格式化输出
    top_scores = result.get("top_scores", [])
    most = top_scores[0] if top_scores else (0, 0, 0.0)
    second = top_scores[1] if len(top_scores) > 1 else (0, 0, 0.0)

    return {
        "home": home_name,
        "away": away_name,
        "status": "predicted",
        "home_rating": round(result.get("home_rating", 0), 2),
        "away_rating": round(result.get("away_rating", 0), 2),
        "rating_diff": round(result.get("rating_diff", 0), 2),
        "home_win": round(result.get("home_win", 0) * 100, 1),
        "draw": round(result.get("draw", 0) * 100, 1),
        "away_win": round(result.get("away_win", 0) * 100, 1),
        "over_25": round(result.get("over_25", 0) * 100, 1),
        "most_probable": f"{most[0]}-{most[1]}",
        "most_prob": round(most[2] * 100, 2),
        "second_probable": f"{second[0]}-{second[1]}",
        "second_prob": round(second[2] * 100, 2),
        "momentum_home": result.get("momentum_delta_home", 0),
        "momentum_away": result.get("momentum_delta_away", 0),
    }


def generate_report(base_date: date) -> str:
    """生成完整的预测报告。"""
    lines: List[str] = []

    # 报告头
    lines.append("=" * 70)
    lines.append("  2026 美加墨世界杯 - 每日比赛预测报告")
    lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    lines.append(f"  预测范围: {base_date.strftime('%Y-%m-%d')} (今天) + {base_date + timedelta(days=1)} (明天)")
    lines.append("=" * 70)
    lines.append("")

    # 获取比赛
    matches = get_matches_for_period(base_date)

    if not matches:
        lines.append("⚠️  该时段无世界杯比赛安排")
        lines.append("")
        lines.append("世界杯赛程: 2026-06-11 至 2026-07-19")
        return "\n".join(lines)

    # 按日期分组
    current_date = ""
    for d, t, h, a, v, c in matches:
        if d != current_date:
            current_date = d
            date_obj = datetime.strptime(d, "%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
            lines.append(f"\n{'─' * 70}")
            lines.append(f"  📅 {d} {weekday}")
            lines.append(f"{'─' * 70}")

        # 预测
        pred = predict_match(h, a)

        if pred["status"] == "placeholder":
            lines.append(f"\n  ⏰ {t}  {h} vs {a}")
            lines.append(f"     📍 {v} ({c})")
            lines.append(f"     ⚠️  对阵尚未确定，跳过预测")
            continue

        if pred["status"] == "missing_team":
            lines.append(f"\n  ⏰ {t}  {h} vs {a}")
            lines.append(f"     📍 {v} ({c})")
            lines.append(f"     ⚠️  {pred['note']}")
            continue

        # 判断胜负倾向
        hw, dr, aw = pred["home_win"], pred["draw"], pred["away_win"]
        if hw > aw and hw > dr:
            tendency = f"🏠 主胜 {hw}%"
            confidence = "高" if hw > 60 else "中" if hw > 45 else "低"
        elif aw > hw and aw > dr:
            tendency = f"✈️ 客胜 {aw}%"
            confidence = "高" if aw > 60 else "中" if aw > 45 else "低"
        else:
            tendency = f"🤝 平局 {dr}%"
            confidence = "中"

        lines.append(f"\n  ⏰ {t}  {h} vs {a}")
        lines.append(f"     📍 {v} ({c})")
        lines.append(f"     📊 评分: {h} {pred['home_rating']} vs {pred['away_rating']} {a} (差: {pred['rating_diff']:+.2f})")
        lines.append(f"     🎯 倾向: {tendency} | 信心: {confidence}")
        lines.append(f"     📈 概率: 主胜 {hw}% | 平局 {dr}% | 客胜 {aw}%")
        lines.append(f"     ⚽ 比分: 最可能 {pred['most_probable']} ({pred['most_prob']}%) | 次可能 {pred['second_probable']} ({pred['second_prob']}%)")
        lines.append(f"     🔮 大小球: {'大' if pred['over_25'] > 50 else '小'}2.5 ({pred['over_25']}%)")

        # 动力修正提示
        mh, ma = pred["momentum_home"], pred["momentum_away"]
        if abs(mh) > 0.3 or abs(ma) > 0.3:
            effects = []
            if mh > 0.3:
                effects.append(f"{h} 动力↑")
            elif mh < -0.3:
                effects.append(f"{h} 动力↓")
            if ma > 0.3:
                effects.append(f"{a} 动力↑")
            elif ma < -0.3:
                effects.append(f"{a} 动力↓")
            lines.append(f"     💡 动量: {', '.join(effects)}")

    # 报告尾
    lines.append("")
    lines.append("=" * 70)
    lines.append("  ⚠️ 免责声明: 本预测基于历史数据和统计模型，仅供参考")
    lines.append("  不构成投注建议。足球比赛结果受多种因素影响，请理性对待。")
    lines.append("=" * 70)

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="2026世界杯每日比赛预测 (北京时间)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=date.today().isoformat(),
        help="预测基准日期 (YYYY-MM-DD)，默认今天",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="输出文件路径，默认 stdout",
    )
    args = parser.parse_args()

    try:
        base_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"错误: 日期格式无效 '{args.date}'，请使用 YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    report = generate_report(base_date)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ 报告已保存到: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
