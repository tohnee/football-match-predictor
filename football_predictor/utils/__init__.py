"""
utils/__init__.py - 工具函数包
===============================
"""

from football_predictor.utils.math_utils import (
    poisson_pmf,
    poisson_cdf,
    poisson_compare,
    draw_probability,
    match_probability,
    outcome_probabilities,
    most_probable_scoreline,
    over_under_probability,
    elo_win_probability,
    clamp,
    lerp,
)
from football_predictor.utils.formatting import (
    format_scoreline,
    format_percent,
    format_scoreline_table,
    pprint_rating,
)

__all__ = [
    "poisson_pmf",
    "poisson_cdf",
    "poisson_compare",
    "draw_probability",
    "match_probability",
    "outcome_probabilities",
    "most_probable_scoreline",
    "over_under_probability",
    "elo_win_probability",
    "clamp",
    "lerp",
    "format_scoreline",
    "format_percent",
    "format_scoreline_table",
    "pprint_rating",
]
