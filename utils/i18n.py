"""
Internationalization (Bangla & English) and Weather Terminology Explanations
"""

# WMO Weather interpretation codes (WW)
WMO_CODES = {
    0: {"en": "Clear sky", "bn": "পরিষ্কার আকাশ", "emoji": "☀️"},
    1: {"en": "Mainly clear", "bn": "বেশিরভাগ পরিষ্কার", "emoji": "🌤️"},
    2: {"en": "Partly cloudy", "bn": "আংশিক মেঘলা", "emoji": "⛅"},
    3: {"en": "Overcast", "bn": "মেঘাচ্ছন্ন", "emoji": "☁️"},
    45: {"en": "Fog", "bn": "কুয়াশা", "emoji": "🌫️"},
    48: {"en": "Depositing rime fog", "bn": "ঘন কুয়াশা", "emoji": "🌫️"},
    51: {"en": "Light drizzle", "bn": "হালকা গুঁড়ি গুঁড়ি বৃষ্টি", "emoji": "🌦️"},
    53: {"en": "Moderate drizzle", "bn": "মাঝারি গুঁড়ি গুঁড়ি বৃষ্টি", "emoji": "🌦️"},
    55: {"en": "Dense drizzle", "bn": "ঘন গুঁড়ি গুঁড়ি বৃষ্টি", "emoji": "🌧️"},
    56: {"en": "Light freezing drizzle", "bn": "হালকা শীতল গুঁড়ি বৃষ্টি", "emoji": "🌧️"},
    57: {"en": "Dense freezing drizzle", "bn": "ঘন শীতল গুঁড়ি বৃষ্টি", "emoji": "🌧️"},
    61: {"en": "Slight rain", "bn": "হালকা বৃষ্টি", "emoji": "🌦️"},
    63: {"en": "Moderate rain", "bn": "মাঝারি বৃষ্টি", "emoji": "🌧️"},
    65: {"en": "Heavy rain", "bn": "ভারী বৃষ্টি", "emoji": "🌧️⛈️"},
    66: {"en": "Light freezing rain", "bn": "হালকা বরফ বৃষ্টি", "emoji": "🌨️"},
    67: {"en": "Heavy freezing rain", "bn": "ভারী বরফ বৃষ্টি", "emoji": "🌨️"},
    71: {"en": "Slight snow fall", "bn": "হালকা তুষারপাত", "emoji": "🌨️"},
    73: {"en": "Moderate snow fall", "bn": "মাঝারি তুষারপাত", "emoji": "❄️"},
    75: {"en": "Heavy snow fall", "bn": "ভারী তুষারপাত", "emoji": "❄️🌨️"},
    77: {"en": "Snow grains", "bn": "তুষারকণা", "emoji": "❄️"},
    80: {"en": "Slight rain showers", "bn": "হালকা পশলা বৃষ্টি", "emoji": "🌦️"},
    81: {"en": "Moderate rain showers", "bn": "মাঝারি পশলা বৃষ্টি", "emoji": "🌧️"},
    82: {"en": "Violent rain showers", "bn": "প্রচণ্ড ঝড়ো বৃষ্টি", "emoji": "⛈️"},
    85: {"en": "Slight snow showers", "bn": "হালকা তুষার পশলা", "emoji": "🌨️"},
    86: {"en": "Heavy snow showers", "bn": "ভারী তুষার পশলা", "emoji": "❄️"},
    95: {"en": "Thunderstorm", "bn": "বজ্রঝড়", "emoji": "⛈️⚡"},
    96: {"en": "Thunderstorm with slight hail", "bn": "শিলাবৃষ্টিসহ বজ্রঝড়", "emoji": "⛈️🌨️"},
    99: {"en": "Thunderstorm with heavy hail", "bn": "তীব্র শিলাবৃষ্টিসহ বজ্রঝড়", "emoji": "⛈️🌨️⚡"}
}

def get_wmo_description(code: int, lang: str = "bn") -> tuple[str, str]:
    """Return condition text and emoji."""
    info = WMO_CODES.get(code, {"en": "Unknown", "bn": "অজানা", "emoji": "🌡️"})
    text = info.get(lang, info["en"])
    return text, info["emoji"]

