"""Physics behind the impact numbers: inhaled dose, indoor mass balance, best/worst windows."""

from __future__ import annotations

from datetime import timedelta

import pytest

from saans.constants import ACH_CLOSED, ACH_OPEN, VENTILATION_M3_PER_H
from saans.exposure import (
    best_window,
    fmt_window,
    indoor_pm25,
    inhaled_dose_ug,
    mean_at_hour,
    purifier_effect,
    recommended_cadr,
    room_volume_m3,
    windows,
    with_n95,
    worst_window,
)
from saans.models import Reading


def test_dose_formula():
    # 100 µg/m³ × 0.72 m³/h (light) × 0.5 h = 36 µg
    assert inhaled_dose_ug(100, "light", 30) == pytest.approx(36.0)


@pytest.mark.parametrize("activity", list(VENTILATION_M3_PER_H))
def test_dose_scales_linearly(activity):
    assert inhaled_dose_ug(200, activity, 60) == pytest.approx(2 * inhaled_dose_ug(100, activity, 60))


def test_harder_breathing_means_more_dose():
    doses = [inhaled_dose_ug(100, a, 30) for a in ("sedentary", "light", "moderate", "high")]
    assert doses == sorted(doses)


def test_dose_never_negative():
    assert inhaled_dose_ug(-50, "light", 30) == 0
    assert inhaled_dose_ug(50, "light", -30) == 0


def test_n95_best_case():
    assert with_n95(100) == pytest.approx(5)


def test_indoor_lower_than_outdoor_and_closed_beats_open():
    v = room_volume_m3(12)
    open_, closed = indoor_pm25(200, ACH_OPEN, v), indoor_pm25(200, ACH_CLOSED, v)
    assert closed < open_ < 200


def test_purifier_reduces_indoor_and_bigger_is_better():
    small = purifier_effect(200, 12, 100)
    big = purifier_effect(200, 12, 400)
    assert small[1] < small[0]
    assert big[1] < small[1]
    assert small[0] == big[0]  # same baseline


def test_indoor_zero_outdoor_is_zero():
    assert indoor_pm25(0, ACH_OPEN, 30) == 0


def test_indoor_rejects_bad_volume():
    with pytest.raises(ValueError):
        indoor_pm25(100, 1, 0)


@pytest.mark.parametrize(("area", "cadr"), [(10, 130), (12, 156), (20, 260)])
def test_recommended_cadr_gives_48_ach(area, cadr):
    assert recommended_cadr(area) == cadr
    assert recommended_cadr(area) / room_volume_m3(area) >= 4.8


def _series(start, values):
    return tuple(Reading(start + timedelta(hours=i), v) for i, v in enumerate(values))


def test_best_window_is_the_cleanest_daytime_block(now):
    start = now.replace(hour=0, minute=0)
    values = [10] * 5 + [300, 300, 200, 100, 80, 60, 40, 30, 50, 70, 90, 120, 150, 200, 250, 260, 270, 280, 290]
    forecast = _series(start, values)
    best = best_window(forecast, 60)
    assert best.start.hour == 12 and best.mean_pm25 == 30
    # 2-hour block: 11-12 (40+30)/2 = 35 vs 12-13 (30+50)/2 = 40
    assert best_window(forecast, 120).start.hour == 11


def test_night_hours_never_recommended(now):
    start = now.replace(hour=0, minute=0)
    forecast = _series(start, [1] * 5 + [500] * 19)  # super clean only at 0-4 am
    assert best_window(forecast, 60).start.hour >= 5


def test_windows_must_end_by_evening(now):
    start = now.replace(hour=0, minute=0)
    forecast = _series(start, [100] * 24)
    assert all(w.end.hour < 21 for w in windows(forecast, 120))


def test_non_consecutive_hours_are_skipped(now):
    start = now.replace(hour=10, minute=0)
    gap = (Reading(start, 50), Reading(start + timedelta(hours=2), 50))
    assert windows(gap, 120) == []


def test_worst_window(now):
    start = now.replace(hour=5, minute=0)
    forecast = _series(start, [100, 400, 380, 90, 80])
    assert worst_window(forecast, 120).start.hour == 6


def test_empty_forecast():
    assert best_window((), 60) is None
    assert worst_window((), 60) is None


def test_mean_at_hour(now):
    start = now.replace(hour=6, minute=0)
    forecast = _series(start, [100, 50, 20])
    assert mean_at_hour(forecast, 6, 120) == 75
    assert mean_at_hour(forecast, 7, 30) == 50
    assert mean_at_hour(forecast, 23, 30) is None


def test_fmt_window_has_date_and_24h_clock(now):
    w = best_window(_series(now.replace(hour=14, minute=0), [10, 20]), 60)
    assert fmt_window(w) == "26/11 14:00–14:59"
