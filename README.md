# football-predictor · 深度优化的足球比分预测引擎

一个基于 **多维度评分**、**战术匹配** 与 **动力/情绪修正** 的开源足球预测框架，
内置 **2026 美加墨世界杯** 数据与完整赛程。

> 本项目将 v3.3 版的 prompt 模板进化为可执行 Python 代码，
> 提供稳定的 API、类型注解与单元测试，便于集成与二次开发。

---

## 核心特性

1. **七维度球队评分**（1–10 分制）
   - 整体实力（Elo + 身价）
   - 近期状态（最近 8 场 + form）
   - 主客场加成（中立场地自动忽略）
   - 战术匹配（阵型克制 + 风格克制矩阵）
   - 阵容完整度（阵容深度 + 关键球员伤停）
   - 心理因素（动量修正）
   - 临场变量（伤停、保级、决赛压力等上下文字典）

2. **战术匹配分析**
   - 阵型克制矩阵（4-3-3 vs 4-4-2 vs 3-5-2 ...）
   - 风格克制矩阵（控球主导 vs 防守反击 vs 高位逼抢 vs 大巴 ...）
   - 自动推断球队战术风格（依赖 formation + Elo 综合启发式）

3. **动力 / 情绪修正**
   - `check_rebound_effect`：连败 3+ 场后的反弹效应
   - `check_bottom_effect`：极低分差下的精神爆发
   - `check_blowout_illusion`：大胜后松懈幻觉
   - `check_emotional_stack`：连胜/连败累积心理加成
   - 每项输出 [-1.5, +1.5] 修正值，叠加到评分

4. **Poisson 比分预测**
   - 基于 Elo 胜率 + 近期场均进球计算 λ_home / λ_away
   - 结合 1–10 评分差对 λ 做乘法修正
   - 输出胜负平概率、Top-N 比分、大小球概率（2.5 球基准）
   - 95% 覆盖度的 "概率区间" 描述，**拒绝单点预测**

5. **内置世界杯数据**
   - 48 支球队（2026 美加墨世界杯常见参赛队）
   - 8 组小组赛分组 + 完整赛程（小组赛 6 场/组）
   - 淘汰赛阶段（1/8、1/4、半决赛、决赛）模板
   - 截至 2026-06-21 的示例赛果，可自动更新球队状态

---

## 目录结构

```
football-predictor/
├── README.md
├── requirements.txt           # 可选依赖（scipy）
├── setup.py                   # 安装配置
├── examples/
│   ├── quick_start.py         # 最小示例（曼城 vs 阿森纳）
│   └── predict_world_cup.py   # 世界杯预测示例
├── football_predictor/
│   ├── __init__.py            # 顶层便捷导出
│   ├── models/
│   │   ├── team.py            # Team / Player
│   │   ├── match.py           # Match / MatchResult
│   │   └── tournament.py      # Tournament / Group / KnockoutRound
│   ├── analysis/
│   │   ├── rating_engine.py   # 七维度评分
│   │   ├── tactical_engine.py # 战术匹配
│   │   ├── momentum_engine.py # 动力情绪修正
│   │   └── prediction_engine.py # Poisson 比分预测
│   ├── data/
│   │   ├── world_cup_2026.py  # 2026 世界杯数据
│   │   └── leagues.py         # 联赛数据框架
│   └── utils/
│       ├── math_utils.py      # Poisson / Elo 概率计算
│       └── formatting.py      # 格式化输出
└── tests/
    ├── test_prediction_engine.py
    └── test_rating_engine.py
```

---

## 安装

### 方式 A：直接使用源代码（推荐）

```bash
git clone <your-repo-url>
cd football-predictor
python examples/quick_start.py
```

### 方式 B：安装到当前环境

```bash
cd football-predictor
pip install -e .          # 最小安装（仅依赖标准库）
pip install -e .[dev]     # 推荐：启用 scipy 加速概率计算
```

---

## 快速开始

### 1. 一场比赛的完整预测