def get_wind_direction(degree: float, lang: str = "bn") -> str:
    """Convert degrees (0-360) to cardinal direction."""
    directions_en = ["N (North)", "NNE", "NE (North-East)", "ENE", "E (East)", "ESE", "SE (South-East)", "SSE", 
                     "S (South)", "SSW", "SW (South-West)", "WSW", "W (West)", "WNW", "NW (North-West)", "NNW"]
    directions_bn = ["উত্তর (N)", "উত্তর-উত্তরপূর্ব", "উত্তর-পূর্ব (NE)", "পূর্ব-উত্তরপূর্ব", "পূর্ব (E)", "পূর্ব-দক্ষিণপূর্ব", 
                     "দক্ষিণ-পূর্ব (SE)", "দক্ষিণ-দক্ষিণপূর্ব", "দক্ষিণ (S)", "দক্ষিণ-দক্ষিণপশ্চিম", "দক্ষিণ-পশ্চিম (SW)", 
                     "পশ্চিম-দক্ষিণপশ্চিম", "পশ্চিম (W)", "পশ্চিম-উত্তরপশ্চিম", "উত্তর-পশ্চিম (NW)", "উত্তর-উত্তরপশ্চিম"]
    
    idx = int((degree + 11.25) / 22.5) % 16
    return directions_bn[idx] if lang == "bn" else directions_en[idx]

def get_aqi_category(aqi: int, lang: str = "bn") -> tuple[str, str, str]:
    """Return AQI category, color emoji, and health recommendation."""
    if aqi <= 50:
        cat_bn, cat_en = "খুব ভালো (Good)", "Good"
        emoji = "🟢"
        advice_bn = "বাতাসের মান চমৎকার! মুক্ত বাতাসে যেকোনো কাজ বা খেলাধুলা করতে পারেন।"
        advice_en = "Air quality is considered satisfactory, and air pollution poses little or no risk."
    elif aqi <= 100:
        cat_bn, cat_en = "মাঝারি (Moderate)", "Moderate"
        emoji = "🟡"
        advice_bn = "বাতাসের মান গ্রহণযোগ্য। তবে সংবেদনশীল ব্যক্তিদের দীর্ঘসময় বাইরে থাকার ব্যাপারে কিছুটা সতর্ক থাকা ভালো।"
        advice_en = "Air quality is acceptable. Sensitive individuals should consider limiting prolonged outdoor exertion."
    elif aqi <= 150:
        cat_bn, cat_en = "সংবেদনশীলদের জন্য অস্বাস্থ্যকর", "Unhealthy for Sensitive Groups"
        emoji = "🟠"
        advice_bn = "শিশু, বয়স্ক এবং ফুসফুস/অ্যাজমার রোগীদের বাইরে ভারী পরিশ্রম বা খেলাধুলা কমানোর পরামর্শ।"
        advice_en = "Members of sensitive groups may experience health effects. General public less likely to be affected."
    elif aqi <= 200:
        cat_bn, cat_en = "অস্বাস্থ্যকর (Unhealthy)", "Unhealthy"
        emoji = "🔴"
        advice_bn = "সবার স্বাস্থ্যেই বিরূপ প্রভাব পড়তে পারে। বাইরে গেলে অবশ্যই মাস্ক ব্যবহার করুন।"
        advice_en = "Everyone may begin to experience health effects. Wear a mask and reduce prolonged outdoor activity."
    elif aqi <= 300:
        cat_bn, cat_en = "খুবই অস্বাস্থ্যকর (Very Unhealthy)", "Very Unhealthy"
        emoji = "🟣"
        advice_bn = "স্বাস্থ্য সতর্কতা! শিশু ও অসুস্থদের ঘরে থাকার অনুরোধ এবং সাধারণ মানুষ বাইরে যাওয়া এড়িয়ে চলুন।"
        advice_en = "Health alert: The risk of health effects is increased for everyone. Avoid outdoor physical activity."
    else:
        cat_bn, cat_en = "বিপজ্জনক (Hazardous)", "Hazardous"
        emoji = "🟤 ⚠️"
        advice_bn = "জরুরি স্বাস্থ্য সংকট! বাইরে বের হবেন না, জানালা বন্ধ রাখুন ও এয়ার পিউরিফায়ার ব্যবহার করুন।"
        advice_en = "Health warning of emergency conditions: everyone is more likely to be affected."
        
    return (cat_bn if lang == "bn" else cat_en), emoji, (advice_bn if lang == "bn" else advice_en)

