"""Air-quality data: Google Air Quality API first, honest demo data as fallback.

Why Google Air Quality API: it gives current conditions AND a 96-hour hourly
forecast for any lat/lon in India from one key — the forecast is what makes
"go out at 3 pm, not 7 am" possible.

Design:
  * The HTTP call is injected (`post` parameter) so tests never touch the
    network and we can simulate timeouts, bad JSON and missing fields.
  * The API key goes in the `X-Goog-Api-Key` header, never in the URL, so it
    can't leak into logs or browser history. It stays on the server.
  * Any failure -> `demo_snapshot()`, clearly labelled "demo" with the reason,
    so the app keeps working but never pretends demo numbers are measured.
Flow: app.py (cached) -> fetch_snapshot() -> AirSnapshot -> advisor.py
"""

from __future__ import annotations

import json
import logging
import urllib.error
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
)
from .models import AirSnapshot, Reading

logger = logging.getLogger(__name__)

PostFn = Callable[[str, dict, str], dict]
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
    if len(forecast) < 6:  # too short to plan a day honestly
        raise AirDataError("forecast too short")
    return AirSnapshot(city=city, current=current, forecast=forecast, source="google")


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


def get_snapshot(  # noqa: PLR0917 - location + key + clock + injectable HTTP for tests
    city: str, lat: float, lon: float, api_key: str, now: datetime, post: PostFn = http_post_json
) -> AirSnapshot:
    """Live data if possible, otherwise demo data that says why. Never raises."""
    try:
        return fetch_snapshot(city, lat, lon, api_key, now, post)
    except AirDataError as exc:
        reason = str(exc)
    except Exception as exc:  # anything unexpected from the network stack: still never crash the UI
        logger.warning("Unexpected air-data error: %s", type(exc).__name__)
        reason = type(exc).__name__
    return demo_snapshot(city, now, note=reason)
