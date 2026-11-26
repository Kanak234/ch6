"""The rule engine: air data + household profile -> today's plan.

This is where the four things the challenge asks for are produced:
  1. low-exposure daily routine      -> section "routine"
  2. indoor air improvement tips     -> section "indoor"
  3. sustainable, location-aware alternatives -> section "sustainable"
  4. the direct impact of each choice -> Impact objects attached to tips
Why rules (not the LLM) decide the advice: advice about breathing must be
consistent and checkable. The same inputs always give the same plan, every
number is computed in exposure.py, and Gemini (ai.py) only explains it.
Flow: app.py -> build_plan(snapshot, profile) -> Plan -> UI tabs + ai.py facts.
"""

from __future__ import annotations

from .aqi import at_least, category_for, naqi
from .constants import ACH_CLOSED, ACH_OPEN, CITIES
from .exposure import (
    best_window,
    fmt_window,
    indoor_pm25,
    inhaled_dose_ug,
    mean_at_hour,
    purifier_effect,
    recommended_cadr,
    room_volume_m3,
    with_n95,
    worst_window,
)
from .i18n import t
from .models import (
    COMMUTE_ACTIVITY,
    EXERCISE_ACTIVITY,
    POLLUTING_FUELS,
    AirSnapshot,
    Commute,
    Exercise,
    Impact,
    Plan,
    Profile,
    Tip,
    Window,
)

# A shift must save at least this share of exposure to be worth suggesting —
# otherwise we'd nag people to change habits for a 1 % difference.
MIN_WORTHWHILE_SAVING = 0.05
EXERCISE_LABEL_KEY = {Exercise.WALK: "act_walk", Exercise.ACTIVE: "act_active", Exercise.SPORT: "act_sport"}
POLLUTING_TRANSPORT = frozenset({Commute.TWO_WHEELER, Commute.CAR})
CLEAN_TRANSPORT = frozenset({Commute.WALK, Commute.CYCLE, Commute.BUS, Commute.AUTO})


def _cat_key(pm25: float) -> str:
    return category_for(naqi(pm25)).key


def _hour(h: int) -> str:
    return f"{h:02d}:00"


def _who(profile: Profile) -> str:
    """'children and elders' in the user's language (only those actually at home)."""
    lang = profile.lang
    parts = [
        t(lang, key)
        for key, present in (
            ("who_children", profile.children),
            ("who_elderly", profile.elderly),
            ("who_respiratory", profile.respiratory),
        )
        if present
    ]
    return t(lang, "who_join").join(parts)


def _shift_tip(  # noqa: PLR0913 - explicit inputs keep this pure and easy to test
    profile: Profile,
    *,
    usual: float,
    best: Window,
    hour: int,
    minutes: int,
    activity: str,
    impact_key: str,
    title_key: str,
    detail_key: str,
    label: str,
    priority: int,
) -> Tip:
    """'Do X at the clean time instead of your usual time' + its measured impact."""
    lang = profile.lang
    before = round(inhaled_dose_ug(usual, activity, minutes))
    after = round(inhaled_dose_ug(best.mean_pm25, activity, minutes))
    impact = Impact(
        impact_key,
        t(lang, impact_key),
        before,
        after,
        t(lang, "unit_dose"),
        ("google_aq", "open_meteo", "epa_efh6", "epa_expobox"),
    )
    values = {
        "activity": label,
        "mode": label,
        "window": fmt_window(best),
        "hour": _hour(hour),
        "usual": round(usual),
        "best": round(best.mean_pm25),
        "minutes": minutes,
        "pct": impact.change_pct,
    }
    return Tip("routine", t(lang, title_key, **values), t(lang, detail_key, **values), impact, priority)


