"""Saans Saathi — GenAI urban air-quality assistant.

Package layout (each module does ONE job so it can be tested on its own):
  constants.py  -> every fixed number + where it comes from (single source of truth)
  models.py     -> small frozen dataclasses passed between modules
  aqi.py        -> CPCB National AQI maths (concentration -> index -> category)
  validation.py -> cleans every user input before it reaches maths or the AI prompt
  data.py       -> Google Air Quality API client + clearly-labelled demo fallback
  exposure.py   -> inhaled-dose and indoor mass-balance physics (the "impact" numbers)
  i18n.py       -> English / हिंदी / Hinglish text
  advisor.py    -> turns air data + household profile into the daily plan
  prompts.py    -> Gemini system instruction + fact sheet builder
  ai.py         -> Gemini call, "number guard" grounding check, offline fallback
Flow: app.py -> validation -> data -> advisor (aqi + exposure) -> ai -> back to app.py
"""

__version__ = "1.0.0"