def get_uv_category(uv: float, lang: str = "bn") -> tuple[str, str, str]:
    """Return UV category, emoji, and protective advice."""
    if uv <= 2:
        cat_bn, cat_en = "কম (Low)", "Low"
        emoji = "🟢"
        advice_bn = "সুরক্ষার প্রয়োজন নেই। নিরাপদে রোদে থাকা যাবে।"
        advice_en = "Minimal danger from UV rays. Safe to stay outdoors."
    elif uv <= 5:
        cat_bn, cat_en = "মাঝারি (Moderate)", "Moderate"
        emoji = "🟡"
        advice_bn = "দুপুরে রোদে বের হলে সানগ্লাস ও ছাতা ব্যবহার করা ভালো।"
        advice_en = "Wear sunglasses and use sunscreen if outdoors during peak midday hours."
    elif uv <= 7:
        cat_bn, cat_en = "বেশি (High)", "High"
        emoji = "🟠"
        advice_bn = "সানস্ক্রিন, সানগ্লাস এবং ছাতা প্রয়োজন। দুপুর ১১টা থেকে ৩টা সরাসরি রোদ এড়িয়ে চলুন।"
        advice_en = "Protection needed. Seek shade, wear sunscreen SPF 30+, hat, and sunglasses."
    elif uv <= 10:
        cat_bn, cat_en = "খুব বেশি (Very High)", "Very High"
        emoji = "🔴"
        advice_bn = "ত্বক ও চোখের ক্ষতি হতে পারে। অতি প্রয়োজন ছাড়া বাইরে না যাওয়াই উত্তম।"
        advice_en = "Extra protection required. Avoid sun exposure between 11 AM - 3 PM."
    else:
        cat_bn, cat_en = "চরম বিপজ্জনক (Extreme)", "Extreme"
        emoji = "🟣 ⚠️"
        advice_bn = "চরম মাত্রার অতিবেগুনি রশ্মি! মাত্র কয়েক মিনিটেই ত্বক পুড়ে যেতে পারে।"
        advice_en = "Take all precautions. Unprotected skin and eyes can burn in minutes."
        
    return (cat_bn if lang == "bn" else cat_en), emoji, (advice_bn if lang == "bn" else advice_en)

