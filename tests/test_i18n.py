"""Every language has every key, with the same placeholders — a missing translation fails CI."""

from __future__ import annotations

import string

import pytest

from saans.i18n import LANG_NAMES, STRINGS, t
from saans.models import Lang


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("lang", [Lang.HI, Lang.HINGLISH])
def test_same_keys_as_english(lang):
    assert set(STRINGS[lang]) == set(STRINGS[Lang.EN])


@pytest.mark.parametrize("lang", [Lang.HI, Lang.HINGLISH])
def test_same_placeholders_as_english(lang):
    for key, english in STRINGS[Lang.EN].items():
        assert _fields(STRINGS[lang][key]) == _fields(english), key


def test_hindi_uses_devanagari_and_hinglish_uses_roman():
    assert any("ऀ" <= ch <= "ॿ" for ch in STRINGS[Lang.HI]["submit"])
    assert all(ord(ch) < 0x0900 for ch in STRINGS[Lang.HINGLISH]["submit"])


def test_t_formats_and_falls_back():
    assert t(Lang.EN, "brief_headline", city="Ranchi", aqi=150, category="Moderate").startswith("Ranchi: AQI 150")
    assert t(Lang.HI, "no-such-key") == "no-such-key"


def test_language_names():
    assert set(LANG_NAMES) == set(Lang)
