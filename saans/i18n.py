"""Three languages: English, हिंदी (Devanagari) and Hinglish (Roman script).

Why a plain dict and not gettext: the app is small, Streamlit Cloud needs no
compile step, and a test can check that every language has every key with the
SAME {placeholders} — so a missing translation is caught in CI, not by a user.
Numbers stay in Western digits in all languages: they are produced by our own
code and must match the impact table exactly.
Flow: advisor.py / app.py call t(lang, key, **values).
"""

from __future__ import annotations

from .models import Lang

LANG_NAMES = {Lang.EN: "English", Lang.HI: "हिंदी", Lang.HINGLISH: "Hinglish"}

STRINGS: dict[Lang, dict[str, str]] = {
    # ============================== ENGLISH ===================================
    Lang.EN: {
        # --- header / layout
        "app_tagline": "Your daily plan to breathe cleaner air through winter smog — with the impact of every choice.",
        "skip_hint": "Fill in your household in the sidebar and press **Make my plan**.",
        "language": "Language",
        "large_text": "Large text",
        "form_header": "Your household",
        "city": "City / town",
        "custom_loc": "Use exact coordinates instead",
        "lat": "Latitude",
        "lon": "Longitude",
        "who_home": "Who lives with you?",
        "children": "Children",
        "elderly": "Elderly (60+)",
        "respiratory": "Someone with asthma, lung or heart illness",
        "commute": "Daily travel",
        "commute_minutes": "Travel time (minutes, one way)",
        "commute_hour": "Usual departure hour (0–23)",
        "exercise": "Outdoor exercise / walk",
        "exercise_minutes": "Exercise time (minutes)",
        "exercise_hour": "Usual exercise hour (0–23)",
        "fuel": "Cooking fuel",
        "habits": "Home habits",
        "burns_waste": "We burn leaves / garbage nearby",
        "burns_incense": "We use agarbatti or mosquito coils indoors",
        "has_purifier": "We have an air purifier",
        "cadr": "Purifier CADR (m³/h, on the box)",
        "room_area": "Main room size (m²)",
        "submit": "Make my plan",
        # --- enum labels
        "commute_walk": "Walk",
        "commute_cycle": "Cycle",
        "commute_two_wheeler": "Bike / scooter",
        "commute_auto": "Auto / e-rickshaw",
        "commute_bus": "Bus",
        "commute_car": "Car",
        "commute_none": "I stay home",
        "exercise_walk": "Walk",
        "exercise_active": "Yoga / cycling / brisk walk",
        "exercise_sport": "Running / sports",
        "exercise_none": "None",
        "fuel_lpg": "LPG",
        "fuel_electric": "Induction / electric",
        "fuel_biomass": "Chulha (wood / dung / crop waste)",
        "fuel_coal": "Coal",
        "fuel_kerosene": "Kerosene",
        # --- categories
        "good": "Good",
        "satisfactory": "Satisfactory",
        "moderate": "Moderate",
        "poor": "Poor",
        "very_poor": "Very Poor",
        "severe": "Severe",
        # --- status
        "aqi_now": "AQI now (PM-based estimate)",
        "pm25_now": "PM2.5 now",
        "best_slot": "Cleanest outdoor slot",
        "worst_slot": "Most polluted slot",
        "src_google": "Live data: Google Air Quality API",
        "src_open_meteo": "Live forecast: Open-Meteo (Copernicus CAMS model, ~45 km grid)",
        "src_demo": "Demo data (not live) — live sources unavailable ({reason}).",
        "no_slot": "No daytime slot in the forecast",
        # --- tabs
        "tab_plan": "Today's plan",
        "tab_indoor": "Indoor air",
        "tab_green": "Greener choices",
        "tab_impact": "Impact of each choice",
        "tab_ask": "Ask Saans Saathi",
        "tab_method": "Sources & method",
        "forecast_chart": "PM2.5 forecast, next 24 hours (µg/m³)",
        "forecast_table": "Forecast as a table",
        "time": "Time",
        "pm25": "PM2.5 (µg/m³)",
        "aqi": "AQI",
        "category": "Category",
        # --- impact table
        "imp_choice": "Choice",
        "imp_before": "Before",
        "imp_after": "After",
        "imp_unit": "Unit",
        "imp_change": "Reduction",
        "imp_none": "No measurable change to show for your answers — your current habits are already the cleaner option.",
        "unit_dose": "µg PM2.5 inhaled",
        "unit_indoor": "µg/m³ PM2.5 indoors",
        "imp_exercise": "Exercise at the cleanest time",
        "imp_commute": "Travel at the cleanest time",
        "imp_mask": "Well-fitted N95 while travelling",
        "imp_windows": "Windows shut during peak smog",
        "imp_purifier": "Run an air purifier",
        # --- routine tips
        "t_exercise_shift": "Move your {activity} to {window}",
        "d_exercise_shift": (
            "At your usual {hour} the air averages {usual} µg/m³ PM2.5; {window} averages {best}. "
            "Same {minutes} minutes, about {pct}% less PM2.5 breathed in."
        ),
        "t_exercise_ok": "Your {activity} time is already the cleanest slot",
        "d_exercise_ok": "{window} averages {best} µg/m³ PM2.5 — keep it there today.",
        "t_exercise_indoor": "Exercise indoors today",
        "d_exercise_indoor": (
            "Even the cleanest slot ({window}) is {category}. Hard breathing outdoors pulls in far more particles — "
            "do yoga or stretching inside with windows shut."
        ),
        "t_commute_shift": "If your timing is flexible, travel at {window}",
        "d_commute_shift": (
            "Your {minutes}-minute {mode} trip at {hour} meets {usual} µg/m³; at {window} it is {best}. "
            "That is about {pct}% less PM2.5 breathed in."
        ),
        "t_mask": "Wear a well-fitted N95 on your {mode} trip",
        "d_mask": (
            "Cuts the PM2.5 you breathe in on the way from about {before} µg to {after} µg in the best case "
            "(N95 filters at least 95%). Cloth or loose masks leak around the edges and give much less."
        ),
        "t_vulnerable": "Protect {who} during {worst}",
        "d_vulnerable": (
            "Keep them indoors in that slot and plan outings for {best}. Keep prescribed inhalers or medicines handy; "
            "breathlessness, chest pain or blue lips need a doctor right away (emergency: 112)."
        ),
        "who_children": "children",
        "who_elderly": "elders",
        "who_respiratory": "anyone with asthma or heart/lung illness",
        "who_join": " and ",
        "act_walk": "walk",
        "act_active": "exercise",
        "act_sport": "sport",
        # --- indoor tips
        "t_windows": "Keep windows shut during {worst}; air the house at {best}",
        "d_windows": (
            "With windows open at peak smog, a room settles near {before} µg/m³ PM2.5; shut, about {after}. "
            "Open them for a short airing at {best} when outdoor air is cleanest."
        ),
        "t_purifier_have": "Run your purifier in the room you use most, doors shut",
        "d_purifier_have": (
            "Your {cadr} m³/h purifier in a {area} m² room brings indoor PM2.5 from about {before} to {after} µg/m³ "
            "at today's peak. Clean or replace the filter as the maker says."
        ),
        "t_purifier_need": "A purifier of at least {cadr} m³/h CADR suits your {area} m² room",
        "d_purifier_need": (
            "That size gives 4.8 air changes per hour (US EPA / ENERGY STAR). At today's peak it would bring the room "
            "from about {before} to {after} µg/m³. Check the CADR on the box, not just 'room size'."
        ),
        "t_fuel": "Switch cooking from {fuel} to LPG or induction",
        "d_fuel": (
            "Smoke from solid fuels and kerosene is the biggest indoor source in many homes — WHO links household air "
            "pollution to 2.9 million deaths a year. Until you switch: cook with the window open or an exhaust fan on, "
            "and keep children away from the stove."
        ),
        "t_incense": "Skip agarbatti and mosquito coils on smog days",
        "d_incense": "They burn indoors, right where you breathe. Use a mosquito net or an electric repellent instead.",
        "t_wet_clean": "Wet-mop instead of sweeping",
        "d_wet_clean": "Dry sweeping throws settled dust back into the air; a damp cloth or mop traps it.",
        # --- sustainable tips
        "t_waste": "Stop burning leaves and garbage",
        "d_waste": (
            "Open burning is banned under the Solid Waste Management Rules, 2016, and the smoke enters your own home first. "
            "Give dry waste to municipal collection and compost wet waste in a pit or pot."
        ),
        "t_report": "Report open burning near you",
        "d_report": "Use CPCB's Sameer app or your municipal helpline — one complaint can clear a whole street.",
        "t_transport": "Share rides or take the bus / e-rickshaw on smog days",
        "d_transport": (
            "Your {mode} adds exhaust and road dust to the same air your family breathes. Pooling one trip a day "
            "takes a vehicle off the road; for trips under 2 km, walk at {best}."
        ),
        "t_transport_clean": "You already travel the clean way",
        "d_transport_clean": "Choose lanes away from main roads and busy junctions — exhaust is highest next to traffic.",
        "t_pmuy": "Check Ujjwala Yojana for an LPG connection",
        "d_pmuy": "Eligible households can get an LPG connection under Pradhan Mantri Ujjwala Yojana (pmuy.gov.in).",
        "note_hazaribagh": "Hazaribagh: winter smoke from chulhas and leaf burning settles in the bowl-shaped town at night.",
        "note_dhanbad": "Dhanbad: coal dust from mining and the Jharia coalfield fires add to winter smog.",
        # --- warnings
        "w_severe": "Air is {category} — everyone should limit time outdoors today.",
        "w_vulnerable": "Air is {category} — extra care for {who}.",
        # --- AI tab
        "ai_header": "Your briefing",
        "ai_by_gemini": "Written by Google Gemini from the numbers above — every number checked against our calculations.",
        "ai_offline": "Offline briefing — {reason}",
        "ai_reason_no_key": "no Gemini key is configured",
        "ai_reason_failed": "Gemini didn't respond in time",
        "ai_reason_guard": "Gemini's answer used a number we couldn't verify, so we show our own summary",
        "ask_label": "Ask about your air, home or routine (optional)",
        "ask_placeholder": "e.g. Can my kids play cricket this evening?",
        "ask_button": "Ask",
        "answer": "Answer",
        "brief_headline": "{city}: AQI {aqi} ({category}) right now.",
        "brief_best": "Cleanest time to be outside: {window} (PM2.5 {best} µg/m³).",
        "brief_impact": "{title}: {before} → {after} {unit} ({pct}% less).",
        "brief_offline_answer": "Gemini is not available, so I can't answer free questions right now — the plan above covers today.",
        # --- method & footer
        "method": (
            "**How the numbers are made.** Air data comes from the Google Air Quality API, or the free Open-Meteo (Copernicus CAMS) forecast, or labelled demo data. "
            "We convert PM2.5/PM10 to India's CPCB AQI ourselves. *Breathed-in dose* = concentration × breathing rate "
            "for the activity × time. *Indoor air* uses a standard single-room mass balance. Gemini only writes the "
            "words; a guard rejects any answer containing a number our code didn't produce."
        ),
        "assumptions": "Assumptions (model inputs that are typical values, not measurements of your home)",
        "footer": "Built by Kanak Prabhakar · No account, no cookies, nothing stored · Not medical advice.",
        "privacy_title": "Privacy & terms",
        "privacy": (
            "Your answers stay in this browser session and are never saved. Coordinates are rounded to about 1 km "
            "before being sent to Google to fetch air data; the plan facts (no name, no exact address) are sent to "
            "Gemini to write the briefing. This tool gives general guidance, not a diagnosis — follow your doctor's advice."
        ),
        # --- errors
        "err_city": "Please pick a city or enter coordinates.",
        "err_coords": "Coordinates must be numbers inside India.",
        "err_minutes": "Minutes must be whole numbers between 0 and 240.",
        "err_hour": "Hours must be between 0 and 23.",
        "err_cadr": "CADR must be a whole number between 0 and 2000 m³/h.",
        "err_cadr_missing": "Please enter your purifier's CADR (printed on the box).",
        "err_room": "Room size must be between 4 and 120 m².",
    },
    # ============================== HINDI =====================================
    Lang.HI: {
        "app_tagline": "सर्दियों के स्मॉग में साफ़ हवा के लिए आपका रोज़ का प्लान — हर फ़ैसले के असर के साथ।",
        "skip_hint": "साइडबार में अपने घर की जानकारी भरें और **मेरा प्लान बनाओ** दबाएँ।",
        "language": "भाषा",
        "large_text": "बड़े अक्षर",
        "form_header": "आपका घर",
        "city": "शहर / कस्बा",
        "custom_loc": "सही निर्देशांक (coordinates) डालें",
        "lat": "अक्षांश (Latitude)",
        "lon": "देशांतर (Longitude)",
        "who_home": "आपके साथ कौन रहता है?",
        "children": "बच्चे",
        "elderly": "बुज़ुर्ग (60+)",
        "respiratory": "दमा, फेफड़े या दिल की बीमारी वाला सदस्य",
        "commute": "रोज़ का सफ़र",
        "commute_minutes": "सफ़र का समय (मिनट, एक तरफ़)",
        "commute_hour": "निकलने का आम समय (0–23 घंटा)",
        "exercise": "बाहर व्यायाम / सैर",
        "exercise_minutes": "व्यायाम का समय (मिनट)",
        "exercise_hour": "व्यायाम का आम समय (0–23 घंटा)",
        "fuel": "खाना पकाने का ईंधन",
        "habits": "घर की आदतें",
        "burns_waste": "आस-पास पत्ते / कचरा जलाते हैं",
        "burns_incense": "घर में अगरबत्ती या मच्छर कॉइल जलाते हैं",
        "has_purifier": "हमारे पास एयर प्यूरीफ़ायर है",
        "cadr": "प्यूरीफ़ायर का CADR (m³/h, डिब्बे पर लिखा)",
        "room_area": "मुख्य कमरे का आकार (m²)",
        "submit": "मेरा प्लान बनाओ",
        "commute_walk": "पैदल",
        "commute_cycle": "साइकिल",
        "commute_two_wheeler": "बाइक / स्कूटर",
        "commute_auto": "ऑटो / ई-रिक्शा",
        "commute_bus": "बस",
        "commute_car": "कार",
        "commute_none": "घर पर रहता/रहती हूँ",
        "exercise_walk": "सैर",
        "exercise_active": "योग / साइकिल / तेज़ चाल",
        "exercise_sport": "दौड़ / खेल",
        "exercise_none": "कोई नहीं",
        "fuel_lpg": "LPG",
        "fuel_electric": "इंडक्शन / बिजली",
        "fuel_biomass": "चूल्हा (लकड़ी / गोबर / फ़सल का कचरा)",
        "fuel_coal": "कोयला",
        "fuel_kerosene": "मिट्टी का तेल",
        "good": "अच्छी",
        "satisfactory": "संतोषजनक",
        "moderate": "मध्यम",
        "poor": "ख़राब",
        "very_poor": "बहुत ख़राब",
        "severe": "गंभीर",
        "aqi_now": "अभी AQI (PM पर आधारित अनुमान)",
        "pm25_now": "अभी PM2.5",
        "best_slot": "बाहर जाने का सबसे साफ़ समय",
        "worst_slot": "सबसे प्रदूषित समय",
        "src_google": "लाइव डेटा: Google Air Quality API",
        "src_open_meteo": "लाइव पूर्वानुमान: Open-Meteo (Copernicus CAMS मॉडल, ~45 km ग्रिड)",
        "src_demo": "डेमो डेटा (लाइव नहीं) — लाइव स्रोत उपलब्ध नहीं ({reason})।",
        "no_slot": "पूर्वानुमान में दिन का कोई समय नहीं मिला",
        "tab_plan": "आज का प्लान",
        "tab_indoor": "घर के अंदर की हवा",
        "tab_green": "हरित विकल्प",
        "tab_impact": "हर फ़ैसले का असर",
        "tab_ask": "साँस साथी से पूछें",
        "tab_method": "स्रोत और तरीका",
        "forecast_chart": "अगले 24 घंटे का PM2.5 पूर्वानुमान (µg/m³)",
        "forecast_table": "पूर्वानुमान तालिका में",
        "time": "समय",
        "pm25": "PM2.5 (µg/m³)",
        "aqi": "AQI",
        "category": "श्रेणी",
        "imp_choice": "फ़ैसला",
        "imp_before": "पहले",
        "imp_after": "बाद में",
        "imp_unit": "इकाई",
        "imp_change": "कमी",
        "imp_none": "आपके जवाबों के हिसाब से दिखाने लायक कोई बदलाव नहीं — आपकी आदतें पहले से साफ़ विकल्प हैं।",
        "unit_dose": "µg PM2.5 साँस में",
        "unit_indoor": "µg/m³ PM2.5 घर में",
        "imp_exercise": "सबसे साफ़ समय पर व्यायाम",
        "imp_commute": "सबसे साफ़ समय पर सफ़र",
        "imp_mask": "सफ़र में ठीक से लगा N95",
        "imp_windows": "स्मॉग के चरम पर खिड़कियाँ बंद",
        "imp_purifier": "एयर प्यूरीफ़ायर चलाएँ",
        "t_exercise_shift": "अपनी {activity} {window} पर करें",
        "d_exercise_shift": (
            "आपके आम समय {hour} पर हवा में औसत {usual} µg/m³ PM2.5 है; {window} पर औसत {best}। "
            "वही {minutes} मिनट, लगभग {pct}% कम PM2.5 साँस में।"
        ),
        "t_exercise_ok": "आपकी {activity} का समय पहले से सबसे साफ़ है",
        "d_exercise_ok": "{window} पर औसत {best} µg/m³ PM2.5 — आज वही समय रखें।",
        "t_exercise_indoor": "आज व्यायाम घर के अंदर करें",
        "d_exercise_indoor": (
            "सबसे साफ़ समय ({window}) भी {category} है। बाहर तेज़ साँस लेने से बहुत ज़्यादा कण अंदर जाते हैं — "
            "खिड़कियाँ बंद करके घर में योग या स्ट्रेचिंग करें।"
        ),
        "t_commute_shift": "अगर समय बदल सकते हैं, तो {window} पर सफ़र करें",
        "d_commute_shift": (
            "{hour} पर आपके {minutes} मिनट के {mode} सफ़र में {usual} µg/m³ है; {window} पर {best}। "
            "यानी लगभग {pct}% कम PM2.5 साँस में।"
        ),
        "t_mask": "{mode} के सफ़र में ठीक से लगा N95 पहनें",
        "d_mask": (
            "रास्ते में साँस में जाने वाला PM2.5 लगभग {before} µg से घटकर {after} µg तक (सबसे अच्छी स्थिति में; "
            "N95 कम से कम 95% छानता है)। कपड़े का या ढीला मास्क किनारों से रिसता है और बहुत कम बचाता है।"
        ),
        "t_vulnerable": "{worst} के दौरान {who} को बचाएँ",
        "d_vulnerable": (
            "उस समय उन्हें घर के अंदर रखें और बाहर जाना {best} पर रखें। डॉक्टर की दी हुई इनहेलर/दवाइयाँ पास रखें; "
            "साँस फूलना, सीने में दर्द या होंठ नीले पड़ें तो तुरंत डॉक्टर को दिखाएँ (आपातकाल: 112)।"
        ),
        "who_children": "बच्चों",
        "who_elderly": "बुज़ुर्गों",
        "who_respiratory": "दमा या दिल/फेफड़े के मरीज़",
        "who_join": " और ",
        "act_walk": "सैर",
        "act_active": "कसरत",
        "act_sport": "खेल",
        "t_windows": "{worst} में खिड़कियाँ बंद रखें; {best} पर घर में हवा आने दें",
        "d_windows": (
            "स्मॉग के चरम पर खिड़कियाँ खुली हों तो कमरे में लगभग {before} µg/m³ PM2.5 रहता है; बंद हों तो लगभग {after}। "
            "{best} पर जब बाहर हवा सबसे साफ़ हो, थोड़ी देर के लिए खोलें।"
        ),
        "t_purifier_have": "जिस कमरे में सबसे ज़्यादा रहते हैं, वहाँ दरवाज़े बंद करके प्यूरीफ़ायर चलाएँ",
        "d_purifier_have": (
            "{area} m² कमरे में आपका {cadr} m³/h प्यूरीफ़ायर आज के चरम पर घर का PM2.5 लगभग {before} से {after} µg/m³ "
            "तक लाता है। फ़िल्टर कंपनी के बताए अनुसार साफ़ करें या बदलें।"
        ),
        "t_purifier_need": "आपके {area} m² कमरे के लिए कम से कम {cadr} m³/h CADR का प्यूरीफ़ायर ठीक है",
        "d_purifier_need": (
            "इतना CADR घंटे में 4.8 बार हवा बदलता है (US EPA / ENERGY STAR)। आज के चरम पर यह कमरे को लगभग {before} से "
            "{after} µg/m³ तक लाएगा। डिब्बे पर CADR देखें, सिर्फ़ 'कमरे का आकार' नहीं।"
        ),
        "t_fuel": "खाना {fuel} की जगह LPG या इंडक्शन पर पकाएँ",
        "d_fuel": (
            "ठोस ईंधन और मिट्टी के तेल का धुआँ कई घरों में अंदर का सबसे बड़ा स्रोत है — WHO के अनुसार घरेलू वायु प्रदूषण "
            "से हर साल 2.9 मिलियन मौतें होती हैं। बदलने तक: खिड़की खोलकर या एग्ज़ॉस्ट फ़ैन चलाकर पकाएँ और बच्चों को "
            "चूल्हे से दूर रखें।"
        ),
        "t_incense": "स्मॉग वाले दिनों में अगरबत्ती और मच्छर कॉइल न जलाएँ",
        "d_incense": "ये घर के अंदर, ठीक वहीं जलते हैं जहाँ आप साँस लेते हैं। मच्छरदानी या बिजली वाला रिपेलेंट इस्तेमाल करें।",
        "t_wet_clean": "झाड़ू की जगह गीला पोछा लगाएँ",
        "d_wet_clean": "सूखी झाड़ू जमी धूल को फिर हवा में उड़ा देती है; गीला कपड़ा या पोछा उसे पकड़ लेता है।",
        "t_waste": "पत्ते और कचरा जलाना बंद करें",
        "d_waste": (
            "ठोस अपशिष्ट प्रबंधन नियम, 2016 के तहत खुले में जलाना मना है, और इसका धुआँ सबसे पहले आपके अपने घर में आता है। "
            "सूखा कचरा नगर निगम की गाड़ी को दें और गीले कचरे की गड्ढे या मटके में खाद बनाएँ।"
        ),
        "t_report": "आस-पास कचरा जलता दिखे तो शिकायत करें",
        "d_report": "CPCB का समीर (Sameer) ऐप या नगर निगम हेल्पलाइन इस्तेमाल करें — एक शिकायत पूरी गली की हवा साफ़ कर सकती है।",
        "t_transport": "स्मॉग वाले दिनों में साथ सफ़र करें या बस / ई-रिक्शा लें",
        "d_transport": (
            "आपकी {mode} उसी हवा में धुआँ और सड़क की धूल डालती है जिसमें आपका परिवार साँस लेता है। रोज़ एक सफ़र साझा "
            "करने से एक गाड़ी कम होती है; 2 km से छोटे सफ़र {best} पर पैदल करें।"
        ),
        "t_transport_clean": "आप पहले से साफ़ तरीके से सफ़र करते हैं",
        "d_transport_clean": "मुख्य सड़कों और भीड़ वाले चौराहों से दूर की गलियाँ चुनें — ट्रैफ़िक के पास धुआँ सबसे ज़्यादा होता है।",
        "t_pmuy": "LPG कनेक्शन के लिए उज्ज्वला योजना देखें",
        "d_pmuy": "पात्र परिवार प्रधानमंत्री उज्ज्वला योजना (pmuy.gov.in) में LPG कनेक्शन ले सकते हैं।",
        "note_hazaribagh": "हज़ारीबाग: सर्दियों में चूल्हे और पत्ते जलाने का धुआँ रात में कटोरे जैसे शहर में जम जाता है।",
        "note_dhanbad": "धनबाद: खनन की कोयला धूल और झरिया कोलफ़ील्ड की आग सर्दियों के स्मॉग को बढ़ाती है।",
        "w_severe": "हवा {category} है — आज सभी लोग बाहर कम समय बिताएँ।",
        "w_vulnerable": "हवा {category} है — {who} का ख़ास ध्यान रखें।",
        "ai_header": "आपकी ब्रीफ़िंग",
        "ai_by_gemini": "ऊपर के आँकड़ों से Google Gemini ने लिखा — हर संख्या हमारी गणना से जाँची गई।",
        "ai_offline": "ऑफ़लाइन ब्रीफ़िंग — {reason}",
        "ai_reason_no_key": "Gemini key सेट नहीं है",
        "ai_reason_failed": "Gemini ने समय पर जवाब नहीं दिया",
        "ai_reason_guard": "Gemini के जवाब में ऐसी संख्या थी जिसे हम जाँच नहीं सके, इसलिए हमारा सारांश दिखा रहे हैं",
        "ask_label": "अपनी हवा, घर या दिनचर्या के बारे में पूछें (वैकल्पिक)",
        "ask_placeholder": "जैसे: क्या बच्चे आज शाम क्रिकेट खेल सकते हैं?",
        "ask_button": "पूछें",
        "answer": "जवाब",
        "brief_headline": "{city}: अभी AQI {aqi} ({category})।",
        "brief_best": "बाहर रहने का सबसे साफ़ समय: {window} (PM2.5 {best} µg/m³)।",
        "brief_impact": "{title}: {before} → {after} {unit} ({pct}% कम)।",
        "brief_offline_answer": "Gemini उपलब्ध नहीं है, इसलिए अभी सवालों के जवाब नहीं दे सकते — आज के लिए ऊपर का प्लान देखें।",
        "method": (
            "**संख्याएँ कैसे बनती हैं।** हवा का डेटा Google Air Quality API से, या मुफ़्त Open-Meteo (Copernicus CAMS) पूर्वानुमान से, या साफ़ लिखे डेमो डेटा से आता है। "
            "PM2.5/PM10 को हम ख़ुद भारत के CPCB AQI में बदलते हैं। *साँस में गई मात्रा* = सांद्रता × उस गतिविधि में "
            "साँस की दर × समय। *घर के अंदर की हवा* के लिए एक मानक कमरा-संतुलन मॉडल है। Gemini सिर्फ़ शब्द लिखता है; "
            "ऐसा कोई भी जवाब रद्द होता है जिसमें हमारी गणना से बाहर की संख्या हो।"
        ),
        "assumptions": "मान्यताएँ (मॉडल के सामान्य मान, आपके घर का माप नहीं)",
        "footer": "कनक प्रभाकर द्वारा बनाया गया · न अकाउंट, न कुकी, कुछ भी सेव नहीं · यह चिकित्सा सलाह नहीं है।",
        "privacy_title": "गोपनीयता और शर्तें",
        "privacy": (
            "आपके जवाब सिर्फ़ इस ब्राउज़र सेशन में रहते हैं और कभी सेव नहीं होते। हवा का डेटा लाने के लिए निर्देशांक लगभग "
            "1 km तक गोल करके Google को भेजे जाते हैं; ब्रीफ़िंग लिखने के लिए प्लान के तथ्य (न नाम, न सही पता) Gemini को "
            "भेजे जाते हैं। यह सामान्य मार्गदर्शन है, जाँच नहीं — अपने डॉक्टर की सलाह मानें।"
        ),
        "err_city": "कृपया शहर चुनें या निर्देशांक डालें।",
        "err_coords": "निर्देशांक भारत के अंदर की संख्याएँ होने चाहिए।",
        "err_minutes": "मिनट 0 से 240 के बीच पूरी संख्या होने चाहिए।",
        "err_hour": "घंटा 0 से 23 के बीच होना चाहिए।",
        "err_cadr": "CADR 0 से 2000 m³/h के बीच पूरी संख्या होनी चाहिए।",
        "err_cadr_missing": "कृपया अपने प्यूरीफ़ायर का CADR डालें (डिब्बे पर लिखा होता है)।",
        "err_room": "कमरे का आकार 4 से 120 m² के बीच होना चाहिए।",
    },
    # ============================== HINGLISH ==================================
    Lang.HINGLISH: {
        "app_tagline": "Sardiyon ke smog mein saaf hawa ke liye aapka daily plan — har choice ke asar ke saath.",
        "skip_hint": "Sidebar mein apne ghar ki details bharo aur **Mera plan banao** dabao.",
        "language": "Bhasha",
        "large_text": "Bade akshar",
        "form_header": "Aapka ghar",
        "city": "Shehar / town",
        "custom_loc": "Exact coordinates daalo",
        "lat": "Latitude",
        "lon": "Longitude",
        "who_home": "Aapke saath kaun rehta hai?",
        "children": "Bachche",
        "elderly": "Buzurg (60+)",
        "respiratory": "Asthma, lungs ya dil ki bimari wala member",
        "commute": "Roz ka safar",
        "commute_minutes": "Safar ka time (minute, ek taraf)",
        "commute_hour": "Nikalne ka usual time (0–23 ghanta)",
        "exercise": "Bahar exercise / walk",
        "exercise_minutes": "Exercise ka time (minute)",
        "exercise_hour": "Exercise ka usual time (0–23 ghanta)",
        "fuel": "Khana pakane ka fuel",
        "habits": "Ghar ki aadatein",
        "burns_waste": "Aas-paas patte / kachra jalate hain",
        "burns_incense": "Ghar mein agarbatti ya mosquito coil jalate hain",
        "has_purifier": "Hamare paas air purifier hai",
        "cadr": "Purifier ka CADR (m³/h, dibbe pe likha)",
        "room_area": "Main room ka size (m²)",
        "submit": "Mera plan banao",
        "commute_walk": "Paidal",
        "commute_cycle": "Cycle",
        "commute_two_wheeler": "Bike / scooter",
        "commute_auto": "Auto / e-rickshaw",
        "commute_bus": "Bus",
        "commute_car": "Car",
        "commute_none": "Ghar pe rehta/rehti hoon",
        "exercise_walk": "Walk",
        "exercise_active": "Yoga / cycling / tez walk",
        "exercise_sport": "Running / khel",
        "exercise_none": "Kuch nahi",
        "fuel_lpg": "LPG",
        "fuel_electric": "Induction / bijli",
        "fuel_biomass": "Chulha (lakdi / gobar / fasal ka kachra)",
        "fuel_coal": "Koyla",
        "fuel_kerosene": "Kerosene (mitti ka tel)",
        "good": "Achhi",
        "satisfactory": "Theek-thaak",
        "moderate": "Moderate",
        "poor": "Kharab",
        "very_poor": "Bahut kharab",
        "severe": "Gambhir",
        "aqi_now": "Abhi AQI (PM based estimate)",
        "pm25_now": "Abhi PM2.5",
        "best_slot": "Bahar jaane ka sabse saaf time",
        "worst_slot": "Sabse pollution wala time",
        "src_google": "Live data: Google Air Quality API",
        "src_open_meteo": "Live forecast: Open-Meteo (Copernicus CAMS model, ~45 km grid)",
        "src_demo": "Demo data (live nahi) — live sources available nahi ({reason}).",
        "no_slot": "Forecast mein din ka koi slot nahi mila",
        "tab_plan": "Aaj ka plan",
        "tab_indoor": "Ghar ke andar ki hawa",
        "tab_green": "Green choices",
        "tab_impact": "Har choice ka asar",
        "tab_ask": "Saans Saathi se poocho",
        "tab_method": "Sources aur tareeka",
        "forecast_chart": "Agle 24 ghante ka PM2.5 forecast (µg/m³)",
        "forecast_table": "Forecast table mein",
        "time": "Time",
        "pm25": "PM2.5 (µg/m³)",
        "aqi": "AQI",
        "category": "Category",
        "imp_choice": "Choice",
        "imp_before": "Pehle",
        "imp_after": "Baad mein",
        "imp_unit": "Unit",
        "imp_change": "Kami",
        "imp_none": "Aapke jawaabon ke hisaab se dikhane layak koi change nahi — aapki aadatein pehle se saaf option hain.",
        "unit_dose": "µg PM2.5 saans mein",
        "unit_indoor": "µg/m³ PM2.5 ghar mein",
        "imp_exercise": "Sabse saaf time pe exercise",
        "imp_commute": "Sabse saaf time pe safar",
        "imp_mask": "Safar mein theek se laga N95",
        "imp_windows": "Smog peak pe khidkiyan band",
        "imp_purifier": "Air purifier chalao",
        "t_exercise_shift": "Apni {activity} {window} pe karo",
        "d_exercise_shift": (
            "Aapke usual time {hour} pe hawa mein average {usual} µg/m³ PM2.5 hai; {window} pe average {best}. "
            "Wahi {minutes} minute, lagbhag {pct}% kam PM2.5 saans mein."
        ),
        "t_exercise_ok": "Aapki {activity} ka time pehle se sabse saaf slot hai",
        "d_exercise_ok": "{window} pe average {best} µg/m³ PM2.5 — aaj wahi time rakho.",
        "t_exercise_indoor": "Aaj exercise ghar ke andar karo",
        "d_exercise_indoor": (
            "Sabse saaf slot ({window}) bhi {category} hai. Bahar tez saans lene se bahut zyada particles andar jaate hain — "
            "khidkiyan band karke ghar mein yoga ya stretching karo."
        ),
        "t_commute_shift": "Agar time badal sakte ho, toh {window} pe safar karo",
        "d_commute_shift": (
            "{hour} pe aapke {minutes} minute ke {mode} safar mein {usual} µg/m³ hai; {window} pe {best}. "
            "Yaani lagbhag {pct}% kam PM2.5 saans mein."
        ),
        "t_mask": "{mode} ke safar mein theek se laga N95 pehno",
        "d_mask": (
            "Raste mein saans mein jaane wala PM2.5 lagbhag {before} µg se {after} µg tak (best case; N95 kam se kam 95% "
            "filter karta hai). Kapde ka ya dheela mask kinaron se leak karta hai aur bahut kam bachata hai."
        ),
        "t_vulnerable": "{worst} ke time {who} ko bachao",
        "d_vulnerable": (
            "Us slot mein unhe ghar ke andar rakho aur bahar jaana {best} pe rakho. Doctor ki di hui inhaler/dawaiyan paas "
            "rakho; saans phoolna, seene mein dard ya hoth neele pade toh turant doctor ko dikhao (emergency: 112)."
        ),
        "who_children": "bachchon",
        "who_elderly": "buzurgon",
        "who_respiratory": "asthma ya dil/lungs ke mareez",
        "who_join": " aur ",
        "act_walk": "walk",
        "act_active": "exercise",
        "act_sport": "khel",
        "t_windows": "{worst} mein khidkiyan band rakho; {best} pe ghar mein hawa aane do",
        "d_windows": (
            "Smog peak pe khidkiyan khuli hon toh room mein lagbhag {before} µg/m³ PM2.5 rehta hai; band hon toh lagbhag "
            "{after}. {best} pe jab bahar hawa sabse saaf ho, thodi der ke liye kholo."
        ),
        "t_purifier_have": "Jis room mein sabse zyada rehte ho, wahan darwaze band karke purifier chalao",
        "d_purifier_have": (
            "{area} m² room mein aapka {cadr} m³/h purifier aaj ke peak pe ghar ka PM2.5 lagbhag {before} se {after} "
            "µg/m³ tak laata hai. Filter company ke bataye hisaab se saaf karo ya badlo."
        ),
        "t_purifier_need": "Aapke {area} m² room ke liye kam se kam {cadr} m³/h CADR ka purifier sahi hai",
        "d_purifier_need": (
            "Itna CADR ghante mein 4.8 baar hawa badalta hai (US EPA / ENERGY STAR). Aaj ke peak pe ye room ko lagbhag "
            "{before} se {after} µg/m³ tak laayega. Dibbe pe CADR dekho, sirf 'room size' nahi."
        ),
        "t_fuel": "Khana {fuel} ki jagah LPG ya induction pe pakao",
        "d_fuel": (
            "Solid fuel aur kerosene ka dhuan kai gharon mein andar ka sabse bada source hai — WHO ke hisaab se household air "
            "pollution se har saal 2.9 million mautein hoti hain. Badalne tak: khidki khol ke ya exhaust fan chala ke pakao, "
            "aur bachchon ko chulhe se door rakho."
        ),
        "t_incense": "Smog wale din agarbatti aur mosquito coil mat jalao",
        "d_incense": "Ye ghar ke andar, theek wahin jalte hain jahan aap saans lete ho. Machhardani ya electric repellent use karo.",
        "t_wet_clean": "Jhaadu ki jagah geela pochha lagao",
        "d_wet_clean": "Sookhi jhaadu jami dhool ko phir hawa mein uda deti hai; geela kapda ya pochha use pakad leta hai.",
        "t_waste": "Patte aur kachra jalana band karo",
        "d_waste": (
            "Solid Waste Management Rules, 2016 ke under khule mein jalana mana hai, aur iska dhuan sabse pehle aapke apne "
            "ghar mein aata hai. Sookha kachra nagar nigam ki gaadi ko do aur geele kachre ki gaddhe ya matke mein khaad banao."
        ),
        "t_report": "Aas-paas kachra jalta dikhe toh complaint karo",
        "d_report": "CPCB ka Sameer app ya nagar nigam helpline use karo — ek complaint poori gali ki hawa saaf kar sakti hai.",
        "t_transport": "Smog wale din ride share karo ya bus / e-rickshaw lo",
        "d_transport": (
            "Aapki {mode} usi hawa mein dhuan aur sadak ki dhool daalti hai jismein aapka parivaar saans leta hai. Roz ek "
            "safar share karne se ek gaadi kam hoti hai; 2 km se chhote safar {best} pe paidal karo."
        ),
        "t_transport_clean": "Aap pehle se saaf tareeke se safar karte ho",
        "d_transport_clean": "Main road aur bheed wale chauraahon se door ki galiyan chuno — traffic ke paas dhuan sabse zyada hota hai.",
        "t_pmuy": "LPG connection ke liye Ujjwala Yojana check karo",
        "d_pmuy": "Eligible parivaar Pradhan Mantri Ujjwala Yojana (pmuy.gov.in) mein LPG connection le sakte hain.",
        "note_hazaribagh": "Hazaribagh: sardiyon mein chulhe aur patte jalane ka dhuan raat mein katori jaise shehar mein jam jaata hai.",
        "note_dhanbad": "Dhanbad: mining ki koyla dhool aur Jharia coalfield ki aag sardiyon ka smog badhati hai.",
        "w_severe": "Hawa {category} hai — aaj sab log bahar kam time bitayein.",
        "w_vulnerable": "Hawa {category} hai — {who} ka khaas dhyan rakho.",
        "ai_header": "Aapki briefing",
        "ai_by_gemini": "Upar ke numbers se Google Gemini ne likha — har number hamari calculation se check kiya gaya.",
        "ai_offline": "Offline briefing — {reason}",
        "ai_reason_no_key": "Gemini key set nahi hai",
        "ai_reason_failed": "Gemini ne time pe jawab nahi diya",
        "ai_reason_guard": "Gemini ke jawab mein aisa number tha jo hum verify nahi kar paaye, isliye hamari summary dikha rahe hain",
        "ask_label": "Apni hawa, ghar ya routine ke baare mein poocho (optional)",
        "ask_placeholder": "jaise: Kya bachche aaj shaam cricket khel sakte hain?",
        "ask_button": "Poocho",
        "answer": "Jawab",
        "brief_headline": "{city}: abhi AQI {aqi} ({category}).",
        "brief_best": "Bahar rehne ka sabse saaf time: {window} (PM2.5 {best} µg/m³).",
        "brief_impact": "{title}: {before} → {after} {unit} ({pct}% kam).",
        "brief_offline_answer": "Gemini available nahi hai, isliye abhi sawaalon ke jawab nahi de sakte — aaj ke liye upar ka plan dekho.",
        "method": (
            "**Numbers kaise bante hain.** Hawa ka data Google Air Quality API se, ya free Open-Meteo (Copernicus CAMS) forecast se, ya saaf likhe demo data se aata hai. "
            "PM2.5/PM10 ko hum khud India ke CPCB AQI mein badalte hain. *Saans mein gayi matra* = concentration × us "
            "activity mein saans ki rate × time. *Ghar ke andar ki hawa* ke liye ek standard single-room mass balance "
            "model hai. Gemini sirf words likhta hai; koi bhi jawab reject hota hai jismein hamari calculation se bahar "
            "ka number ho."
        ),
        "assumptions": "Assumptions (model ke typical values, aapke ghar ka measurement nahi)",
        "footer": "Kanak Prabhakar ne banaya · Na account, na cookies, kuch save nahi · Ye medical advice nahi hai.",
        "privacy_title": "Privacy aur terms",
        "privacy": (
            "Aapke jawaab sirf is browser session mein rehte hain aur kabhi save nahi hote. Hawa ka data laane ke liye "
            "coordinates lagbhag 1 km tak round karke Google ko bheje jaate hain; briefing likhne ke liye plan ke facts "
            "(na naam, na exact address) Gemini ko bheje jaate hain. Ye general guidance hai, diagnosis nahi — apne "
            "doctor ki salaah maano."
        ),
        "err_city": "Please shehar chuno ya coordinates daalo.",
        "err_coords": "Coordinates India ke andar ke numbers hone chahiye.",
        "err_minutes": "Minute 0 se 240 ke beech poore number hone chahiye.",
        "err_hour": "Ghanta 0 se 23 ke beech hona chahiye.",
        "err_cadr": "CADR 0 se 2000 m³/h ke beech poora number hona chahiye.",
        "err_cadr_missing": "Please apne purifier ka CADR daalo (dibbe pe likha hota hai).",
        "err_room": "Room ka size 4 se 120 m² ke beech hona chahiye.",
    },
}


def t(lang: Lang, key: str, **values: object) -> str:
    """Translated text with {placeholders} filled in.

    Falls back to English if a key is missing in a language, and to the key
    itself if it is missing everywhere — the UI never crashes on a typo.
    """
    text = STRINGS.get(lang, {}).get(key) or STRINGS[Lang.EN].get(key) or key
    return text.format(**values) if values else text