# Explanations for users asking "What does humidity mean?"
TERMINOLOGY_EXPLANATIONS = {
    "humidity": {
        "bn": (
            "💧 **বাতাসের আর্দ্রতা (Humidity) কী?**\n\n"
            "বাতাসে কী পরিমাণ জলীয় বাষ্প জমা আছে তার শতকরা অনুপাত হলো আর্দ্রতা।\n"
            "• **৮০% বা তার বেশি**: বাতাস খুব ভেজা থাকে, ঘাম শুকায় না এবং অতিরিক্ত গুমোট গরম অনুভূত হয়।\n"
            "• **৪০% - ৬০%**: মানুষের শরীরের জন্য সবচেয়ে আরামদায়ক আবহাওয়া।\n"
            "• **৩০% এর নিচে**: বাতাস শুষ্ক হয়ে যায়, ত্বক ফেটে যাওয়া ও ঠোঁট ফাটার সমস্যা হয়।"
        ),
        "en": (
            "💧 **What is Humidity?**\n\n"
            "Humidity is the percentage of moisture/water vapor in the air.\n"
            "• **Above 80%**: Air feels sticky and muggy; sweat doesn't evaporate easily.\n"
            "• **40% - 60%**: Most comfortable range for humans.\n"
            "• **Below 30%**: Dry air causes dry skin and chapped lips."
        )
    },
    "aqi": {
        "bn": (
            "🌫️ **এয়ার কোয়ালিটি ইনডেক্স (AQI) কী?**\n\n"
            "AQI হলো বাতাসের দূষণের মাত্রা মাপার আন্তর্জাতিক সূচক।\n"
            "• **০ - ৫০ (সবুজ)**: চমৎকার বাতাস 🟢\n"
            "• **৫১ - ১০০ (হলুদ)**: গ্রহণযোগ্য বাতাস 🟡\n"
            "• **১০১ - ১৫০ (কমলা)**: শিশু ও অ্যাজমা রোগীদের জন্য ক্ষতিকর 🟠\n"
            "• **১৫১ - ২০০ (লাল)**: সাধারণ মানুষের জন্য অস্বাস্থ্যকর 🔴\n"
            "• **২০১ - ৩০০ (বেগুনি)**: খুবই ঝুঁকিপূর্ণ 🟣\n"
            "• **৩০০+ (বাদামি)**: জরুরি বিপজ্জনক অবস্থা 🟤"
        ),
        "en": (
            "🌫️ **What is Air Quality Index (AQI)?**\n\n"
            "AQI is an index for reporting daily air quality and pollution levels.\n"
            "• **0 - 50**: Good 🟢\n"
            "• **51 - 100**: Moderate 🟡\n"
            "• **101 - 150**: Unhealthy for Sensitive Groups 🟠\n"
            "• **151 - 200**: Unhealthy 🔴\n"
            "• **201 - 300**: Very Unhealthy 🟣\n"
            "• **300+**: Hazardous 🟤"
        )
    },
    "uv": {
        "bn": (
            "☀️ **ইউভি ইনডেক্স (UV Index) কী?**\n\n"
            "সূর্য থেকে আসা অতিবেগুনি (Ultraviolet) রশ্মির তীব্রতা নির্দেশ করে ইউভি ইনডেক্স।\n"
            "• **০ - ২ (Low)**: নিরাপদ 🟢\n"
            "• **৩ - ৫ (Moderate)**: ছাতা বা সানগ্লাস রাখা ভালো 🟡\n"
            "• **৬ - ৭ (High)**: সানস্ক্রিন ও ছায়াযুক্ত স্থানে থাকা দরকার 🟠\n"
            "• **৮ - ১০ (Very High)**: ত্বকের ক্ষতির উচ্চ ঝুঁকি 🔴\n"
            "• **১১+ (Extreme)**: সরাসরি রোদে থাকা অত্যন্ত বিপজ্জনক 🟣"
        ),
        "en": (
            "☀️ **What is UV Index?**\n\n"
            "UV Index measures the strength of sunburn-producing ultraviolet radiation.\n"
            "• **0 - 2**: Low 🟢\n"
            "• **3 - 5**: Moderate 🟡\n"
            "• **6 - 7**: High 🟠 (Sunscreen recommended)\n"
            "• **8 - 10**: Very High 🔴\n"
            "• **11+**: Extreme 🟣"
        )
    },
    "dew_point": {
        "bn": (
            "❄️ **শিশিরাঙ্ক বা ডিউ পয়েন্ট (Dew Point) কী?**\n\n"
            "যে তাপমাত্রায় বাতাস জলীয় বাষ্প ধরে রাখতে পারে না এবং শিশির বা কুয়াশায় পরিণত হয়, তাকে শিশিরাঙ্ক বলে।\n"
            "• এটি মানুষের অস্বস্তির পরিমাপ হিসেবেও কাজ করে: ডিউ পয়েন্ট ২৪°C বা তার বেশি হলে আবহাওয়া অসহ্য গুমোট হয়ে যায়।"
        ),
        "en": (
            "❄️ **What is Dew Point?**\n\n"
            "The temperature to which air must be cooled to become saturated with water vapor.\n"
            "A higher dew point indicates more moisture in the air, making it feel muggier and stickier."
        )
    }
}
