"""Google Air Quality API client (with a fake HTTP layer) and the labelled demo fallback."""

from __future__ import annotations

import pytest
from conftest import FakeGet, FakePost, google_hour, open_meteo_payload

from saans.constants import AQ_BASE_URL, IST, OPEN_METEO_URL
from saans.data import (
    AirDataError,
    demo_snapshot,
    fetch_open_meteo,
    fetch_snapshot,
    get_snapshot,
    parse_reading,
)


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


DOWN = FakeGet(error=AirDataError("URLError"))


@pytest.mark.parametrize("error", [AirDataError("HTTP 403"), TimeoutError(), ValueError("boom")])
def test_google_failure_falls_back_to_open_meteo(now, error):
    snap = get_snapshot("Ranchi", 23.34, 85.31, "KEY", now, FakePost(error=error), FakeGet(open_meteo_payload()))
    assert snap.source == "open_meteo"


@pytest.mark.parametrize("error", [AirDataError("HTTP 403"), TimeoutError(), ValueError("boom")])
def test_both_down_gives_labelled_demo_with_both_reasons(now, error):
    snap = get_snapshot("Ranchi", 23.34, 85.31, "KEY", now, FakePost(error=error), DOWN)
    assert snap.source == "demo" and len(snap.forecast) == 24
    assert "Google" in snap.note and "Open-Meteo" in snap.note


def test_google_preferred_when_it_works(now, google_payloads):
    get = FakeGet(open_meteo_payload())
    snap = get_snapshot("Ranchi", 23.34, 85.31, "KEY", now, FakePost(*google_payloads), get)
    assert snap.source == "google" and get.calls == []  # Open-Meteo not even called


def test_no_google_key_goes_straight_to_open_meteo(now):
    post = FakePost(error=AssertionError("must not be called"))
    snap = get_snapshot("Ranchi", 23.34, 85.31, "", now, post, FakeGet(open_meteo_payload()))
    assert snap.source == "open_meteo" and post.calls == []


def test_no_key_and_open_meteo_down_is_demo_with_reason(now):
    snap = get_snapshot("Ranchi", 23.34, 85.31, "", now, None, DOWN)
    assert snap.source == "demo" and snap.note == "Open-Meteo: URLError"


def test_open_meteo_parsing(now):
    get = FakeGet(open_meteo_payload())
    snap = fetch_open_meteo("Ranchi", 23.34, 85.31, now, get)
    url, params = get.calls[0]
    assert url == OPEN_METEO_URL and params["hourly"] == "pm2_5,pm10" and params["timezone"] == "Asia/Kolkata"
    # NOW is 15:30 IST -> current = the 15:00 reading (hour index 15 -> 65.0), forecast starts 16:00.
    assert snap.current.time.hour == 15 and snap.current.pm25 == 65.0 and snap.current.time.tzinfo == IST
    assert snap.forecast[0].time.hour == 16 and len(snap.forecast) == 24
    assert snap.forecast[0].pm10 == 106.0


def test_open_meteo_skips_null_hours(now):
    payload = open_meteo_payload()
    payload["hourly"]["pm2_5"][16] = None
    snap = fetch_open_meteo("Ranchi", 23.34, 85.31, now, FakeGet(payload))
    assert all(r.time.hour != 16 or r.time.day != 26 for r in snap.forecast)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"hourly": "nope"},
        open_meteo_payload(units="ppm"),
        open_meteo_payload(hours=17),  # only up to 16:00 today -> forecast too short
        open_meteo_payload(start_iso="2026-11-27T00:00"),  # all in the future -> no "current"
        {"hourly_units": {"pm2_5": "\u03bcg/m\u00b3"}, "hourly": {"time": ["bad"], "pm2_5": [5.0], "pm10": [5.0]}},
    ],
)
def test_open_meteo_bad_payloads_raise(now, payload):
    with pytest.raises(AirDataError):
        fetch_open_meteo("Ranchi", 23.34, 85.31, now, FakeGet(payload))


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
