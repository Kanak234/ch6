"""End-to-end UI runs with Streamlit's AppTest (no browser, no network, no keys)."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from saans import data
from saans.data import AirDataError

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def _offline(url, params):
    raise AirDataError("offline in tests")


@pytest.fixture
def app(monkeypatch):
    for key in ("GEMINI_API_KEY", "GOOGLE_MAPS_API_KEY", "GEMINI_MODEL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(data, "http_get_json", _offline)  # no network: Open-Meteo "down"
    return AppTest.from_file(APP, default_timeout=60).run()


def _submit(at):
    at.sidebar.button[0].click().run()
    return at


def test_starts_with_hint(app):
    assert not app.exception
    assert "Make my plan" in app.info[0].value


def test_submit_builds_full_plan(app):
    _submit(app)
    assert not app.exception
    assert len(app.tabs) == 6
    assert any("AQI now" in m.label for m in app.metric)


def test_demo_data_is_clearly_labelled(app):
    _submit(app)
    assert any("Demo data (not live)" in w.value for w in app.warning)


def test_offline_briefing_explains_why(app):
    _submit(app)
    assert any("no Gemini key" in c.value for c in app.caption)


def test_invalid_input_shows_error(app):
    app.sidebar.checkbox(key="has_purifier").check()
    _submit(app)
    assert any("CADR" in e.value for e in app.sidebar.error)


def test_language_switch_keeps_plan(app):
    _submit(app)
    app.sidebar.selectbox(key="lang").select_index(1).run()
    assert not app.exception
    assert any("AQI" in m.label and "अभी" in m.label for m in app.metric)


def test_vulnerable_city_flow(app):
    app.sidebar.selectbox(key="city").select("Dhanbad")
    app.sidebar.checkbox(key="children").check()
    _submit(app)
    assert not app.exception
    assert any("Jharia" in i.value for i in app.info)


def test_ask_question_offline(app):
    _submit(app)
    app.text_input(key="q").input("Can my kids play outside?")
    next(b for b in app.button if b.label == "Ask").click().run()
    assert not app.exception
    assert any("Gemini is not available" in m.value for m in app.markdown)


def test_live_open_meteo_is_labelled(monkeypatch):
    from conftest import FakeGet, open_meteo_payload

    for key in ("GEMINI_API_KEY", "GOOGLE_MAPS_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    from datetime import datetime

    from saans.constants import IST

    today = datetime.now(IST).strftime("%Y-%m-%dT00:00")
    monkeypatch.setattr(data, "http_get_json", FakeGet(open_meteo_payload(start_iso=today)))
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    at.sidebar.selectbox(key="city").select("Bokaro")  # different cache key from the offline tests
    at.sidebar.button[0].click().run()
    assert not at.exception
    assert any("Open-Meteo" in c.value for c in at.caption)