def routine_tips(profile: Profile, snapshot: AirSnapshot, best: Window | None, worst: Window | None) -> list[Tip]:
    """Requirement 1 — when to go out and how to travel."""
    lang, forecast, tips = profile.lang, snapshot.forecast, []

    # --- Outdoor exercise ---------------------------------------------------
    if profile.exercise is not Exercise.NONE and profile.exercise_minutes > 0:
        minutes, activity = profile.exercise_minutes, EXERCISE_ACTIVITY[profile.exercise]
        label = t(lang, EXERCISE_LABEL_KEY[profile.exercise])
        slot = best_window(forecast, minutes)
        usual = mean_at_hour(forecast, profile.exercise_hour, minutes)
        if slot is not None:
            window = fmt_window(slot)
            slot_cat = _cat_key(slot.mean_pm25)
            if at_least(slot_cat, "very_poor"):
                tips.append(
                    Tip(
                        "routine",
                        t(lang, "t_exercise_indoor"),
                        t(lang, "d_exercise_indoor", window=window, category=t(lang, slot_cat)),
                        priority=1,
                    )
                )
            elif usual is not None and usual > slot.mean_pm25 * (1 + MIN_WORTHWHILE_SAVING):
                tips.append(
                    _shift_tip(
                        profile,
                        usual=usual,
                        best=slot,
                        hour=profile.exercise_hour,
                        minutes=minutes,
                        activity=activity,
                        impact_key="imp_exercise",
                        title_key="t_exercise_shift",
                        detail_key="d_exercise_shift",
                        label=label,
                        priority=1,
                    )
                )
            else:
                tips.append(
                    Tip(
                        "routine",
                        t(lang, "t_exercise_ok", activity=label),
                        t(lang, "d_exercise_ok", window=window, best=round(slot.mean_pm25)),
                        priority=3,
                    )
                )

    # --- Commute -----------------------------------------------------------
    if profile.commute is not Commute.NONE and profile.commute_minutes > 0:
        minutes, activity = profile.commute_minutes, COMMUTE_ACTIVITY[profile.commute]
        mode = t(lang, f"commute_{profile.commute.value}").lower()
        slot = best_window(forecast, minutes)
        usual = mean_at_hour(forecast, profile.commute_hour, minutes)
        if slot is not None and usual is not None and usual > slot.mean_pm25 * (1 + MIN_WORTHWHILE_SAVING):
            tips.append(
                _shift_tip(
                    profile,
                    usual=usual,
                    best=slot,
                    hour=profile.commute_hour,
                    minutes=minutes,
                    activity=activity,
                    impact_key="imp_commute",
                    title_key="t_commute_shift",
                    detail_key="d_commute_shift",
                    label=mode,
                    priority=2,
                )
            )
        # Masks only matter when the trip itself is in poor air.
        trip_pm25 = usual if usual is not None else snapshot.current.pm25
        trip_cat = _cat_key(trip_pm25)
        if at_least(trip_cat, "poor"):
            before = round(inhaled_dose_ug(trip_pm25, activity, minutes))
            after = round(with_n95(inhaled_dose_ug(trip_pm25, activity, minutes)))
            impact = Impact(
                "imp_mask", t(lang, "imp_mask"), before, after, t(lang, "unit_dose"), ("niosh_n95", "epa_efh6")
            )
            tips.append(
                Tip(
                    "routine",
                    t(lang, "t_mask", mode=mode),
                    t(lang, "d_mask", before=before, after=after),
                    impact,
                    1 if at_least(trip_cat, "very_poor") else 2,
                )
            )

    # --- Vulnerable family members -------------------------------------------
    if profile.vulnerable and best is not None and worst is not None:
        tips.append(
            Tip(
                "routine",
                t(lang, "t_vulnerable", who=_who(profile), worst=fmt_window(worst)),
                t(lang, "d_vulnerable", best=fmt_window(best)),
                priority=1,
            )
        )
    return tips


