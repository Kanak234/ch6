"""India's National Air Quality Index (CPCB) — concentration to index to category.

Why we compute it ourselves instead of only trusting an API number:
  * the demo/offline path has no API, and
  * we need the SAME scale for current data, every forecast hour and every
    "what-if" in the impact table, so all comparisons are apples to apples.
Formula (CPCB 2014): I = (I_hi - I_lo) / (C_hi - C_lo) * (C - C_lo) + I_lo,
and the overall AQI is the highest pollutant sub-index.
Note: CPCB uses 24-hour averages; applying the bands to hourly values is an
estimate, and the UI says so ("PM-based estimate").
Flow: data.py / advisor.py -> naqi() -> category_for() -> UI colour + label.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import AQI_MAX, PM10_BREAKPOINTS, PM25_BREAKPOINTS

Breakpoints = tuple[tuple[float, float, int, int], ...]


def sub_index(conc: float | None, table: Breakpoints) -> int | None:
    """Linear interpolation inside the CPCB band that contains `conc`.

    Returns None for missing/negative/NaN input so a bad sensor value can never
    silently turn into "Good air".
    """
    if conc is None or math.isnan(conc) or conc < 0:
        return None
    for c_lo, c_hi, i_lo, i_hi in table:
        if conc <= c_hi:
            # CPCB bands are integers (…30 | 31…). A value in the gap, e.g. 30.4,
            # belongs to the next band and is clamped to its lower edge.
            c = max(conc, c_lo)
            return round((i_hi - i_lo) / (c_hi - c_lo) * (c - c_lo) + i_lo)
    return AQI_MAX  # above the last band -> capped at 500, exactly like CPCB


def naqi(pm25: float | None, pm10: float | None = None) -> int | None:
    """Overall index = the worse of the PM2.5 and PM10 sub-indices."""
    values = [v for v in (sub_index(pm25, PM25_BREAKPOINTS), sub_index(pm10, PM10_BREAKPOINTS)) if v is not None]
    return max(values) if values else None


@dataclass(frozen=True)
class Category:
    key: str  # i18n key and stable id
    low: int
    high: int
    color: str  # CPCB colour; ALWAYS shown together with the text label (no meaning by colour alone)
    text_color: str  # chosen so the badge passes WCAG AA contrast on its colour


# CPCB categories, colours from the official NAQI colour scheme.
CATEGORIES: tuple[Category, ...] = (
    Category("good", 0, 50, "#00B050", "#000000"),
    Category("satisfactory", 51, 100, "#92D050", "#000000"),
    Category("moderate", 101, 200, "#FFFF00", "#000000"),
    Category("poor", 201, 300, "#FF9900", "#000000"),
    Category("very_poor", 301, 400, "#FF0000", "#000000"),
    Category("severe", 401, 500, "#8B0000", "#FFFFFF"),
)
CATEGORY_ORDER = {c.key: i for i, c in enumerate(CATEGORIES)}


def category_for(aqi: int | None) -> Category:
    """Category for an index value; missing values are treated as the worst
    known-safe assumption ("moderate") rather than "good"."""
    if aqi is None:
        return CATEGORIES[2]
    for cat in CATEGORIES:
        if aqi <= cat.high:
            return cat
    return CATEGORIES[-1]


def at_least(category_key: str, threshold_key: str) -> bool:
    """True if `category_key` is as bad as or worse than `threshold_key`."""
    return CATEGORY_ORDER[category_key] >= CATEGORY_ORDER[threshold_key]
