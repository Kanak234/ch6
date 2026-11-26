"""Gemini integration: grounded briefing + Q&A, with a guard and an offline fallback.

Design:
  * `TextGenerator` is a tiny Protocol — anything with `generate(prompt) -> str`.
    The real one is `GeminiGenerator`; tests pass a fake, so tests never hit the network.
  * The google-genai SDK is imported lazily inside GeminiGenerator, so start-up
    and the offline path stay fast.
  * NUMBER GUARD (the key safety idea): every number in Gemini's reply must
    already exist in the fact sheet we computed. One invented number -> the
    whole reply is discarded and our own rule-based summary is shown instead.
    Health advice with a made-up figure is worse than no AI at all.
  * Output is parsed as JSON, keys checked, strings cleaned and length-capped.
Flow: app.py -> generate_briefing(plan, question, generator) -> Briefing -> "Ask" tab
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol

from .constants import AI_MAX_OUTPUT_TOKENS, AI_TEMPERATURE, AI_TIMEOUT_MS, DEFAULT_MODELS
from .exposure import fmt_window
from .i18n import t
from .models import Plan
from .prompts import RESPONSE_KEYS, SYSTEM_INSTRUCTION, build_facts, build_prompt
from .validation import clean_text

logger = logging.getLogger(__name__)

# Numbers that are part of names or universal facts, not data: PM2.5, PM10, N95,
# India's emergency number 112, "24 hours".
ALWAYS_ALLOWED = frozenset({2.5, 10.0, 95.0, 112.0, 24.0})
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_THOUSANDS_RE = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")


class TextGenerator(Protocol):
    """Anything that turns a prompt into text. Lets us swap Gemini for a fake in tests."""

    def generate(self, prompt: str) -> str: ...


class GeminiGenerator:
    """Thin wrapper around the google-genai SDK.

    Tries each model in `models` until one answers, so a renamed/retired model
    ID doesn't take the whole app down.
    """

    def __init__(self, api_key: str, models: tuple[str, ...] = DEFAULT_MODELS) -> None:
        from google import genai  # lazy import: only paid for when AI is actually used
        from google.genai import types

        self._types = types
        self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=AI_TIMEOUT_MS))
        self._models = models

    def generate(self, prompt: str) -> str:
        config = self._types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=AI_TEMPERATURE,
            max_output_tokens=AI_MAX_OUTPUT_TOKENS,
            response_mime_type="application/json",  # ask Gemini for JSON, not prose
        )
        last_error: Exception | None = None
        for model in self._models:
            try:
                response = self._client.models.generate_content(model=model, contents=prompt, config=config)
                if response.text:
                    return response.text
            except Exception as exc:  # SDK raises many types; log and try the next model
                last_error = exc
                logger.warning("Gemini model %s failed: %s", model, type(exc).__name__)
        raise RuntimeError("All Gemini models failed") from last_error


@dataclass(frozen=True)
class Briefing:
    text: str
    answer: str
    source: str  # "gemini" | "offline"
    reason_key: str = ""  # i18n key explaining why we are offline


def numbers_in(text: str) -> set[float]:
    """All numbers in a text, as floats. Devanagari digits (०-९) become 0-9 first,
    and '1,200' is read as 1200, so the guard can't be dodged by formatting."""
    # isdecimal (not isdigit): superscripts like the ³ in µg/m³ are NOT numbers.
    ascii_text = "".join(str(unicodedata.decimal(ch)) if ch.isdecimal() else ch for ch in text)
    ascii_text = _THOUSANDS_RE.sub("", ascii_text)
    return {float(n) for n in _NUMBER_RE.findall(ascii_text)}


def is_grounded(text: str, facts: dict) -> bool:
    """True if every number in `text` appears in the fact sheet (or is a name like PM2.5)."""
    allowed = numbers_in(json.dumps(facts, ensure_ascii=False)) | ALWAYS_ALLOWED
    return numbers_in(text) <= allowed


def parse_response(raw: str) -> tuple[str, str] | None:
    """Gemini's JSON text -> (briefing, answer); None if unusable."""
    text = raw.strip()
    if text.startswith("```"):  # some models wrap JSON in fences even when asked not to
        text = text.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not all(isinstance(data.get(k), str) for k in RESPONSE_KEYS):
        return None
    briefing = clean_text(data["briefing"], 1200)
    answer = clean_text(data["answer"], 800)
    return (briefing, answer) if briefing else None


def offline_briefing(plan: Plan) -> str:
    """Rule-based summary built only from the plan — the worst-case path never breaks."""
    lang = plan.profile.lang
    lines = [t(lang, "brief_headline", city=plan.profile.city, aqi=plan.aqi_now, category=t(lang, plan.category))]
    if plan.best_window:
        lines.append(t(lang, "brief_best", window=fmt_window(plan.best_window), best=round(plan.best_window.mean_pm25)))
    top = sorted(plan.impacts, key=lambda i: i.change_pct, reverse=True)[:3]
    lines += [
        t(lang, "brief_impact", title=i.title, before=i.before, after=i.after, unit=i.unit, pct=i.change_pct)
        for i in top
    ]
    return " ".join(lines)


def _offline(plan: Plan, question: str, reason_key: str) -> Briefing:
    answer = t(plan.profile.lang, "brief_offline_answer") if question else ""
    return Briefing(offline_briefing(plan), answer, "offline", reason_key)


def generate_briefing(plan: Plan, question: str, generator: TextGenerator | None) -> Briefing:
    """Ask Gemini to explain the plan (and answer the question); fall back on any problem."""
    if generator is None:
        return _offline(plan, question, "ai_reason_no_key")
    facts = build_facts(plan)
    try:
        parsed = parse_response(generator.generate(build_prompt(facts, question, plan.profile.lang)))
    except Exception as exc:  # network, quota, timeout... the user still gets a briefing
        logger.warning("Gemini briefing failed: %s", type(exc).__name__)
        return _offline(plan, question, "ai_reason_failed")
    if parsed is None:
        return _offline(plan, question, "ai_reason_failed")
    briefing, answer = parsed
    if not is_grounded(briefing + " " + answer, facts):
        logger.info("Number guard rejected a Gemini reply")
        return _offline(plan, question, "ai_reason_guard")
    return Briefing(briefing, answer, "gemini")
