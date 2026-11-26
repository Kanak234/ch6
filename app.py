"""Saans Saathi — Streamlit user interface.

This file only does UI. All logic lives in the `saans` package so it can be
tested without a browser.
Flow: sidebar form -> validation.build_profile -> cached air data (Google / demo)
      -> advisor.build_plan -> cached Gemini briefing -> 6 tabs
"""

from __future__ import annotations

import base64
import html
import json
import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import streamlit as st

from saans.advisor import build_plan
from saans.ai import Briefing, GeminiGenerator, TextGenerator, generate_briefing
from saans.aqi import category_for, naqi
from saans.constants import (
    ACH_CLOSED,
    ACH_OPEN,
    CEILING_M,
    CITIES,
    DEFAULT_CITY,
    DEFAULT_MODELS,
    DEPOSITION_PER_H,
    IST,
    PENETRATION,
)
from saans.data import get_snapshot
from saans.exposure import fmt_window
from saans.i18n import LANG_NAMES, t
from saans.models import AirSnapshot, Commute, Exercise, Fuel, Lang, Plan, Tip
from saans.prompts import build_facts
from saans.sources import SOURCES
from saans.validation import build_profile, clean_question

ASSETS = Path(__file__).parent / "assets"

# Must be the first Streamlit call. Tab title + favicon.
st.set_page_config(page_title="Saans Saathi — Urban Air Quality Assistant", page_icon="🌬️", layout="wide")


# ---------- Secrets & cached resources (efficiency + security) -----------------
def _secret(name: str) -> str:
    """Read a secret from Streamlit secrets or env vars — never hard-coded, never sent to the browser."""
    try:
        value = st.secrets.get(name, "")
    except Exception:  # no secrets.toml locally -> fall back to environment
        value = ""
    return str(value or os.environ.get(name, ""))


@st.cache_resource(show_spinner=False)
def get_generator() -> TextGenerator | None:
    """Create the Gemini client ONCE per server process, not on every rerun."""
    key = _secret("GEMINI_API_KEY")
    if not key:
        return None
    model = _secret("GEMINI_MODEL")
    return GeminiGenerator(key, (model, *DEFAULT_MODELS) if model else DEFAULT_MODELS)


class LiveDataUnavailableError(RuntimeError):
    """Raised inside the cached function so a DEMO result is never cached."""

    def __init__(self, snapshot: AirSnapshot) -> None:
        super().__init__(snapshot.note)
        self.snapshot = snapshot


@st.cache_data(show_spinner=False, ttl=1800, max_entries=256)
def _cached_live_snapshot(city: str, lat: float, lon: float, hour_key: str) -> AirSnapshot:
    """LIVE air data per (rounded location, hour) — Google or Open-Meteo.

    `hour_key` makes the cache roll over every hour, so each source is called at
    most twice an hour per place. Streamlit never caches a function that raises,
    so a demo fallback (temporary outage) is retried on the next run instead of
    being stuck for 30 minutes.
    """
    del hour_key  # only part of the cache key
    snapshot = get_snapshot(city, lat, lon, _secret("GOOGLE_MAPS_API_KEY"), datetime.now(IST))
    if snapshot.source == "demo":
        raise LiveDataUnavailableError(snapshot)
    return snapshot


def cached_snapshot(city: str, lat: float, lon: float, hour_key: str) -> AirSnapshot:
    """Live data from the cache when possible; uncached, labelled demo data otherwise."""
    try:
        return _cached_live_snapshot(city, lat, lon, hour_key)
    except LiveDataUnavailableError as exc:
        return exc.snapshot


class AIUnavailableError(RuntimeError):
    """Raised inside the cached function so a failed AI call is NOT cached."""


@st.cache_data(show_spinner=False, ttl=3600, max_entries=256)
def gemini_briefing(facts_key: str, question: str, _plan: Plan, _generator: TextGenerator) -> Briefing:
    """Same facts + same question -> reuse Gemini's answer for an hour.

    Streamlit never caches a function that raises, so only SUCCESSFUL answers
    are stored. Leading underscores tell Streamlit not to hash those arguments.
    """
    del facts_key  # only part of the cache key
    result = generate_briefing(_plan, question, _generator)
    if result.source != "gemini":
        raise AIUnavailableError(result.reason_key)
    return result


