"""Gemini layer: JSON parsing, the number guard, injection fencing and every fallback path."""

from __future__ import annotations

import json

import pytest

from saans.advisor import build_plan
from saans.ai import generate_briefing, is_grounded, numbers_in, offline_briefing, parse_response
from saans.prompts import SYSTEM_INSTRUCTION, build_facts, build_prompt


@pytest.fixture
def plan(snapshot, profile):
    return build_plan(snapshot, profile)


def _grounded_reply(plan) -> str:
    i = plan.impacts[0]
    text = (
        f"Air in {plan.profile.city} is AQI {plan.aqi_now} now. "
        f"{i.title}: {i.before:g} to {i.after:g}, {i.change_pct}% less."
    )
    return json.dumps({"briefing": text, "answer": "Wear an N95 and check PM2.5 before you go."})


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("AQI 191 and 59%", {191.0, 59.0}),
        ("PM2.5 is 88.5", {2.5, 88.5}),
        ("AQI १९१ है", {191.0}),  # Devanagari digits are still numbers
        ("about 1,200 µg", {1200.0}),  # thousands separator can't dodge the guard
        ("in µg/m³ and m²", set()),  # superscripts are units, not numbers
    ],
)
def test_numbers_in(text, expected):
    assert numbers_in(text) == expected


def test_guard_accepts_numbers_from_facts(plan):
    facts = build_facts(plan)
    assert is_grounded(f"AQI {plan.aqi_now}, call 112, wear N95, PM2.5 and PM10", facts)


def test_guard_rejects_invented_number(plan):
    assert not is_grounded("Your risk drops by 73.3 percent", build_facts(plan))


@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "[]",
        json.dumps({"briefing": 5, "answer": ""}),
        json.dumps({"answer": "x"}),
        json.dumps({"briefing": "", "answer": ""}),
    ],
)
def test_parse_response_rejects_bad_output(raw):
    assert parse_response(raw) is None


def test_parse_response_strips_fences_and_html():
    raw = '```json\n{"briefing": "<b>Hello</b> world", "answer": ""}\n```'
    assert parse_response(raw) == ("Hello world", "")


def test_no_key_gives_offline_briefing(plan):
    brief = generate_briefing(plan, "", None)
    assert brief.source == "offline" and brief.reason_key == "ai_reason_no_key"
    assert str(plan.aqi_now) in brief.text


def test_offline_answer_only_when_asked(plan):
    assert generate_briefing(plan, "", None).answer == ""
    assert generate_briefing(plan, "Can kids play?", None).answer


def test_gemini_success(plan, fake_generator):
    gen = fake_generator(_grounded_reply(plan))
    brief = generate_briefing(plan, "Is it safe?", gen)
    assert brief.source == "gemini" and "AQI" in brief.text
    assert len(gen.prompts) == 1


def test_gemini_exception_falls_back(plan, fake_generator):
    brief = generate_briefing(plan, "", fake_generator(error=TimeoutError()))
    assert brief.source == "offline" and brief.reason_key == "ai_reason_failed"


def test_gemini_bad_json_falls_back(plan, fake_generator):
    assert generate_briefing(plan, "", fake_generator("sorry, no json")).reason_key == "ai_reason_failed"


def test_number_guard_blocks_hallucination(plan, fake_generator):
    reply = json.dumps({"briefing": "Your lungs will be 37.7% healthier.", "answer": ""})
    brief = generate_briefing(plan, "", fake_generator(reply))
    assert brief.source == "offline" and brief.reason_key == "ai_reason_guard"


def test_guard_also_checks_the_answer(plan, fake_generator):
    reply = json.dumps({"briefing": f"AQI {plan.aqi_now}.", "answer": "Go out at 4:45 pm exactly."})
    assert generate_briefing(plan, "when?", fake_generator(reply)).reason_key == "ai_reason_guard"


def test_question_is_fenced_as_data(plan):
    prompt = build_prompt(build_facts(plan), "what about tonight?", plan.profile.lang)
    assert "<question>what about tonight?</question>" in prompt
    assert "FACTS:" in prompt


def test_prompt_requests_language_and_script(plan):
    from dataclasses import replace

    from saans.models import Lang

    hi = replace(plan, profile=replace(plan.profile, lang=Lang.HI))
    assert "Devanagari" in build_prompt(build_facts(hi), "", Lang.HI)
    assert "Roman" in build_prompt(build_facts(hi), "", Lang.HINGLISH)


def test_facts_contain_no_coordinates_or_free_text(plan):
    facts_text = json.dumps(build_facts(plan))
    assert str(plan.profile.lat) not in facts_text and str(plan.profile.lon) not in facts_text


def test_facts_carry_every_impact(plan):
    assert len(build_facts(plan)["impacts"]) == len(plan.impacts)


def test_system_instruction_has_core_rules():
    for rule in ("ONLY numbers", "not a doctor", "112", "<question>", "JSON"):
        assert rule in SYSTEM_INSTRUCTION


def test_offline_briefing_is_itself_grounded(plan):
    assert is_grounded(offline_briefing(plan), build_facts(plan))
