"""Air-quality data, in three tiers: Google -> Open-Meteo -> labelled demo.

1. Google Air Quality API (needs a key + billing): current conditions and a
   96-hour hourly forecast for any lat/lon in India.
2. Open-Meteo Air Quality API (free, no key): hourly PM2.5/PM10 forecast from
   the Copernicus (CAMS) model. Used automatically when Google is unavailable,
   so the app shows LIVE forecast data even without a paid Google project.
3. Demo data: only if both fail, and always labelled "demo" with the reason.
The hourly forecast is what makes "go out at 3 pm, not 7 am" possible.

Design:
  * The HTTP calls are injected (`post` / `get` parameters) so tests never
    touch the network and we can simulate timeouts, bad JSON and missing fields.
  * The Google key goes in the `X-Goog-Api-Key` header, never in the URL, so it
    can't leak into logs or browser history. It stays on the server.
Flow: app.py (cached) -> get_snapshot() -> AirSnapshot -> advisor.py
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timedelta

from .constants import (
    AQ_BASE_URL,
    AQ_TIMEOUT_S,
    CITIES,
    DEFAULT_CITY,
    DEMO_DIURNAL_FACTORS,
    DEMO_PM10_RATIO,
    FORECAST_HOURS,
    IST,
    MIN_FORECAST_HOURS,
    OPEN_METEO_URL,
)
from .models import AirSnapshot, Reading

logger = logging.getLogger(__name__)

PostFn = Callable[[str, dict, str], dict]
GetFn = Callable[[str, dict], dict]
MICROGRAMS = "MICROGRAMS_PER_CUBIC_METER"


class AirDataError(RuntimeError):
    """Live data could not be used. The message is a short, user-safe reason."""


def http_post_json(url: str, body: dict, api_key: str) -> dict:
    """POST JSON with a timeout; returns parsed JSON or raises AirDataError."""
    request = urllib.request.Request(  # noqa: S310 - URL is our own https constant, not user input
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=AQ_TIMEOUT_S) as response:  # noqa: S310
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise AirDataError(f"HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AirDataError(type(exc).__name__) from exc


def http_get_json(url: str, params: dict) -> dict:
    """GET with query parameters and a timeout; returns parsed JSON or raises AirDataError."""
    full = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full, headers={"User-Agent": "SaansSaathi/1.0"})  # noqa: S310 - our https constant
    try:
        with urllib.request.urlopen(request, timeout=AQ_TIMEOUT_S) as response:  # noqa: S310
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise AirDataError(f"HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AirDataError(type(exc).__name__) from exc


def _parse_time(value: object) -> datetime:
    """Google returns RFC-3339 UTC ('2026-11-26T10:00:00Z'); convert to IST."""
    if not isinstance(value, str):
        raise AirDataError("missing dateTime")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(IST)
    except ValueError as exc:
        raise AirDataError("bad dateTime") from exc


def _pollutant(entry: dict, code: str) -> float | None:
    """Concentration of one pollutant in µg/m³, or None if absent / other unit."""
    for item in entry.get("pollutants") or []:
        if not isinstance(item, dict) or item.get("code") != code:
            continue
        conc = item.get("concentration") or {}
        value, units = conc.get("value"), conc.get("units")
        if isinstance(value, (int, float)) and not isinstance(value, bool) and units == MICROGRAMS and value >= 0:
            return float(value)
    return None


def parse_reading(entry: dict) -> Reading:
    """One API hour -> Reading. PM2.5 is required (it drives the whole plan)."""
    if not isinstance(entry, dict):
        raise AirDataError("bad entry")
    pm25 = _pollutant(entry, "pm25")
    if pm25 is None:
        raise AirDataError("no PM2.5 in response")
    return Reading(_parse_time(entry.get("dateTime")), round(pm25, 1), _pollutant(entry, "pm10"))


def _body(lat: float, lon: float) -> dict:
    # POLLUTANT_CONCENTRATION gives raw µg/m³ (we compute CPCB AQI ourselves);
    # LOCAL_AQI makes Google also return India's ind_cpcb index for cross-checking.
    return {
        "location": {"latitude": lat, "longitude": lon},
        "extraComputations": ["POLLUTANT_CONCENTRATION", "LOCAL_AQI"],
        "languageCode": "en",
    }


def fetch_snapshot(  # noqa: PLR0917 - mirrors get_snapshot; all six inputs are needed
    city: str, lat: float, lon: float, api_key: str, now: datetime, post: PostFn = http_post_json
) -> AirSnapshot:
    """Live current conditions + next-24-h forecast. Raises AirDataError on any problem."""
    if not api_key:
        raise AirDataError("no API key")
    current = parse_reading(post(f"{AQ_BASE_URL}/currentConditions:lookup", _body(lat, lon), api_key))
    start = now.astimezone(IST).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    body = _body(lat, lon) | {
        "period": {
            "startTime": start.isoformat(),
            "endTime": (start + timedelta(hours=FORECAST_HOURS)).isoformat(),
        },
        "pageSize": FORECAST_HOURS,
    }
    raw = post(f"{AQ_BASE_URL}/forecast:lookup", body, api_key).get("hourlyForecasts") or []
    forecast = tuple(sorted((parse_reading(h) for h in raw), key=lambda r: r.time))
    if len(forecast) < MIN_FORECAST_HOURS:  # too short to plan a day honestly
        raise AirDataError("forecast too short")
    return AirSnapshot(city=city, current=current, forecast=forecast, source="google")


def _num(value: object) -> float | None:
    """A non-negative real number, or None (Open-Meteo uses null for missing hours)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return float(value)
    return None