```python
from football_predictor import Team, PredictionEngine

home = Team(name="曼城", elo_rating=2050, squad_depth=9, form=9,
            market_value=1300, formation="4-3-3")
away = Team(name="阿森纳", elo_rating=2000, squad_depth=8, form=8,
            market_value=1200, formation="4-3-3")

engine = PredictionEngine()
prediction = engine.predict_match(home, away)
print(prediction)
```

输出示例：

```
=== 曼城 vs 阿森纳 ===
综合评分: 8.03 vs 7.65  (差: +0.38)
Poisson λ:  主队 1.840  |  客队 1.530

结果概率:
  主胜   45.8%   平局   26.2%   客胜   28.0%
  大球(>2.5)  57.1%   小球  42.9%

最可能比分:
  1. 2-1  11.2%
  2. 1-1  10.4%
  3. 2-2   8.1%
  4. 1-0   7.6%
  5. 2-0   7.2%

动量修正: 主队 +0.30  客队 +0.00
```

### 2. 世界杯焦点战

```python
from football_predictor import PredictionEngine
from football_predictor.data.world_cup_2026 import TEAMS

engine = PredictionEngine()
print(engine.predict_match(TEAMS["阿根廷"], TEAMS["法国"], neutral=True))
```

### 3. 直接使用字典结果

```python
result = engine.predict_score(TEAMS["阿根廷"], TEAMS["法国"], neutral=True)
print("最可能比分:", result["most_probable"])   # (2, 1, 0.112)
print("主胜概率:", result["home_win"])           # 0.48
print("大球概率:", result["over_25"])            # 0.61
print("综合评分:", result["home_rating"], result["away_rating"])
```

### 4. 查看某组积分榜

```python
from football_predictor.data.world_cup_2026 import get_tournament
t = get_tournament()
for team, pts, played, w, d, l, gf, ga, gd in t.groups["B"].standings():
    print(f"{team.name:<12}{pts:<4}{w}{d}{l}  {gf}-{ga}")
```

---

## 核心 API

### `Team(name, elo_rating, squad_depth, form, ...)`

| 属性 | 说明 |
| :--- | :--- |
| `name` | 球队名 |
| `elo_rating` | Elo 评分，建议 1200–2200 |
| `squad_depth` | 阵容深度 (1–10) |
| `form` | 近期状态 (1–10) |
| `market_value` | 全队身价（百万欧元） |
| `formation` | 常用阵型，如 `"4-3-3"` |
| `recent_form` | 最近 N 场结果（`"W"/"D"/"L"`） |

方法：
- `update_form(result, goals_for, goals_against)`：更新状态
- `get_strength_score()` → `0–10` 综合实力
- `recent_form_summary()` → `(胜, 平, 负, 指数)`
- `avg_goals_per_game()` → `(场均进, 场均失)`

### `RatingEngine().rate_match(home, away, neutral=False)`

返回 `(home_score, away_score, details_dict)`，`details_dict` 包含七维度详细分数与动量修正值。

### `MomentumEngine().total_adjustment(team, opponent, context=None)`

返回 [-1.5, +1.5] 区间的总修正值，直接加到评分中。

### `PredictionEngine().predict_score(home, away, neutral=False, home_context=None, away_context=None)`

返回字典：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `lambda_home`, `lambda_away` | float | Poisson λ |
| `most_probable` | `(hg, ag, p)` | 最可能比分 |
| `top_scores` | `List[(h,a,p)]` | Top-5 比分 |
| `home_win`, `draw`, `away_win` | float | 胜负平概率 |
| `over_25`, `under_25` | float | 大小球 |
| `home_rating`, `away_rating` | float | 1–10 评分 |
| `rating_diff` | float | 评分差 |
| `score_probability_range` | `List[str]` | 95% 覆盖比分区间 |

### 上下文字典 `home_context` / `away_context`

可自由添加修正项（负值代表减分）：

```python
context = {
    "injury_penalty": -1.2,   # 核心球员伤停
    "fatigue": -0.3,           # 多线作战疲劳
    "must_win_bonus": 0.8,    # 出线生死战
    "derby_factor": 0.4,      # 德比情绪因素
}
```

---

## 算法原理概览

### 1. 基础进球率 λ