def get_briefing(plan: Plan, question: str) -> Briefing:
    generator = get_generator()
    if generator is None:
        return generate_briefing(plan, question, None)
    facts_key = json.dumps(build_facts(plan), sort_keys=True, ensure_ascii=False) + plan.profile.lang.value
    try:
        return gemini_briefing(facts_key, question, plan, generator)
    except AIUnavailableError as exc:
        # Show the real reason (Gemini down vs. number guard) on the offline briefing.
        reason = exc.args[0] if exc.args else "ai_reason_failed"
        return replace(generate_briefing(plan, question, None), reason_key=reason)


@st.cache_data(show_spinner=False)
def logo_data_uri() -> str:
    """Inline the KP watermark as a data URI (one less network request)."""
    return "data:image/svg+xml;base64," + base64.b64encode((ASSETS / "logo-mark.svg").read_bytes()).decode()


# ---------- UI pieces ----------------------------------------------------------
def lang_and_display() -> Lang:
    """Language + large-text toggle sit OUTSIDE the form so they apply instantly."""
    with st.sidebar:
        lang = st.selectbox(
            "Language / भाषा / Bhasha",
            list(Lang),
            format_func=lambda x: LANG_NAMES[x],
            key="lang",
        )
        if st.toggle(t(lang, "large_text"), key="large_text"):
            # Our own constant CSS only — no user text is ever injected here.
            st.markdown(
                "<style>html, body, [class*='st-'] p, li, label {font-size: 1.2rem !important;}</style>",
                unsafe_allow_html=True,
            )
    return lang


def render_form(lang: Lang) -> None:
    """Sidebar form. Stores a validated Profile in session_state on submit."""
    with st.sidebar:
        st.header(t(lang, "form_header"))
        with st.form("household", border=False):
            city = st.selectbox(t(lang, "city"), list(CITIES), index=list(CITIES).index(DEFAULT_CITY), key="city")
            use_custom = st.checkbox(t(lang, "custom_loc"), key="use_custom")
            col1, col2 = st.columns(2)
            preset = CITIES[city]
            lat = col1.number_input(t(lang, "lat"), value=preset.lat, format="%.4f", key="lat")
            lon = col2.number_input(t(lang, "lon"), value=preset.lon, format="%.4f", key="lon")

            st.markdown(f"**{t(lang, 'who_home')}**")
            children = st.checkbox(t(lang, "children"), key="children")
            elderly = st.checkbox(t(lang, "elderly"), key="elderly")
            respiratory = st.checkbox(t(lang, "respiratory"), key="respiratory")

            commute = st.selectbox(
                t(lang, "commute"),
                list(Commute),
                index=4,
                format_func=lambda c: t(lang, f"commute_{c.value}"),
                key="commute",
            )
            commute_minutes = st.number_input(t(lang, "commute_minutes"), 0, 240, 30, 5, key="commute_minutes")
            commute_hour = st.number_input(t(lang, "commute_hour"), 0, 23, 9, key="commute_hour")

            exercise = st.selectbox(
                t(lang, "exercise"),
                list(Exercise),
                format_func=lambda e: t(lang, f"exercise_{e.value}"),
                key="exercise",
            )
            exercise_minutes = st.number_input(t(lang, "exercise_minutes"), 0, 240, 30, 5, key="exercise_minutes")
            exercise_hour = st.number_input(t(lang, "exercise_hour"), 0, 23, 6, key="exercise_hour")

            fuel = st.selectbox(
                t(lang, "fuel"), list(Fuel), format_func=lambda f: t(lang, f"fuel_{f.value}"), key="fuel"
            )
            st.markdown(f"**{t(lang, 'habits')}**")
            burns_waste = st.checkbox(t(lang, "burns_waste"), key="burns_waste")
            burns_incense = st.checkbox(t(lang, "burns_incense"), key="burns_incense")
            has_purifier = st.checkbox(t(lang, "has_purifier"), key="has_purifier")
            cadr = st.number_input(t(lang, "cadr"), 0, 2000, 0, 10, key="cadr")
            room = st.number_input(t(lang, "room_area"), 4.0, 120.0, 12.0, 1.0, key="room")
            submitted = st.form_submit_button(t(lang, "submit"), type="primary", use_container_width=True)

    if submitted:
        profile, errors = build_profile(
            city=city,
            lat=lat if use_custom else None,
            lon=lon if use_custom else None,
            lang=lang.value,
            children=children,
            elderly=elderly,
            respiratory=respiratory,
            commute=commute.value,
            commute_minutes=commute_minutes,
            commute_hour=commute_hour,
            exercise=exercise.value,
            exercise_minutes=exercise_minutes,
            exercise_hour=exercise_hour,
            fuel=fuel.value,
            burns_waste=burns_waste,
            burns_incense=burns_incense,
            has_purifier=has_purifier,
            purifier_cadr=cadr,
            room_area_m2=room,
        )
        for key in errors:
            st.sidebar.error(t(lang, key), icon="⚠️")
        if profile:
            st.session_state["form"] = profile


