<div align="center">

# 🌬️ Saans Saathi

**GenAI urban air-quality assistant for winter smog.**
A daily low-exposure routine · cleaner indoor air · greener choices · and the *measured* impact of every choice — in English, हिंदी and Hinglish.

[![CI](https://github.com/Kanak234/ch6/actions/workflows/ci.yml/badge.svg)](https://github.com/Kanak234/ch6/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-212%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

*PromptWars Virtual — Challenge 06: Urban Air Quality Assistant*

[**▶ Live app**](https://ip3kzexavzt7s3mfizlc5c.streamlit.app)

</div>

---

## The problem

In Indian towns, winter smog is worst at night and early morning (temperature inversion traps chulha smoke and traffic exhaust) and eases in the afternoon. Families see an AQI number but not a plan: **when** is it safe to walk, **what** actually helps at home, and **how much** does any change matter?

## What Saans Saathi does — mapped to the challenge brief

| Challenge asks for | How Saans Saathi delivers it | Code |
|---|---|---|
| **Low-exposure daily routine** | Finds the cleanest daytime slot (05:00–21:00) in the hourly forecast for *your* exercise and commute, compares it with *your* usual hour, and only suggests a shift if it saves ≥ 5 %. Very Poor air → exercise indoors. N95 tip when the trip is in Poor+ air. Extra protection for children, elders and anyone with asthma. | `saans/advisor.py`, `saans/exposure.py` |
| **Indoor air improvement** | Windows shut at peak vs open, purifier effect (your CADR, or the right size for your room), chulha/coal/kerosene → LPG/induction, agarbatti & coils, wet mopping. | `saans/advisor.py` |
| **Sustainable alternatives for location & lifestyle** | Waste-burning → SWM Rules 2016 + composting (or report via CPCB's Sameer app), bike/car → ride-share / bus / e-rickshaw, Ujjwala Yojana for LPG, local notes (e.g. Dhanbad's Jharia coalfield). | `saans/advisor.py`, `saans/constants.py` |
| **Direct impact of each choice** | Every measurable choice shows **before → after** with a % and its sources, as a chart *and* a table. Computed with standard exposure-science formulas — never guessed. | `saans/exposure.py`, `saans/sources.py` |
| **GenAI** | Google **Gemini** turns the computed plan into a short, warm briefing and answers your questions in your language — fed **only** a fact sheet. | `saans/ai.py`, `saans/prompts.py` |

**Example** (Dhanbad, demo data, family with kids + grandparent, bike commute at 08:00, walk at 06:00):

| Choice | Before | After | Reduction |
|---|---|---|---|
| Walk at the cleanest time | 63 µg inhaled | 26 µg | **59 %** |
| Commute at the cleanest time | 61 µg | 26 µg | **57 %** |
| Well-fitted N95 on the bike | 61 µg | 3 µg | **95 %** (best case) |
| Windows shut during peak smog | 167 µg/m³ indoors | 127 µg/m³ | **24 %** |
| Right-sized purifier (156 m³/h) | 127 µg/m³ | 16 µg/m³ | **87 %** |

## Why it's built this way

- **Numbers from code, words from Gemini.** Doses use *concentration × breathing rate × time* (US EPA); indoor air uses the standard single-room mass balance; AQI uses CPCB's own breakpoints (tested against CPCB's worked examples). Gemini only explains.
- **Number guard.** Every number in Gemini's reply must already exist in our fact sheet — Devanagari digits and `1,200`-style formatting included. One invented number → the reply is discarded and our own summary is shown. Health advice with a made-up figure is worse than no AI.
- **Live data with no paid key.** Three tiers: **Google Air Quality API** (if a key with billing is set) → **Open-Meteo** (free, no key — Copernicus CAMS forecast) → deterministic demo data **labelled "Demo data (not live)" with the reason**. The source is always shown on screen.
- **Never breaks, never pretends.** No key, quota, timeout or bad data → the next tier, and an offline briefing that says why if Gemini is unavailable.
- **Google services.** Google Gemini (JSON mode, model fallback list), Google Air Quality API (current + 96-h hourly forecast, first-choice data source), optional Cloud Run `Dockerfile`.
- **Efficient.** Gemini client created once (`st.cache_resource`); air data cached per rounded location per hour; Gemini replies cached for an hour and failures never cached; lazy SDK import; only **two** runtime dependencies (stdlib `urllib` for HTTP).
- **Secure.** Keys only in secrets/env; Air Quality key in a header, never a URL; inputs normalised, HTML/zero-width stripped, prompt-injection phrases neutralised, user question fenced as data; model output parsed, cleaned, length-capped and guarded; no user HTML rendered; XSRF on; non-root container.
- **Private.** No account, no cookies, nothing stored. Coordinates rounded to ~1 km; the Gemini fact sheet has no name or coordinates.
- **Accessible.** Three languages (switching keeps your plan), large-text toggle, WCAG-AA contrast on every AQI badge (tested), every chart repeated as a table, category always in words (never colour alone), labelled keyboard-friendly forms.

```
app.py (UI only)
  ├─ validation.build_profile ─► Profile
  ├─ data.get_snapshot ─► Google Air Quality API ─► Open-Meteo (free) ─► labelled demo
  ├─ advisor.build_plan ─► aqi · exposure · i18n ─► Plan (tips + impacts)
  └─ ai.generate_briefing ─► Gemini (1 JSON call) ─► number guard ─► (fallback: offline)
```

## Run locally

```bash
git clone https://github.com/Kanak234/ch6 && cd ch6 && pip install -r requirements-dev.txt && streamlit run app.py
```
Keys go in `.streamlit/secrets.toml` (see `secrets.toml.example`): `GEMINI_API_KEY` ([Google AI Studio](https://aistudio.google.com/apikey)) for the briefing. Live air data works **without any key** via Open-Meteo; add an optional `GOOGLE_MAPS_API_KEY` (Air Quality API enabled, billing on) to use Google's data first.

**Cloud Run:** `gcloud run deploy saans-saathi --source . --region asia-south1 --set-secrets GEMINI_API_KEY=gemini-key:latest,GOOGLE_MAPS_API_KEY=maps-key:latest`

## Tests & quality

```bash
ruff check . && ruff format --check . && pytest
```
**212 tests** (~3 s, fully offline): CPCB breakpoints and category edges, WCAG contrast of every badge, input cleaning & injection stripping, dose / mass-balance / time-window physics, both air-data clients with fake HTTP layers (Google request shape, key never in URL, Open-Meteo parsing & null hours, Google → Open-Meteo → demo fallback order), the rule engine for every requirement and household type, all 3 languages (same keys, same placeholders, no leftovers), Gemini parsing / number guard / every fallback with a fake model, and end-to-end UI runs with Streamlit `AppTest`. CI runs on every push.

## Sources

CPCB National AQI (2014) · Google Air Quality API · Open-Meteo Air Quality API (Copernicus CAMS data) · US EPA Exposure Factors Handbook Ch. 6 & 19 · US EPA ExpoBox · US EPA Guide to Air Cleaners in the Home · ENERGY STAR room air cleaners · CDC/NIOSH N95 · WHO household air pollution fact sheet · Pradhan Mantri Ujjwala Yojana · Solid Waste Management Rules 2016 — full links in the app's **Sources & method** tab and `saans/sources.py`.

## Project docs

[PRD](project-docs/PRD.md) · [TRD](project-docs/TRD.md) · [UI/UX brief](project-docs/DESIGN.md)

## Author

Built by **Kanak Prabhakar** — BCA, AISECT University, Hazaribagh · [GitHub](https://github.com/Kanak234) · YouTube: *Cooding with Kanak*

> Saans Saathi gives general guidance, not medical advice. In an emergency call 112.

MIT License
