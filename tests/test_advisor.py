"""The rule engine: each challenge requirement is produced, numbers are consistent, all 3 languages render."""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import timedelta

import pytest

from saans.advisor import build_plan
from saans.models import AirSnapshot, Commute, Exercise, Fuel, Lang, Reading


def test_plan_covers_all_four_requirements(snapshot, profile):
    plan = build_plan(snapshot, profile)
    assert plan.section("routine")  # 1. low-exposure routine
    assert plan.section("indoor")  # 2. indoor air tips
    assert plan.section("sustainable")  # 3. greener alternatives
    assert plan.impacts  # 4. impact of each choice


def test_every_impact_is_an_improvement_with_sources(snapshot, profile):
    for impact in build_plan(snapshot, profile).impacts:
        assert impact.after <= impact.before
        assert 0 <= impact.change_pct <= 100
        assert impact.sources


def test_impact_percent_matches_numbers(snapshot, profile):
    for i in build_plan(snapshot, profile).impacts:
        assert i.change_pct == round((i.before - i.after) / i.before * 100)


def test_exercise_shift_when_usual_time_is_smoggy(snapshot, profile):
    plan = build_plan(snapshot, profile)
    keys = {i.key for i in plan.impacts}
    assert {"imp_exercise", "imp_commute", "imp_mask", "imp_windows", "imp_purifier"} <= keys


def test_no_exercise_means_no_exercise_tip(snapshot, profile):
    plan = build_plan(snapshot, replace(profile, exercise=Exercise.NONE))
    assert "imp_exercise" not in {i.key for i in plan.impacts}


def test_staying_home_means_no_commute_or_mask(snapshot, profile):
    plan = build_plan(snapshot, replace(profile, commute=Commute.NONE))
    assert not {"imp_commute", "imp_mask"} & {i.key for i in plan.impacts}


def test_already_at_best_time(snapshot, profile):
    best_hour = build_plan(snapshot, profile).best_window.start.hour
    plan = build_plan(snapshot, replace(profile, exercise_hour=best_hour))
    assert any("already" in t.title for t in plan.section("routine"))


def _flat(snapshot: AirSnapshot, pm25: float) -> AirSnapshot:
    rows = tuple(Reading(r.time, pm25) for r in snapshot.forecast)
    return AirSnapshot(snapshot.city, Reading(snapshot.current.time, pm25), rows, "demo")


def test_clean_air_needs_no_mask(snapshot, profile):
    plan = build_plan(_flat(snapshot, 20), profile)
    assert "imp_mask" not in {i.key for i in plan.impacts}
    assert plan.warnings == ()
    assert plan.category == "good"


def test_severe_air_moves_exercise_indoors_and_warns(snapshot, profile):
    plan = build_plan(_flat(snapshot, 300), profile)
    assert any("indoors" in t.title for t in plan.section("routine"))
    assert plan.warnings and "Severe" in plan.warnings[0]


def test_vulnerable_household_gets_protection_tip(snapshot, profile):
    plan = build_plan(snapshot, profile)
    assert any("children and elders" in t.title for t in plan.section("routine"))
    plan2 = build_plan(snapshot, replace(profile, children=False, elderly=False))
    assert not any("Protect" in t.title for t in plan2.section("routine"))


def test_vulnerable_warning_on_poor_air(snapshot, profile):
    plan = build_plan(_flat(snapshot, 100), profile)  # PM2.5 100 -> AQI 233 "poor"
    assert plan.category == "poor"
    assert plan.warnings and "children" in plan.warnings[0]


@pytest.mark.parametrize("fuel", [Fuel.BIOMASS, Fuel.COAL, Fuel.KEROSENE])
def test_polluting_fuel_gets_switch_and_scheme(snapshot, profile, fuel):
    plan = build_plan(snapshot, replace(profile, fuel=fuel))
    assert any("LPG or induction" in t.title for t in plan.section("indoor"))
    assert any("Ujjwala" in t.title for t in plan.section("sustainable"))


def test_clean_fuel_gets_no_fuel_tip(snapshot, profile):
    plan = build_plan(snapshot, replace(profile, fuel=Fuel.LPG))
    assert not any("Ujjwala" in t.title for t in plan.tips)


def test_waste_burning_vs_reporting(snapshot, profile):
    assert build_plan(snapshot, profile).section("sustainable")[0].title.startswith("Stop burning")
    plan = build_plan(snapshot, replace(profile, burns_waste=False))
    assert any("Report" in t.title for t in plan.section("sustainable"))


@pytest.mark.parametrize(
    ("mode", "expect"), [(Commute.CAR, "Share rides"), (Commute.WALK, "clean way"), (Commute.BUS, "clean way")]
)
def test_transport_advice_fits_the_mode(snapshot, profile, mode, expect):
    plan = build_plan(snapshot, replace(profile, commute=mode))
    assert any(expect in t.title for t in plan.section("sustainable"))


def test_owned_purifier_uses_its_cadr(snapshot, profile):
    plan = build_plan(snapshot, replace(profile, has_purifier=True, purifier_cadr=300))
    tip = next(t for t in plan.section("indoor") if t.impact and t.impact.key == "imp_purifier")
    assert "300 m³/h" in tip.title or "300 m³/h" in tip.detail


def test_sections_sorted_by_priority(snapshot, profile):
    plan = build_plan(snapshot, profile)
    for name in ("routine", "indoor", "sustainable"):
        priorities = [t.priority for t in plan.section(name)]
        assert priorities == sorted(priorities)


def test_city_note_for_dhanbad(snapshot, profile):
    assert "Jharia" in build_plan(snapshot, profile).city_note
    assert build_plan(snapshot, replace(profile, city="Ranchi")).city_note == ""


@pytest.mark.parametrize("lang", list(Lang))
def test_every_language_renders_without_leftover_placeholders(snapshot, profile, lang):
    plan = build_plan(snapshot, replace(profile, lang=lang))
    for tip in plan.tips:
        assert not re.search(r"\{\w+\}", tip.title + tip.detail)


def test_plan_is_deterministic(snapshot, profile):
    assert build_plan(snapshot, profile) == build_plan(snapshot, profile)


def test_short_forecast_still_gives_a_plan(snapshot, profile):
    short = AirSnapshot(snapshot.city, snapshot.current, snapshot.forecast[:2], "demo")
    plan = build_plan(short, profile)
    assert plan.section("indoor")  # still useful advice


def test_impact_numbers_appear_in_tip_text(snapshot, profile):
    for tip in build_plan(snapshot, profile).tips:
        if tip.impact and tip.impact.key in {"imp_exercise", "imp_commute"}:
            assert f"{tip.impact.change_pct}%" in tip.detail
        if tip.impact and tip.impact.key == "imp_mask":
            assert f"{tip.impact.before:g}" in tip.detail


def test_best_window_is_within_forecast(snapshot, profile):
    plan = build_plan(snapshot, profile)
    times = {r.time for r in snapshot.forecast}
    assert plan.best_window.start in times
    assert plan.best_window.start - snapshot.current.time <= timedelta(hours=24)
