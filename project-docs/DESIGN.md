# UI/UX brief — Saans Saathi

**Direction:** calm, clear, trustworthy — a sky-blue, high-contrast theme. One screen answers "what should my family do today?".

## Information architecture
1. Sidebar: language + large-text toggle (apply instantly), then the household form (≈30 s) and **Make my plan**.
2. Status strip: AQI badge (colour + text category + city), data-source line (live / demo with reason), 4 metrics (AQI, PM2.5, cleanest slot, worst slot), warnings, local note.
3. Tabs: **Today's plan** (routine tips + 24-h forecast chart & table) · **Indoor air** · **Greener choices** · **Impact of each choice** (chart + table) · **Ask Saans Saathi** (AI briefing + question) · **Sources & method**.
4. Footer: privacy & terms expander, KP watermark, "not medical advice".

## Tip card
Title (action) → one-paragraph reason → bold impact line `63 → 26 µg PM2.5 inhaled (−59%)`. Cards sorted most-urgent first (🔴 do today, 🟠 recommended, 🟢 good habit); order and text carry the meaning, the dot is extra.

## States
- **Empty:** hint pointing to the sidebar.
- **Loading:** spinner while data / Gemini load.
- **Error:** every validation problem listed at once, in the user's language.
- **Degraded:** demo-data warning; offline-briefing caption with reason.
- **Success:** full plan; caption "Written by Google Gemini … every number checked".

## Accessibility
Labelled inputs, keyboard-usable forms, large-text toggle, WCAG-AA contrast on every AQI badge (tested), charts duplicated as tables, no meaning by colour alone, `role="status"` on the AQI badge, alt text on the logo.

## Responsive
Streamlit wide layout; metrics wrap on phones; sidebar collapses to a drawer.
