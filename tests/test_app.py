"""End-to-end UI runs with Streamlit's AppTest (no browser, no network, no keys)."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def app(monkeypatch):
    for key in ("GEMINI_API_KEY", "GOOGLE_MAPS_API_KEY", "GEMINI_MODEL"):
        monkeypatch.delenv(key, raising=False)
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