def aqi_badge(plan: Plan) -> str:
    """Coloured badge that ALSO spells out the category (meaning never by colour alone)."""
    lang, cat = plan.profile.lang, category_for(plan.aqi_now)
    return (
        f'<div role="status" style="background:{cat.color};color:{cat.text_color};padding:.6rem 1rem;'
        f'border-radius:.6rem;font-weight:700;display:inline-block">'
        f"AQI {plan.aqi_now} — {html.escape(t(lang, cat.key))} · {html.escape(plan.profile.city)}</div>"
    )


def render_status(plan: Plan) -> None:
    lang, snap = plan.profile.lang, plan.snapshot
    st.markdown(aqi_badge(plan), unsafe_allow_html=True)  # safe: constants + html.escape'd text
    if snap.source in {"google", "open_meteo"}:
        st.caption("✅ " + t(lang, f"src_{snap.source}"))
    else:
        st.warning(t(lang, "src_demo", reason=snap.note or "offline"), icon="ℹ️")
    cols = st.columns(4)
    cols[0].metric(t(lang, "aqi_now"), plan.aqi_now, help=t(lang, plan.category))
    cols[1].metric(t(lang, "pm25_now"), f"{snap.current.pm25:.0f} µg/m³")
    cols[2].metric(t(lang, "best_slot"), fmt_window(plan.best_window) if plan.best_window else t(lang, "no_slot"))
    cols[3].metric(t(lang, "worst_slot"), fmt_window(plan.worst_window) if plan.worst_window else t(lang, "no_slot"))
    for warning in plan.warnings:
        st.error(warning, icon="🚨")
    if plan.city_note:
        st.info(plan.city_note, icon="📍")


def render_tips(tips: tuple[Tip, ...]) -> None:
    icons = {1: "🔴", 2: "🟠", 3: "🟢"}  # paired with text order (most urgent first), not meaning-by-colour
    for tip in tips:
        with st.container(border=True):
            st.markdown(f"#### {icons[tip.priority]} {tip.title}")
            st.markdown(tip.detail)
            if tip.impact:
                i = tip.impact
                st.markdown(f"**{i.before:g} → {i.after:g} {i.unit}** (−{i.change_pct}%)")


def render_forecast(plan: Plan) -> None:
    lang = plan.profile.lang
    rows = plan.snapshot.forecast
    st.subheader(t(lang, "forecast_chart"))
    data = {f"{r.time:%d/%m %H:%M}": r.pm25 for r in rows}
    st.line_chart(data, x_label=t(lang, "time"), y_label=t(lang, "pm25"))
    # The table repeats the chart in text so screen-reader users get the same data.
    with st.expander(t(lang, "forecast_table")):
        st.table(
            {
                t(lang, "time"): list(data),
                t(lang, "pm25"): [f"{v:.0f}" for v in data.values()],
                t(lang, "aqi"): [naqi(r.pm25, r.pm10) for r in rows],
                t(lang, "category"): [t(lang, category_for(naqi(r.pm25, r.pm10)).key) for r in rows],
            }
        )


