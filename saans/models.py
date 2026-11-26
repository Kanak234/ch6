"""Small, immutable data types shared across the app.

Why frozen dataclasses: they are hashable (so Streamlit can cache on them),
can't be changed by accident halfway through a plan, and make the flow
between modules explicit. Enums keep allowed choices in one place, so the
UI, validation and advisor can never disagree about what "bus" means.
Flow: validation.py builds Profile -> data.py builds AirSnapshot ->
      advisor.py builds Plan -> app.py renders it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Lang(str, Enum):
    EN = "en"
    HI = "hi"
    HINGLISH = "hinglish"


class Commute(str, Enum):
    """How the user travels. Value = breathing level while doing it."""

    WALK = "walk"
    CYCLE = "cycle"
    TWO_WHEELER = "two_wheeler"
    AUTO = "auto"
    BUS = "bus"
    CAR = "car"
    NONE = "none"  # works / studies from home


COMMUTE_ACTIVITY: dict[Commute, str] = {
    Commute.WALK: "light",
    Commute.CYCLE: "moderate",
    Commute.TWO_WHEELER: "light",
    Commute.AUTO: "sedentary",
    Commute.BUS: "sedentary",
    Commute.CAR: "sedentary",
    Commute.NONE: "sedentary",
}


class Exercise(str, Enum):
    WALK = "walk"  # light breathing
    ACTIVE = "active"  # yoga, cycling, brisk walk -> moderate
    SPORT = "sport"  # running, cricket, football -> high
    NONE = "none"


EXERCISE_ACTIVITY: dict[Exercise, str] = {
    Exercise.WALK: "light",
    Exercise.ACTIVE: "moderate",
    Exercise.SPORT: "high",
    Exercise.NONE: "sedentary",
}


class Fuel(str, Enum):
    LPG = "lpg"
    ELECTRIC = "electric"
    BIOMASS = "biomass"  # chulha: wood, dung cakes, crop waste
    COAL = "coal"
    KEROSENE = "kerosene"


POLLUTING_FUELS = frozenset({Fuel.BIOMASS, Fuel.COAL, Fuel.KEROSENE})


@dataclass(frozen=True)
class Profile:
    """Everything we know about the household — only what the plan needs, nothing stored."""

    city: str
    lat: float
    lon: float
    lang: Lang = Lang.EN
    children: bool = False
    elderly: bool = False
    respiratory: bool = False  # asthma / COPD / heart condition in the family
    commute: Commute = Commute.BUS
    commute_minutes: int = 30
    commute_hour: int = 9
    exercise: Exercise = Exercise.WALK
    exercise_minutes: int = 30
    exercise_hour: int = 6
    fuel: Fuel = Fuel.LPG
    burns_waste: bool = False
    burns_incense: bool = False  # agarbatti / mosquito coil indoors
    has_purifier: bool = False
    purifier_cadr: int = 0  # m³/h, printed on the box
    room_area_m2: float = 12.0

    @property
    def vulnerable(self) -> bool:
        """Children, elderly or someone with a lung/heart condition at home."""
        return self.children or self.elderly or self.respiratory


@dataclass(frozen=True)
class Reading:
    """One hour of air data. pm10 may be missing in some API responses."""

    time: datetime
    pm25: float
    pm10: float | None = None


@dataclass(frozen=True)
class AirSnapshot:
    city: str
    current: Reading
    forecast: tuple[Reading, ...]  # next hours, oldest first
    source: str  # "google" (live) or "demo" (offline, clearly labelled)
    note: str = ""  # why we are on demo data, if we are


@dataclass(frozen=True)
class Window:
    """A block of consecutive hours and its average PM2.5."""

    start: datetime
    end: datetime
    mean_pm25: float


@dataclass(frozen=True)
class Impact:
    """One choice and what it changes — the core of the "explain impact" requirement.

    `before`/`after` are in `unit`. `sources` are keys into sources.SOURCES so
    every number on screen links to where its inputs came from.
    """

    key: str  # stable id, e.g. "exercise_timing"
    title: str
    before: float
    after: float
    unit: str
    sources: tuple[str, ...] = ()

    @property
    def change_pct(self) -> int:
        """Percentage reduction (positive = better). 0 if there was nothing to reduce."""
        if self.before <= 0:
            return 0
        return round((self.before - self.after) / self.before * 100)


@dataclass(frozen=True)
class Tip:
    """One piece of advice: what to do, why, and (optionally) its measured impact."""

    section: str  # "routine" | "indoor" | "sustainable"
    title: str
    detail: str
    impact: Impact | None = None
    priority: int = 2  # 1 = do today, 2 = recommended, 3 = good habit


@dataclass(frozen=True)
class Plan:
    profile: Profile
    snapshot: AirSnapshot
    aqi_now: int
    category: str  # category key, e.g. "very_poor"
    best_window: Window | None
    worst_window: Window | None
    tips: tuple[Tip, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    city_note: str = ""  # short local context (e.g. Dhanbad coal dust), already translated

    def section(self, name: str) -> tuple[Tip, ...]:
        """Tips of one section, most urgent first."""
        return tuple(sorted((t for t in self.tips if t.section == name), key=lambda t: t.priority))

    @property
    def impacts(self) -> tuple[Impact, ...]:
        return tuple(t.impact for t in self.tips if t.impact is not None)
