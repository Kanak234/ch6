"""Shared pytest fixtures.

A fixed NOW makes every time-based test deterministic (never depends on when
the tests run). FakeGenerator / FakePost replace Gemini and the Google Air
Quality API, so the whole suite runs offline in a few seconds.
Flow: imported automatically by pytest.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Make `import saans` work when pytest runs from the repo root without installing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from saans.constants import IST  # noqa: E402
from saans.data import demo_snapshot  # noqa: E402
from saans.models import AirSnapshot, Commute, Exercise, Fuel, Lang, Profile  # noqa: E402

NOW = datetime(2026, 11, 26, 15, 30, tzinfo=IST)


@pytest.fixture
def now() -> datetime:
    return NOW


@pytest.fixture
def profile() -> Profile:
    """A typical Dhanbad family: kids + grandparent, bike commute, chulha, burns leaves."""
    return Profile(
        city="Dhanbad",
        lat=23.80,
        lon=86.43,
        lang=Lang.EN,
        children=True,
        elderly=True,
        commute=Commute.TWO_WHEELER,
        commute_minutes=30,
        commute_hour=8,
        exercise=Exercise.WALK,
        exercise_minutes=30,
        exercise_hour=6,
        fuel=Fuel.BIOMASS,
        burns_waste=True,
        burns_incense=True,
    )


@pytest.fixture
def snapshot(now: datetime) -> AirSnapshot:
    return demo_snapshot("Dhanbad", now)


class FakeGenerator:
    """Stands in for Gemini: returns canned text or raises, and records prompts."""

    def __init__(self, reply: str = "", error: Exception | None = None) -> None:
        self.reply, self.error, self.prompts = reply, error, []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.reply


@pytest.fixture
def fake_generator() -> type[FakeGenerator]:
    return FakeGenerator


def google_hour(iso: str, pm25: float | None, pm10: float | None = 120.0, units: str = "MICROGRAMS_PER_CUBIC_METER"):
    """Build one hour in the exact shape the Google Air Quality API returns."""
    pollutants = []
    if pm25 is not None:
        pollutants.append({"code": "pm25", "concentration": {"value": pm25, "units": units}})
    if pm10 is not None:
        pollutants.append({"code": "pm10", "concentration": {"value": pm10, "units": units}})
    return {"dateTime": iso, "indexes": [{"code": "ind_cpcb", "aqi": 200}], "pollutants": pollutants}


class FakePost:
    """Records calls and replays responses per endpoint (or raises)."""

    def __init__(self, current: dict | None = None, forecast: dict | None = None, error: Exception | None = None):
        self.current, self.forecast, self.error, self.calls = current, forecast, error, []

    def __call__(self, url: str, body: dict, api_key: str) -> dict:
        self.calls.append((url, body, api_key))
        if self.error:
            raise self.error
        return self.current if url.endswith("currentConditions:lookup") else self.forecast


@pytest.fixture
def google_payloads():
    current = google_hour("2026-11-26T10:00:00Z", 140.0)
    # 24 forecast hours from 11:00 UTC (16:30 IST rounded -> 16:00 IST) onwards, deliberately unsorted.
    hours = [google_hour(f"2026-11-{26 + (11 + h) // 24}T{(11 + h) % 24:02d}:00:00Z", 60.0 + h) for h in range(24)]
    return current, {"hourlyForecasts": list(reversed(hours))}


def open_meteo_payload(start_iso: str = "2026-11-26T00:00", hours: int = 48, units: str = "\u03bcg/m\u00b3"):
    """Open-Meteo hourly response (IST wall-clock times, as with timezone=Asia/Kolkata)."""
    from datetime import datetime as _dt
    from datetime import timedelta as _td

    t0 = _dt.fromisoformat(start_iso)
    times = [(t0 + _td(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(hours)]
    return {
        "timezone": "Asia/Kolkata",
        "hourly_units": {"time": "iso8601", "pm2_5": units, "pm10": units},
        "hourly": {"time": times, "pm2_5": [50.0 + h for h in range(hours)], "pm10": [90.0 + h for h in range(hours)]},
    }


class FakeGet:
    """Fake for data.http_get_json: replays one payload (or raises) and records calls."""

    def __init__(self, payload: dict | None = None, error: Exception | None = None):
        self.payload, self.error, self.calls = payload, error, []

    def __call__(self, url: str, params: dict) -> dict:
        self.calls.append((url, params))
        if self.error:
            raise self.error
        return self.payload