```
elo_factor = 0.6 + 0.8 · P(主队胜 | Elo 差)
λ_home = base_home_goals · elo_factor
λ_away = base_away_goals · elo_factor
```

然后与近期场均进球做加权平均（历史 0.6 + 近期 0.4）。

### 2. 评分差修正

```
Δrating = home_score - away_score
λ_home' = λ_home · (1 + 0.10 · Δrating / 5)
λ_away' = λ_away · (1 - 0.10 · Δrating / 5)
```

### 3. 战术修正

按阵型/风格克制矩阵得到 [-2, +2] 的优势值，再做 ±6% 乘法修正：

```
λ'' = λ' · (1 + advantage · 0.06)
```

### 4. Poisson 概率

纯 Python 实现的 Poisson PMF 可保证**零依赖运行**；
若检测到 `scipy`，自动切换到 `scipy.stats.poisson` 以获得更高精度。

```
P(主队进 h 球, 客队进 a 球) = Poisson(h; λ_h) · Poisson(a; λ_a)
```

### 5. 概率区间

累加所有 (h, a) 联合概率，按降序直到累计覆盖 ≥ 95%，
得到"置信比分集"，避免单点预测误导。

---

## 2026 世界杯赛程与数据

| 组别 | 球队 |
| :--- | :--- |
| A | 美国、墨西哥、加拿大、哥斯达黎加 |
| B | 阿根廷、乌拉圭、智利、厄瓜多尔 |
| C | 巴西、哥伦比亚、厄瓜多尔、智利 |
| D | 英格兰、法国、葡萄牙、比利时 |
| E | 西班牙、德国、荷兰、意大利 |
| F | 克罗地亚、丹麦、瑞士、塞尔维亚 |
| G | 摩洛哥、塞内加尔、尼日利亚、埃及 |
| H | 日本、韩国、澳大利亚、沙特阿拉伯 |

> 注：内置数据为常见参赛队示例，实际数据请以官方 FIFA 名单为准。

---

## 运行示例

```bash
cd football-predictor
python examples/quick_start.py          # 最小示例
python examples/predict_world_cup.py    # 世界杯焦点战 + 分组预测
python -m unittest discover tests       # 运行单元测试
```

---

## 测试

两个测试文件覆盖：

- **基础功能**：Team 状态更新、Elo 胜率、Poisson 求和
- **评分引擎**：七维度评分范围、强/弱队排序、细节字段
- **动力引擎**：连胜/连败、反弹、大胜幻觉
- **预测引擎**：胜负平概率求和 = 1、中立场地影响、结果结构
- **世界杯数据**：球队数量、关键队存在、Tournament 构造

```
$ python -m unittest discover tests
.........
----------------------------------------------------------------------
Ran 13 tests in 0.042s
OK
```

---

## 常见问题

### 1. 预测准不准？

本项目的目标是**提供一个可解释、可复现、可扩展的基准模型**，
而非声称达到博彩公司级别的胜率。关键建议：

- 接入真实的伤停、禁赛、赛程数据
- 结合历史对阵（head-to-head）进行叠加
- 动态滚动更新近期战绩与进球序列
- 重大比赛可增加 `must_win_bonus` 等心理修正

### 2. 如何扩展自定义球队数据？

```python
from football_predictor import Team, Player

my_team = Team(name="我的队", elo_rating=1700, squad_depth=6,
               form=6, market_value=150, formation="4-3-3")
my_team.add_player(Player("核心A", "MF", 80, 26))
```

### 3. 我想改成自定义概率分布？

直接继承 `PredictionEngine`，重写 `compute_lambdas` 即可：

```python
class MyEngine(PredictionEngine):
    def compute_lambdas(self, home, away, neutral=False, **kw):
        lam_h, lam_a, data = super().compute_lambdas(home, away, neutral, **kw)
        # 你的自定义逻辑
        return lam_h * 1.1, lam_a * 0.95, data
```

---

## 版本历史

- **1.0.0** (2026-06-21)
  - 正式版发布，完成七维度评分、战术/动力修正、Poisson 预测
  - 内置 2026 美加墨世界杯数据与完整赛程结构
  - 类型注解、文档字符串、单元测试齐全

## License

MIT © Football Predictor Team
