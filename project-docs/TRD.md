# TRD — Saans Saathi

## Architecture
```
app.py (Streamlit UI only)
  ├─ validation.build_profile ──► Profile (frozen dataclass)
  ├─ cached_snapshot ──► data.get_snapshot ──► Google Air Quality API  (fallback: labelled demo)
  ├─ advisor.build_plan
  │     ├─ aqi        CPCB NAQI maths
  │     ├─ exposure   inhaled dose + indoor mass balance + time windows
  │     └─ i18n       EN / हिंदी / Hinglish text
  └─ get_briefing ──► ai.generate_briefing ──► Gemini (1 JSON call) ──► number guard ──► fallback
```

## Stack
| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit 1.67 | Single Python codebase, free hosting on Streamlit Community Cloud, built-in `AppTest`. |
| Air data | Google Air Quality API (`currentConditions:lookup`, `forecast:lookup`) | Hourly forecast up to 96 h for any lat/lon in India. |
| GenAI | Google Gemini via `google-genai` | JSON output mode, low temperature for faithful wording. Model list with fallback. |
| HTTP | `urllib` (stdlib) | No extra dependency; timeout 8 s. |
| Tests | pytest + Streamlit AppTest | 195 tests, offline, ~3 s. |
| Lint | ruff (incl. bandit `S` rules) | One fast tool for style + security lint. |
| Deploy | Streamlit Cloud, or Cloud Run via `Dockerfile` | Non-root container, keys from Secret Manager. |

## Models (formulas)
- **CPCB sub-index:** `I = (Ihi−Ilo)/(Chi−Clo)·(C−Clo)+Ilo`, AQI = max sub-index, capped 500.
- **Inhaled dose:** `dose = C × breathing rate × time` (EPA ExpoBox); rates from EPA Exposure Factors Handbook Ch. 6.
- **Indoor:** `C_in = P·a·C_out / (a + k + CADR/V)` with P=1, k=0.2/h, a=0.5/h shut (EFH Ch. 19), 3/h open (assumption), ceiling 2.7 m.
- **Purifier sizing:** CADR ≥ 4.8 × room volume (EPA / ENERGY STAR).
- **N95:** ≥95 % filtration (NIOSH) — shown as *best case*.
All constants live in `saans/constants.py`; assumptions are marked and shown in the app.

## Security
- Keys only in Streamlit secrets / env vars; Air Quality key sent as `X-Goog-Api-Key` header (never in URL).
- All input normalised: control/zero-width chars removed, HTML stripped, prompt-injection phrases neutralised, lengths capped, numbers range-checked.
- User question fenced in `<question>` tags as data; Gemini output parsed as JSON, cleaned, length-capped, then number-guarded.
- No user HTML rendered; only constant HTML + `html.escape`d text. XSRF protection on.
- Coordinates rounded to ~1 km; facts sent to Gemini contain no coordinates or name.

## Performance
- `st.cache_resource`: one Gemini client per process.
- `st.cache_data`: air data per (rounded location, hour) for 30 min; Gemini replies per (facts, question) for 1 h; failures never cached.
- Two runtime dependencies; Gemini SDK imported lazily.

## Failure modes
| Failure | Result |
|---|---|
| No / bad Google key, HTTP error, timeout, malformed JSON, missing PM2.5, short forecast | Demo data with visible reason |
| No Gemini key, timeout, bad JSON | Offline briefing with reason |
| Gemini invents a number | Offline briefing ("couldn't verify") |
