"""CPCB National AQI maths — checked against CPCB's own worked examples and band edges."""

from __future__ import annotations

import math

import pytest

from saans.aqi import CATEGORIES, at_least, category_for, naqi, sub_index
from saans.constants import PM10_BREAKPOINTS, PM25_BREAKPOINTS


@pytest.mark.parametrize(
    ("pm25", "expected"),
    [
        (0, 0),
        (15, 25),
        (30, 50),
        (30.4, 51),  # gap between integer bands belongs to the next band
        (31, 51),  # CPCB example
        (45, 75),  # CPCB example
        (60, 100),  # CPCB example
        (61, 101),
        (90, 200),
        (91, 201),
        (120, 300),
        (121, 301),
        (250, 400),
        (251, 401),
        (380, 500),
        (999, 500),  # capped like CPCB
    ],
)
def test_pm25_sub_index(pm25, expected):
    assert sub_index(pm25, PM25_BREAKPOINTS) == expected


@pytest.mark.parametrize(
    ("pm10", "expected"), [(0, 0), (50, 50), (51, 51), (100, 100), (250, 200), (350, 300), (430, 400), (600, 500)]
)
def test_pm10_sub_index(pm10, expected):
    assert sub_index(pm10, PM10_BREAKPOINTS) == expected


@pytest.mark.parametrize("bad", [None, -1, math.nan])
def test_bad_values_are_missing_not_good(bad):
    assert sub_index(bad, PM25_BREAKPOINTS) is None


def test_naqi_takes_the_worse_pollutant():
    assert naqi(20, 300) == sub_index(300, PM10_BREAKPOINTS)
    assert naqi(200, 20) == sub_index(200, PM25_BREAKPOINTS)


def test_naqi_with_only_pm25_and_nothing():
    assert naqi(45) == 75
    assert naqi(None, None) is None


@pytest.mark.parametrize(
    ("aqi", "key"),
    [
        (0, "good"),
        (50, "good"),
        (51, "satisfactory"),
        (100, "satisfactory"),
        (101, "moderate"),
        (200, "moderate"),
        (201, "poor"),
        (300, "poor"),
        (301, "very_poor"),
        (400, "very_poor"),
        (401, "severe"),
        (500, "severe"),
        (900, "severe"),
    ],
)
def test_category_bands(aqi, key):
    assert category_for(aqi).key == key


def test_missing_aqi_is_not_reported_as_good():
    assert category_for(None).key == "moderate"


def test_categories_are_contiguous():
    for low, high in zip(CATEGORIES, CATEGORIES[1:], strict=False):
        assert high.low == low.high + 1


def test_at_least_ordering():
    assert at_least("severe", "poor")
    assert at_least("poor", "poor")
    assert not at_least("moderate", "poor")


def _luminance(hex_color: str) -> float:
    rgb = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


@pytest.mark.parametrize("cat", CATEGORIES, ids=lambda c: c.key)
def test_badge_text_passes_wcag_aa(cat):
    a, b = sorted((_luminance(cat.color), _luminance(cat.text_color)), reverse=True)
    assert (a + 0.05) / (b + 0.05) >= 4.5