def render_impact(plan: Plan) -> None:
    lang = plan.profile.lang
    impacts = plan.impacts
    if not impacts:
        st.info(t(lang, "imp_none"))
        return
    st.bar_chart({i.title: i.change_pct for i in impacts}, horizontal=True, y_label=t(lang, "imp_change") + " (%)")
    st.table(
        {
            t(lang, "imp_choice"): [i.title for i in impacts],
            t(lang, "imp_before"): [f"{i.before:g}" for i in impacts],
            t(lang, "imp_after"): [f"{i.after:g}" for i in impacts],
            t(lang, "imp_unit"): [i.unit for i in impacts],
            t(lang, "imp_change"): [f"{i.change_pct}%" for i in impacts],
        }
    )


def render_ask(plan: Plan) -> None:
    lang = plan.profile.lang
    with st.form("ask", border=False):
        question = st.text_input(t(lang, "ask_label"), placeholder=t(lang, "ask_placeholder"), max_chars=300, key="q")
        asked = st.form_submit_button(t(lang, "ask_button"))
    if asked:
        st.session_state["question"] = clean_question(question)
    q = st.session_state.get("question", "")
    with st.spinner("…"):
        brief = get_briefing(plan, q)
    st.subheader(t(lang, "ai_header"))
    if brief.source == "gemini":
        st.caption("✨ " + t(lang, "ai_by_gemini"))
    else:
        st.caption(t(lang, "ai_offline", reason=t(lang, brief.reason_key)))
    st.write(brief.text)
    if q and brief.answer:
        st.markdown(f"**{t(lang, 'answer')}:** {brief.answer}")


def render_method(plan: Plan) -> None:
    lang = plan.profile.lang
    st.markdown(t(lang, "method"))
    st.markdown(f"**{t(lang, 'assumptions')}**")
    st.markdown(
        f"- Penetration P = {PENETRATION:g} · deposition k = {DEPOSITION_PER_H:g}/h · "
        f"air changes: windows shut {ACH_CLOSED:g}/h, open {ACH_OPEN:g}/h · ceiling {CEILING_M:g} m\n"
        "- AQI from hourly PM2.5/PM10 (CPCB uses 24-h averages, so this is an estimate)"
    )
    st.markdown("\n".join(f"- [{title}]({url})" for title, url in SOURCES.values()))


def render_footer(lang: Lang) -> None:
    st.divider()
    with st.expander(t(lang, "privacy_title")):
        st.markdown(t(lang, "privacy"))
    st.markdown(
        f'<img src="{logo_data_uri()}" alt="KP logo — Kanak Prabhakar" width="28" style="vertical-align:middle"> '
        f"{html.escape(t(lang, 'footer'))}",
        unsafe_allow_html=True,  # safe: our own data-URI + escaped constant text
    )


def main() -> None:
    lang = lang_and_display()
    st.title("🌬️ Saans Saathi")
    st.markdown(t(lang, "app_tagline"))
    render_form(lang)
    saved = st.session_state.get("form")
    if saved is None:
        st.info("👈 " + t(lang, "skip_hint"))
        render_footer(lang)
        return
    # Switching language re-renders the same plan in the new language — no need to resubmit.
    profile = replace(saved, lang=lang)
    now = datetime.now(IST)
    with st.spinner("…"):
        snapshot = cached_snapshot(profile.city, profile.lat, profile.lon, now.strftime("%Y%m%d%H"))
        plan = build_plan(snapshot, profile)
    render_status(plan)
    tabs = st.tabs([t(lang, k) for k in ("tab_plan", "tab_indoor", "tab_green", "tab_impact", "tab_ask", "tab_method")])
    with tabs[0]:
        render_tips(plan.section("routine"))
        render_forecast(plan)
    with tabs[1]:
        render_tips(plan.section("indoor"))
    with tabs[2]:
        render_tips(plan.section("sustainable"))
    with tabs[3]:
        render_impact(plan)
    with tabs[4]:
        render_ask(plan)
    with tabs[5]:
        render_method(plan)
    render_footer(lang)


main()
