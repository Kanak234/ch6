# PRD — Saans Saathi (PromptWars Virtual, Challenge 06: Urban Air Quality Assistant)

## Problem
Every winter, smog in Indian towns peaks at night and early morning (temperature inversion + chulha smoke + traffic) and eases in the afternoon. Families don't know *when* the air is cleanest, *what* actually helps at home, or *how much* any change matters. AQI apps show a number; they don't turn it into a plan.

## Goal
A GenAI assistant that helps a family get through smog season by:
1. suggesting a **low-exposure daily routine** (when to go out, how to travel),
2. giving **indoor air** improvement tips,
3. offering **sustainable alternatives** that fit their place and lifestyle,
4. explaining the **direct impact of each choice** with real, traceable numbers.

### Non-goals
- Medical diagnosis or medicine advice (we point to a doctor / 112).
- Storing user data, accounts, or tracking.
- Making up numbers: the AI never produces data.

## Users
- Families in Jharkhand towns (Hazaribagh, Ranchi, Dhanbad, Bokaro, Jamshedpur) and other smog cities — parents of small children, people caring for elders or someone with asthma.
- Reads English, हिंदी or Hinglish; often on a phone; may have a slow connection.

## Features & exact behaviour
| # | Feature | Behaviour |
|---|---|---|
| F1 | Location | Preset city list or exact lat/lon (validated inside India, rounded to 2 decimals). |
| F2 | Household profile (≈30 s) | Children / elderly / respiratory illness, travel mode + minutes + usual hour, exercise type + minutes + usual hour, cooking fuel, burns waste, incense/coils, purifier + CADR, room size. |
| F3 | Live air data | Google Air Quality API (if key + billing) → Open-Meteo free CAMS forecast (no key) → deterministic demo data **labelled "Demo data (not live)" with the reasons**. Source always shown. |
| F4 | AQI | CPCB National AQI computed from PM2.5/PM10 (labelled "PM-based estimate"). Colour badge always carries the text category. |
| F5 | Routine | Cleanest daytime slot (05:00–21:00 only) for the user's exercise and commute vs. their usual hour; shift suggested only if it saves ≥5 %. Very Poor+ air → "exercise indoors". N95 tip when the trip is in Poor+ air. Extra protection tip if vulnerable people live at home. |
| F6 | Indoor | Windows shut at peak vs open (mass-balance model); purifier effect (owned CADR, or the EPA/ENERGY STAR 4.8 ACH recommended size); polluting fuel → LPG/induction; incense/coils; wet mopping. |
| F7 | Sustainable | Waste burning → SWM Rules 2016 + compost; otherwise report via Sameer app; vehicle → ride-share/bus/e-rickshaw; polluting fuel → Ujjwala Yojana; local city note (e.g. Dhanbad/Jharia). |
| F8 | Impact table | Every measurable choice: before → after, unit, % reduction, with sources. Chart + identical table. |
| F9 | AI briefing + Q&A | Gemini writes a short briefing (and answers an optional question) **only from a fact sheet**. Number guard rejects any reply containing a number not in the facts → offline summary. |
| F10 | Languages | English, हिंदी (Devanagari), Hinglish (Roman). Switching keeps the plan. |
| F11 | Accessibility | Large-text toggle, WCAG-AA badge contrast, every chart duplicated as a table, labelled inputs, keyboard-usable forms. |

## Edge cases
- No API keys → app fully works on demo data + offline briefing.
- Forecast shorter than 6 h → treated as failure → demo.
- Cleanest slot is tomorrow → window text includes the date (`27/11 14:00–14:59`).
- Clean air → no mask tip, no warnings; "already at best time" when habits are fine.
- Purifier ticked with CADR 0 → validation error.
- Gemini returns invalid JSON / times out / invents a number → offline briefing with the reason.

## Acceptance criteria
- All four challenge requirements produced for a typical profile (tested).
- Every impact has `after ≤ before`, a source list, and a % that matches its numbers (tested).
- Every language has every key and the same placeholders (tested).
- Gemini output with an unverified number is never shown (tested).
- `ruff check`, `ruff format --check`, `pytest` all pass in CI.
