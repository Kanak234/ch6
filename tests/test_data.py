"""Google Air Quality API client (with a fake HTTP layer) and the labelled demo fallback."""

from __future__ import annotations

import pytest
from conftest import FakePost, google_hour

from saans.constants import AQ_BASE_URL, IST
from saans.data import AirDataError, demo_snapshot, fetch_snapshot, get_snapshot, parse_reading


def test_parse_reading_converts_to_ist():
    r = parse_reading(google_hour("2026-11-26T10:00:00Z", 140.4, 210.0))
    assert r.time.hour == 15 and r.time.minute == 30 and r.time.tzinfo == IST
    assert (r.pm25, r.pm10) == (140.4, 210.0)


def test_pm10_optional():
    assert parse_reading(google_hour("2026-11-26T10:00:00Z", 50.0, None)).pm10 is None


@pytest.mark.parametrize(
    "entry",
    [
        google_hour("2026-11-26T10:00:00Z", None),  # no PM2.5
        google_hour("2026-11-26T10:00:00Z", 50.0, units="PARTS_PER_BILLION"),  # wrong unit
        google_hour("not-a-date", 50.0),
        {"pollutants": "nonsense"},
        "not a dict",
    ],
)
def test_bad_entries_raise(entry):
    with pytest.raises(AirDataError):
        parse_reading(entry)


def test_negative_concentration_is_rejected():
    with pytest.raises(AirDataError):
        parse_reading(google_hour("2026-11-26T10:00:00Z", -3.0))


def test_fetch_snapshot_live(now, google_payloads):
    current, forecast = google_payloads
    post = FakePost(current, forecast)
    snap = fetch_snapshot("Ranchi", 23.34, 85.31, "KEY", now, post)
    assert snap.source == "google" and snap.current.pm25 == 140.0
    assert len(snap.forecast) == 24
    assert [r.time for r in snap.forecast] == sorted(r.time for r in snap.forecast)  # sorted even if API isn't


def test_request_shape_and_key_never_in_url(now, google_payloads):
    post = FakePost(*google_payloads)
    fetch_snapshot("Ranchi", 23.34, 85.31, "SECRET", now, post)
    urls = [c[0] for c in post.calls]
    assert urls == [f"{AQ_BASE_URL}/currentConditions:lookup", f"{AQ_BASE_URL}/forecast:lookup"]
    assert all("SECRET" not in u for u in urls)
    body = post.calls[1][1]
    assert body["location"] == {"latitude": 23.34, "longitude": 85.31}
    assert "POLLUTANT_CONCENTRATION" in body["extraComputations"]
    assert body["pageSize"] == 24 and "startTime" in body["period"]


def test_no_key_raises(now):
    with pytest.raises(AirDataError):
        fetch_snapshot("Ranchi", 23.34, 85.31, "", now, FakePost())


def test_short_forecast_rejected(now, google_payloads):
    current, _ = google_payloads
    post = FakePost(current, {"hourlyForecasts": [google_hour("2026-11-26T11:00:00Z", 60.0)]})
    with pytest.raises(AirDataError):
        fetch_snapshot("Ranchi", 23.34, 85.31, "KEY", now, post)


@pytest.mark.parametrize("error", [AirDataError("HTTP 403"), TimeoutError(), ValueError("boom")])
def test_get_snapshot_falls_back_to_labelled_demo(now, error):
    snap = get_snapshot("Ranchi", 23.34, 85.31, "KEY", now, FakePost(error=error))
    assert snap.source == "demo" and snap.note
    assert len(snap.forecast) == 24


def test_get_snapshot_without_key_is_demo_with_reason(now):
    snap = get_snapshot("Ranchi", 23.34, 85.31, "", now)
    assert snap.source == "demo" and snap.note == "no API key"


def test_demo_is_deterministic_and_hourly(now):
    a, b = demo_snapshot("Delhi", now), demo_snapshot("Delhi", now)
    assert a == b
    gaps = {(y.time - x.time).total_seconds() for x, y in zip(a.forecast, a.forecast[1:], strict=False)}
    assert gaps == {3600.0}


def test_demo_has_winter_shape(now):
    snap = demo_snapshot("Hazaribagh", now)
    by_hour = {r.time.hour: r.pm25 for r in snap.forecast}
    assert by_hour[7] > by_hour[14]  # morning inversion worse than afternoon


def test_demo_unknown_city_uses_default(now):
    assert demo_snapshot("Nowhere", now).forecast == demo_snapshot("Hazaribagh", now).forecast
