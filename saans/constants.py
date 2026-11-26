"""Every fixed number the app uses, in ONE place, with its source.

Why this file exists: the challenge asks us to explain the *impact* of each
choice. Impact numbers are only trustworthy if every input is traceable.
So nothing numeric is hidden inside other modules — it lives here, next to
the reference (see sources.py for the full links) or is marked ASSUMPTION.
Flow: imported by aqi.py, exposure.py, data.py, advisor.py, ai.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone

# ---------- Time ----------------------------------------------------------------
# India has a single time zone and no daylight saving, so a fixed +05:30 offset
# is exact and avoids needing the tzdata package on Windows / slim containers.
IST = timezone(timedelta(hours=5, minutes=30), "IST")


# ---------- Cities --------------------------------------------------------------
@dataclass(frozen=True)
class City:
    """A preset place. `demo_pm25` is ONLY used when live data is unavailable
    and is always shown with a "demo data" label — it is not a measurement."""

    name: str
    lat: float
    lon: float
    demo_pm25: float  # illustrative winter base level for the offline demo (µg/m³)
    note_key: str = ""  # optional i18n key with a local, factual context note


# Jharkhand first (the builder's home region), then a few big smog cities.
CITIES: dict[str, City] = {
    c.name: c
    for c in (
        City("Hazaribagh", 23.9925, 85.3637, 70, "note_hazaribagh"),
        City("Ranchi", 23.3441, 85.3096, 85),
        City("Dhanbad", 23.7957, 86.4304, 125, "note_dhanbad"),
        City("Jamshedpur", 22.8046, 86.2029, 95),
        City("Bokaro", 23.6693, 86.1511, 105),
        City("Patna", 25.5941, 85.1376, 150),
        City("Kolkata", 22.5726, 88.3639, 110),
        City("Delhi", 28.6139, 77.2090, 210),
    )
}
DEFAULT_CITY = "Hazaribagh"
# Rough bounding box of India — used to reject typo coordinates (lat 236 etc.).
INDIA_LAT = (6.0, 37.5)
INDIA_LON = (68.0, 97.5)
# Coordinates are rounded before any API call: ~1 km precision is plenty for
# city air quality, protects the user's exact location and raises cache hits.
COORD_DECIMALS = 2

# ---------- Demo data shape (ASSUMPTION, labelled as demo in the UI) -------------
# Typical North-Indian winter pattern: night-time inversion traps smoke, the
# morning traffic peak adds to it, afternoon sun mixes the air (lowest levels),
# and the evening cooking / traffic peak brings it back up.
DEMO_DIURNAL_FACTORS: tuple[float, ...] = (
    1.25, 1.30, 1.32, 1.33, 1.33, 1.35, 1.40, 1.45, 1.35, 1.10, 0.90, 0.75,
    0.65, 0.60, 0.58, 0.60, 0.70, 0.90, 1.15, 1.30, 1.35, 1.30, 1.28, 1.26,
)  # fmt: skip
DEMO_PM10_RATIO = 1.7  # ASSUMPTION for demo only: PM10 ≈ 1.7 × PM2.5 in winter dust+smoke mix

# ---------- CPCB National AQI breakpoints (24-h, µg/m³) -------------------------
# Source: CPCB, "National Air Quality Index" (2014), Table of health breakpoints.
# Each row: (conc_low, conc_high, index_low, index_high), exactly CPCB's integer
# bands — so CPCB's own worked example holds: PM2.5 31 -> 51, 45 -> 75, 60 -> 100.
# Upper limit of the last band follows the common CPCB calculator convention;
# the index is capped at 500.
PM25_BREAKPOINTS: tuple[tuple[float, float, int, int], ...] = (
    (0, 30, 0, 50),
    (31, 60, 51, 100),
    (61, 90, 101, 200),
    (91, 120, 201, 300),
    (121, 250, 301, 400),
    (251, 380, 401, 500),
)
PM10_BREAKPOINTS: tuple[tuple[float, float, int, int], ...] = (
    (0, 50, 0, 50),
    (51, 100, 51, 100),
    (101, 250, 101, 200),
    (251, 350, 201, 300),
    (351, 430, 301, 400),
    (431, 510, 401, 500),
)
AQI_MAX = 500

# ---------- Breathing rates (US EPA Exposure Factors Handbook 2011, Ch. 6) ------
# Short-term inhalation rates for adults 21–<31 y, converted from m³/min to m³/h.
VENTILATION_M3_PER_H: dict[str, float] = {
    "sedentary": 0.0042 * 60,  # sitting in a bus / auto
    "light": 0.012 * 60,  # walking, riding a two-wheeler
    "moderate": 0.026 * 60,  # brisk walk, cycling, yoga outdoors
    "high": 0.050 * 60,  # running, football, cricket
}

# ---------- Indoor mass-balance model ------------------------------------------
# Steady state: C_in = P · a · C_out / (a + k + CADR / V)   (standard single-zone model)
PENETRATION = 1.0  # ASSUMPTION (conservative): all outdoor PM2.5 that leaks in stays airborne
DEPOSITION_PER_H = 0.2  # ASSUMPTION: typical PM2.5 indoor deposition rate (literature 0.1–0.4 /h)
ACH_CLOSED = 0.5  # US EPA Exposure Factors Handbook Ch. 19: typical home air-exchange ≈ 0.45 /h
ACH_OPEN = 3.0  # ASSUMPTION: windows wide open (real value varies a lot with wind)
CEILING_M = 2.7  # ASSUMPTION: ~9 ft ceiling, common in Indian homes
PURIFIER_TARGET_ACH = 4.8  # US EPA / ENERGY STAR: purifier should give ≥ 4.8 air changes per hour

# ---------- Masks --------------------------------------------------------------
N95_FILTRATION = 0.95  # NIOSH 42 CFR Part 84: N95 filters ≥ 95 % of test particles (best case, good fit)

# ---------- Planning windows ---------------------------------------------------
DAY_START_HOUR = 5  # earliest hour we suggest going out
DAY_END_HOUR = 21  # latest hour an outdoor slot may END
FORECAST_HOURS = 24

# ---------- Input limits (validation) ------------------------------------------
MAX_MINUTES = 240
MAX_CADR_M3H = 2000
ROOM_AREA_M2 = (4, 120)
MAX_QUESTION_LEN = 300

# ---------- Gemini -------------------------------------------------------------
# Tried in order, so a retired model ID doesn't take the app down.
DEFAULT_MODELS = ("gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest")
AI_TIMEOUT_MS = 30_000
# The briefing itself is short, but newer Gemini models spend output tokens on
# "thinking" BEFORE writing; a tight cap (we had 900) cut the JSON off mid-way.
AI_MAX_OUTPUT_TOKENS = 4096
AI_TEMPERATURE = 0.4  # low: we want faithful wording of facts, not creativity

# ---------- Google Air Quality API ---------------------------------------------
AQ_BASE_URL = "https://airquality.googleapis.com/v1"
AQ_TIMEOUT_S = 8

# ---------- Open-Meteo Air Quality API (free fallback, no key) -------------------
# CAMS (Copernicus) hourly forecast; free for non-commercial use, attribution required.
OPEN_METEO_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
MIN_FORECAST_HOURS = 6  # shorter than this can't plan a day honestly
