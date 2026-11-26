"""Where every number comes from — shown in the app's "Sources & method" tab.

Why: an "impact" number without a source is just an opinion. Each Impact
carries keys from this dict, so the UI can list the exact references behind it.
Flow: constants.py (values) + advisor.py (Impact.sources) -> app.py (links).
"""

from __future__ import annotations

SOURCES: dict[str, tuple[str, str]] = {
    "cpcb_naqi": (
        "CPCB — National Air Quality Index report (2014): breakpoints & categories",
        "https://smartnet.niua.org/sites/default/files/resources/Air%20Quality%20Index.pdf",
    ),
    "google_aq": (
        "Google Air Quality API — current conditions & 96-hour hourly forecast",
        "https://developers.google.com/maps/documentation/air-quality/forecast",
    ),
    "open_meteo": (
        "Open-Meteo Air Quality API — free hourly PM2.5/PM10 forecast (non-commercial use)",
        "https://open-meteo.com/en/docs/air-quality-api",
    ),
    "cams": (
        "Copernicus Atmosphere Monitoring Service (CAMS) — the forecast model behind Open-Meteo",
        "https://atmosphere.copernicus.eu/",
    ),
    "epa_efh6": (
        "US EPA Exposure Factors Handbook, Ch. 6 — breathing rates by activity",
        "https://www.epa.gov/expobox/exposure-factors-handbook-chapter-6",
    ),
    "epa_expobox": (
        "US EPA ExpoBox — inhaled dose = concentration × breathing rate × time",
        "https://www.epa.gov/expobox/exposure-assessment-tools-routes-inhalation",
    ),
    "epa_efh19": (
        "US EPA Exposure Factors Handbook, Ch. 19 — home air-exchange rates",
        "https://www.epa.gov/expobox/exposure-factors-handbook-chapter-19",
    ),
    "epa_air_cleaners": (
        "US EPA — Guide to Air Cleaners in the Home (CADR sizing)",
        "https://www.epa.gov/indoor-air-quality-iaq/guide-air-cleaners-home",
    ),
    "energy_star": (
        "ENERGY STAR — choose a purifier giving ≥ 4.8 air changes per hour",
        "https://www.energystar.gov/products/ask-the-experts/how-choose-room-air-cleaner",
    ),
    "niosh_n95": (
        "CDC / NIOSH — N95 respirators filter at least 95 % of airborne particles",
        "https://www.cdc.gov/niosh/ppe/respirators/ffr.html",
    ),
    "who_hap": (
        "WHO — Household air pollution fact sheet (2.9 million deaths a year, 2021)",
        "https://www.who.int/news-room/fact-sheets/detail/household-air-pollution-and-health",
    ),
    "pmuy": (
        "Pradhan Mantri Ujjwala Yojana — LPG connections for eligible households",
        "https://pmuy.gov.in/",
    ),
    "swm_2016": (
        "Solid Waste Management Rules, 2016 — no burning of waste in the open",
        "https://www.downtoearth.org.in/news/solid-waste-management-rules-2016-53443",
    ),
}
