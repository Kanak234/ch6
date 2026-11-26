"""Input cleaning and validation — the app's first line of defence.

Why: every value the user types reaches either the physics (doses, indoor
model) or the Gemini prompt. Cleaning it once, here, means:
  * no control characters / HTML tags are echoed into the page (XSS-safe),
  * free text is length-capped (keeps the prompt small, fast and cheap),
  * common prompt-injection phrases are neutralised before reaching the model,
  * out-of-range numbers become friendly messages instead of wrong maths,
  * coordinates are rounded (privacy + better cache hits).
Flow: app.py form -> build_profile() / clean_question() -> Profile -> data.py, advisor.py
"""

from __future__ import annotations

import re
import unicodedata

from .constants import (
    CITIES,
    COORD_DECIMALS,
    INDIA_LAT,
    INDIA_LON,
    MAX_CADR_M3H,
    MAX_MINUTES,
    MAX_QUESTION_LEN,
    ROOM_AREA_M2,
)
from .models import Commute, Exercise, Fuel, Lang, Profile

# Compiled once at import time so repeated validation is cheap.
_TAG_RE = re.compile(r"<[^>]*>")
_SPACE_RE = re.compile(r"\s+")
# Phrases commonly used to hijack an LLM. We don't block the user — we strip
# the phrase so it can't act as an instruction inside our prompt.
_INJECTION_RE = re.compile(
    r"(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier)\s+"
    r"(instructions?|prompts?|rules?)"
    r"|system\s*prompt|developer\s*mode|you\s+are\s+now|act\s+as\s+(an?\s+)?",
    re.IGNORECASE,
)


def clean_text(value: object, max_len: int = MAX_QUESTION_LEN) -> str:
    """Return a safe, single-line, length-capped version of free text.

    Steps: normalise unicode -> drop control/format chars -> drop HTML tags ->
    neutralise injection phrases -> collapse whitespace -> cap length.
    Devanagari is kept intact (its vowel signs are category M, not C).
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    # Category "C*" = control/format chars (e.g. \x00, zero-width chars used to hide text).
    text = "".join(ch if not unicodedata.category(ch).startswith("C") else " " for ch in text)
    text = _TAG_RE.sub("", text)
    text = _INJECTION_RE.sub("", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text[:max_len]


def clean_question(value: object) -> str:
    """The "Ask Saans Saathi" box: same cleaning, question-sized cap."""
    return clean_text(value, MAX_QUESTION_LEN)


def valid_coordinates(lat: object, lon: object) -> tuple[float, float] | None:
    """Rounded (lat, lon) if both are numbers inside India, else None."""
    try:
        la, lo = float(lat), float(lon)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not (INDIA_LAT[0] <= la <= INDIA_LAT[1] and INDIA_LON[0] <= lo <= INDIA_LON[1]):
        return None
    return round(la, COORD_DECIMALS), round(lo, COORD_DECIMALS)


def _enum(kind: type, raw: object, default):
    """Map a raw value back to an enum member; fall back to `default` if unknown."""
    try:
        return kind(raw)
    except ValueError:
        return default


def _int_in(value: object, low: int, high: int) -> int | None:
    """int(value) if it is a whole number in [low, high], else None (bool is rejected)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not value.is_integer():  # 30.5 minutes is a typo, not 30
            return None
        value = int(value)
    try:
        number = int(str(value).strip())  # accepts 30 and "30", rejects "30a" / None
    except ValueError:
        return None
    return number if low <= number <= high else None


def build_profile(  # noqa: PLR0912 - one flat list of checks reads better than many helpers
    *,
    city: str,
    lat: object = None,
    lon: object = None,
    lang: str = "en",
    children: bool = False,
    elderly: bool = False,
    respiratory: bool = False,
    commute: str = "bus",
    commute_minutes: object = 30,
    commute_hour: object = 9,
    exercise: str = "walk",
    exercise_minutes: object = 30,
    exercise_hour: object = 6,
    fuel: str = "lpg",
    burns_waste: bool = False,
    burns_incense: bool = False,
    has_purifier: bool = False,
    purifier_cadr: object = 0,
    room_area_m2: object = 12,
) -> tuple[Profile | None, list[str]]:
    """Validate raw form values.

    Returns (Profile, []) on success or (None, [error keys]) on failure, so the
    UI can show every problem at once. Errors are i18n keys, not sentences,
    so they appear in the user's language.
    Custom coordinates (if given) win over the preset city's coordinates.
    """
    errors: list[str] = []

    name = clean_text(city, 60)
    preset = CITIES.get(name)
    if lat is not None or lon is not None:
        coords = valid_coordinates(lat, lon)
        if coords is None:
            errors.append("err_coords")
    elif preset is not None:
        coords = (preset.lat, preset.lon)
    else:
        coords = None
        errors.append("err_city")
    if not name:
        name = "Custom location"

    c_min = _int_in(commute_minutes, 0, MAX_MINUTES)
    e_min = _int_in(exercise_minutes, 0, MAX_MINUTES)
    if c_min is None or e_min is None:
        errors.append("err_minutes")
    c_hour = _int_in(commute_hour, 0, 23)
    e_hour = _int_in(exercise_hour, 0, 23)
    if c_hour is None or e_hour is None:
        errors.append("err_hour")
    cadr = _int_in(purifier_cadr, 0, MAX_CADR_M3H)
    if cadr is None:
        errors.append("err_cadr")
    elif has_purifier and cadr == 0:
        errors.append("err_cadr_missing")
    try:
        area = float(room_area_m2)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        area = -1.0
    if not ROOM_AREA_M2[0] <= area <= ROOM_AREA_M2[1]:
        errors.append("err_room")

    if errors or coords is None:
        return None, errors

    return (
        Profile(
            city=name,
            lat=coords[0],
            lon=coords[1],
            lang=_enum(Lang, lang, Lang.EN),
            children=bool(children),
            elderly=bool(elderly),
            respiratory=bool(respiratory),
            commute=_enum(Commute, commute, Commute.BUS),
            commute_minutes=c_min or 0,
            commute_hour=c_hour or 0,
            exercise=_enum(Exercise, exercise, Exercise.WALK),
            exercise_minutes=e_min or 0,
            exercise_hour=e_hour or 0,
            fuel=_enum(Fuel, fuel, Fuel.LPG),
            burns_waste=bool(burns_waste),
            burns_incense=bool(burns_incense),
            has_purifier=bool(has_purifier),
            purifier_cadr=cadr if has_purifier else 0,
            room_area_m2=round(area, 1),
        ),
        [],
    )