def fetch_open_meteo(city: str, lat: float, lon: float, now: datetime, get: GetFn = http_get_json) -> AirSnapshot:
    """Free CAMS forecast via Open-Meteo. Raises AirDataError on any problem.

    We ask for times in Asia/Kolkata, so timestamps come back as local wall-clock
    ('2026-11-26T17:00') and we attach IST. "Current" = the latest hour that is
    not in the future; the forecast = the next 24 hours after it.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm2_5,pm10",
        "timezone": "Asia/Kolkata",
        "forecast_days": 2,  # today + tomorrow covers any 24-hour window
    }
    data = get(OPEN_METEO_URL, params)
    hourly = data.get("hourly") if isinstance(data, dict) else None
    if not isinstance(hourly, dict):
        raise AirDataError("no hourly data")
    units = (data.get("hourly_units") or {}).get("pm2_5", "")
    if "g/m" not in str(units):  # expect µg/m³ (Open-Meteo writes it with a Greek mu)
        raise AirDataError("unexpected units")
    times, pm25s, pm10s = hourly.get("time") or [], hourly.get("pm2_5") or [], hourly.get("pm10") or []
    readings: list[Reading] = []
    for i, stamp in enumerate(times):
        pm25 = _num(pm25s[i]) if i < len(pm25s) else None
        if pm25 is None or not isinstance(stamp, str):
            continue  # skip hours the model hasn't filled
        try:
            t = datetime.fromisoformat(stamp).replace(tzinfo=IST)
        except ValueError as exc:
            raise AirDataError("bad time") from exc
        pm10 = _num(pm10s[i]) if i < len(pm10s) else None
        readings.append(Reading(t, round(pm25, 1), None if pm10 is None else round(pm10, 1)))
    readings.sort(key=lambda r: r.time)
    hour0 = now.astimezone(IST).replace(minute=0, second=0, microsecond=0)
    past = [r for r in readings if r.time <= hour0]
    future = tuple(r for r in readings if r.time > hour0)[:FORECAST_HOURS]
    if not past or len(future) < MIN_FORECAST_HOURS:
        raise AirDataError("forecast too short")
    return AirSnapshot(city=city, current=past[-1], forecast=future, source="open_meteo")


def demo_snapshot(city: str, now: datetime, note: str = "") -> AirSnapshot:
    """Deterministic, clearly-labelled demo data shaped like a winter smog day.

    Same city + same hour -> same numbers (good for tests and for demos).
    """
    base = (CITIES.get(city) or CITIES[DEFAULT_CITY]).demo_pm25
    hour0 = now.astimezone(IST).replace(minute=0, second=0, microsecond=0)

    def reading(t: datetime) -> Reading:
        pm25 = round(base * DEMO_DIURNAL_FACTORS[t.hour], 1)
        return Reading(t, pm25, round(pm25 * DEMO_PM10_RATIO, 1))

    forecast = tuple(reading(hour0 + timedelta(hours=h)) for h in range(1, FORECAST_HOURS + 1))
    return AirSnapshot(city=city, current=reading(hour0), forecast=forecast, source="demo", note=note)


def _try(label: str, fetch: Callable[[], AirSnapshot]) -> tuple[AirSnapshot | None, str]:
    """Run one data source; return (snapshot, "") or (None, "Label: reason")."""
    try:
        return fetch(), ""
    except AirDataError as exc:
        return None, f"{label}: {exc}"
    except Exception as exc:  # anything unexpected from the network stack: never crash the UI
        logger.warning("Unexpected %s error: %s", label, type(exc).__name__)
        return None, f"{label}: {type(exc).__name__}"


def get_snapshot(  # noqa: PLR0913, PLR0917 - location + key + clock + injectable HTTP for tests
    city: str,
    lat: float,
    lon: float,
    api_key: str,
    now: datetime,
    post: PostFn | None = None,
    get: GetFn | None = None,
) -> AirSnapshot:
    """Google -> Open-Meteo -> labelled demo. Never raises.

    The HTTP functions are looked up at CALL time (not as default arguments),
    so tests can monkeypatch `data.http_get_json` / `data.http_post_json`.
    """
    post = post or http_post_json
    get = get or http_get_json
    reasons: list[str] = []
    if api_key:
        snap, why = _try("Google", lambda: fetch_snapshot(city, lat, lon, api_key, now, post))
        if snap:
            return snap
        reasons.append(why)
    snap, why = _try("Open-Meteo", lambda: fetch_open_meteo(city, lat, lon, now, get))
    if snap:
        return snap
    reasons.append(why)
    return demo_snapshot(city, now, note="; ".join(reasons))