def indoor_tips(profile: Profile, best: Window | None, worst: Window | None) -> list[Tip]:
    """Requirement 2 — cleaner air at home."""
    lang, tips = profile.lang, []
    area = profile.room_area_m2
    peak = worst.mean_pm25 if worst is not None else None

    if peak is not None and best is not None and worst is not None:
        volume = room_volume_m3(area)
        before = round(indoor_pm25(peak, ACH_OPEN, volume))
        after = round(indoor_pm25(peak, ACH_CLOSED, volume))
        impact = Impact(
            "imp_windows",
            t(lang, "imp_windows"),
            before,
            after,
            t(lang, "unit_indoor"),
            ("epa_efh19", "google_aq", "open_meteo"),
        )
        tips.append(
            Tip(
                "indoor",
                t(lang, "t_windows", worst=fmt_window(worst), best=fmt_window(best)),
                t(lang, "d_windows", before=before, after=after, best=fmt_window(best)),
                impact,
                1 if at_least(_cat_key(peak), "poor") else 2,
            )
        )

    if peak is not None:
        cadr = profile.purifier_cadr if profile.has_purifier else recommended_cadr(area)
        no_purifier, with_purifier = (round(v) for v in purifier_effect(peak, area, cadr))
        impact = Impact(
            "imp_purifier",
            t(lang, "imp_purifier"),
            no_purifier,
            with_purifier,
            t(lang, "unit_indoor"),
            ("epa_air_cleaners", "energy_star", "epa_efh19"),
        )
        key = "purifier_have" if profile.has_purifier else "purifier_need"
        values = {"cadr": cadr, "area": f"{area:g}", "before": no_purifier, "after": with_purifier}
        tips.append(
            Tip(
                "indoor",
                t(lang, f"t_{key}", **values),
                t(lang, f"d_{key}", **values),
                impact,
                2 if profile.has_purifier else 3,
            )
        )

    if profile.fuel in POLLUTING_FUELS:
        fuel = t(lang, f"fuel_{profile.fuel.value}")
        tips.append(Tip("indoor", t(lang, "t_fuel", fuel=fuel), t(lang, "d_fuel"), priority=1))
    if profile.burns_incense:
        tips.append(Tip("indoor", t(lang, "t_incense"), t(lang, "d_incense"), priority=2))
    tips.append(Tip("indoor", t(lang, "t_wet_clean"), t(lang, "d_wet_clean"), priority=3))
    return tips


def sustainable_tips(profile: Profile, best: Window | None) -> list[Tip]:
    """Requirement 3 — greener alternatives that fit this household and place."""
    lang, tips = profile.lang, []
    if profile.burns_waste:
        tips.append(Tip("sustainable", t(lang, "t_waste"), t(lang, "d_waste"), priority=1))
    else:
        tips.append(Tip("sustainable", t(lang, "t_report"), t(lang, "d_report"), priority=3))

    if profile.commute in POLLUTING_TRANSPORT:
        mode = t(lang, f"commute_{profile.commute.value}").lower()
        slot = fmt_window(best) if best is not None else t(lang, "no_slot")
        tips.append(
            Tip("sustainable", t(lang, "t_transport"), t(lang, "d_transport", mode=mode, best=slot), priority=2)
        )
    elif profile.commute in CLEAN_TRANSPORT:
        tips.append(Tip("sustainable", t(lang, "t_transport_clean"), t(lang, "d_transport_clean"), priority=3))

    if profile.fuel in POLLUTING_FUELS:
        tips.append(Tip("sustainable", t(lang, "t_pmuy"), t(lang, "d_pmuy"), priority=2))
    return tips


def build_plan(snapshot: AirSnapshot, profile: Profile) -> Plan:
    """Assemble the whole plan. Pure function: same inputs -> same plan."""
    lang = profile.lang
    aqi_now = naqi(snapshot.current.pm25, snapshot.current.pm10) or 0
    category = category_for(aqi_now).key
    # "Cleanest slot" = best single hour; "peak smog" = worst 2-hour block.
    best = best_window(snapshot.forecast, 60)
    worst = worst_window(snapshot.forecast, 120)

    tips = [*routine_tips(profile, snapshot, best, worst), *indoor_tips(profile, best, worst)]
    tips += sustainable_tips(profile, best)

    warnings: list[str] = []
    if at_least(category, "very_poor"):
        warnings.append(t(lang, "w_severe", category=t(lang, category)))
    elif profile.vulnerable and at_least(category, "poor"):
        warnings.append(t(lang, "w_vulnerable", category=t(lang, category), who=_who(profile)))

    city = CITIES.get(profile.city)
    note = t(lang, city.note_key) if city and city.note_key else ""
    return Plan(profile, snapshot, aqi_now, category, best, worst, tuple(tips), tuple(warnings), note)
