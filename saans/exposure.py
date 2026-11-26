"""The physics behind every "impact" number. No AI here — only formulas.

Two models, both standard in exposure science:

1. Inhaled dose (US EPA ExpoBox):
       dose (µg) = concentration (µg/m³) × breathing rate (m³/h) × hours
   Breathing rates come from the EPA Exposure Factors Handbook (constants.py).
   This lets us say "walking at 3 pm instead of 7 am cuts what you breathe in by X %".

2. Single-zone indoor mass balance (steady state):
       C_in = P · a · C_out / (a + k + CADR / V)
   P = penetration, a = air changes per hour, k = deposition rate,
   CADR = purifier clean-air delivery rate (m³/h), V = room volume (m³).
   This lets us compare "windows open vs closed" and "purifier vs none".

Every function is pure (same input -> same output) so it is trivial to test.
Flow: advisor.py calls these to fill Impact(before, after).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import datetime

from .constants import (
    ACH_CLOSED,
    CEILING_M,
    DAY_END_HOUR,
    DAY_START_HOUR,
    DEPOSITION_PER_H,
    N95_FILTRATION,
    PENETRATION,
    PURIFIER_TARGET_ACH,
    VENTILATION_M3_PER_H,
)
from .models import Reading, Window


def inhaled_dose_ug(pm25: float, activity: str, minutes: float) -> float:
    """Micrograms of PM2.5 breathed in during an activity. Negative inputs -> 0."""
    rate = VENTILATION_M3_PER_H[activity]
    return max(pm25, 0.0) * rate * max(minutes, 0.0) / 60.0


def with_n95(dose_ug: float) -> float:
    """Best-case dose while wearing a well-fitted N95 (≥95 % filtration, NIOSH)."""
    return dose_ug * (1 - N95_FILTRATION)


def room_volume_m3(area_m2: float) -> float:
    return area_m2 * CEILING_M


def indoor_pm25(outdoor: float, ach: float, volume_m3: float, cadr_m3h: float = 0.0) -> float:
    """Steady-state indoor PM2.5 with no indoor source (single-zone mass balance)."""
    if volume_m3 <= 0:
        raise ValueError("room volume must be positive")
    removal = ach + DEPOSITION_PER_H + max(cadr_m3h, 0.0) / volume_m3
    return PENETRATION * ach * max(outdoor, 0.0) / removal


def recommended_cadr(area_m2: float) -> int:
    """Smallest purifier CADR (m³/h) giving the EPA / ENERGY STAR target of 4.8 air changes/hour."""
    return math.ceil(room_volume_m3(area_m2) * PURIFIER_TARGET_ACH)


def purifier_effect(outdoor: float, area_m2: float, cadr_m3h: float) -> tuple[float, float]:
    """(indoor PM2.5 without purifier, with purifier) — windows closed in both cases."""
    volume = room_volume_m3(area_m2)
    return indoor_pm25(outdoor, ACH_CLOSED, volume), indoor_pm25(outdoor, ACH_CLOSED, volume, cadr_m3h)


def _hours_needed(minutes: int) -> int:
    """An activity of N minutes occupies ceil(N/60) forecast hours (at least 1)."""
    return max(1, math.ceil(minutes / 60))


def windows(
    forecast: Sequence[Reading],
    minutes: int,
    day_start: int = DAY_START_HOUR,
    day_end: int = DAY_END_HOUR,
) -> list[Window]:
    """Every daytime block long enough for the activity, cleanest first.

    A block is only offered if it starts at/after `day_start` and finishes by
    `day_end` local time, and its hours are consecutive in the forecast — we
    never recommend going for a walk at 2 a.m. just because the number is low.
    """
    span = _hours_needed(minutes)
    found: list[Window] = []
    for i in range(len(forecast) - span + 1):
        block = forecast[i : i + span]
        first, last = block[0].time, block[-1].time
        consecutive = all((b.time - a.time).total_seconds() == 3600 for a, b in zip(block, block[1:], strict=False))
        end_hour = last.hour + 1
        if not consecutive or first.hour < day_start or end_hour > day_end or first.date() != last.date():
            continue
        mean = sum(r.pm25 for r in block) / span
        found.append(Window(first, last.replace(minute=59), round(mean, 1)))
    # Ties broken by the earlier time, so results are deterministic.
    return sorted(found, key=lambda w: (w.mean_pm25, w.start))


def best_window(forecast: Sequence[Reading], minutes: int) -> Window | None:
    options = windows(forecast, minutes)
    return options[0] if options else None


def worst_window(forecast: Sequence[Reading], minutes: int) -> Window | None:
    options = windows(forecast, minutes)
    return max(options, key=lambda w: (w.mean_pm25, -w.start.timestamp())) if options else None


def mean_at_hour(forecast: Sequence[Reading], hour: int, minutes: int) -> float | None:
    """Average PM2.5 for an activity starting at the NEXT occurrence of `hour`.

    Used for "your usual time" so we compare the user's habit with the best slot
    on the same forecast. None if that hour is not in the forecast.
    """
    span = _hours_needed(minutes)
    for i, reading in enumerate(forecast):
        if reading.time.hour == hour:
            block = forecast[i : i + span]
            return round(sum(r.pm25 for r in block) / len(block), 1)
    return None


def fmt_window(window: Window) -> str:
    """'27/11 15:00–16:59' — numeric day/month + 24-hour clock.

    The date matters: after ~3 pm the cleanest slot is often TOMORROW afternoon,
    and digits read the same in English, हिंदी and Hinglish.
    """
    return f"{window.start:%d/%m %H:%M}–{window.end:%H:%M}"


def hour_label(dt: datetime) -> str:
    return f"{dt:%H:%M}"
