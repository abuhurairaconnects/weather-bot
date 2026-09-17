"""
Weather API client using Open-Meteo services (Geocoding, Forecast, and Air Quality).
Requires no API keys and provides global coverage.
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import OPEN_METEO_GEOCODING_URL, OPEN_METEO_FORECAST_URL, OPEN_METEO_AIR_QUALITY_URL
from utils.moon import get_moon_phase
from utils.i18n import get_wmo_description, get_wind_direction, get_aqi_category, get_uv_category

def c_to_f(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32

def format_temp(celsius: Optional[float], unit: str = "C") -> str:
    """Format temperature string based on user preference."""
    if celsius is None:
        return "N/A"
    if unit == "F":
        return f"{c_to_f(celsius):.1f}°F"
    return f"{celsius:.1f}°C"

async def resolve_area_with_ai(bengali_name: str) -> Optional[str]:
    """Uses Gemini Flash Lite to resolve any obscure village/upazila/area in Bangladesh to its standard English name."""
    from config import GEMINI_API_KEY, GEMINI_API_BASE_URL
    if not GEMINI_API_KEY:
        return None
    clean = bengali_name.strip()
    # If purely ascii and looks like gibberish or has underscores, skip AI
    if "_" in clean or len(clean) > 25 and not any(ord(c) > 127 for c in clean):
        return None
    url = f"{GEMINI_API_BASE_URL}/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}"
    prompt = (
        f'The user is searching for a location in Bangladesh: "{clean}". '
        'What is the single standard English place keyword for this upazila, district, thana, union, or village in Bangladesh? '
        'If this location is outside Bangladesh, fake, gibberish, or not a real geographical place in Bangladesh, reply ONLY with "UNKNOWN". '
        'Otherwise return ONLY the single place name keyword in English without commas, punctuation, or country name (e.g. "Srimangal" or "Bheramara" or "Barura").'
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, json=payload)
            if r.status_code == 200:
                candidates = r.json().get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        word = parts[0]["text"].strip()
                        resolved = word.split(",")[0].replace('"', '').strip()
                        if resolved.upper() in ["UNKNOWN", "NONE", "NOT FOUND"]:
                            return None
                        return resolved
    except Exception:
        pass
    return None

async def search_city(query: str) -> List[Dict[str, Any]]:
    """
    Search strictly for locations within Bangladesh matching query.
    1. First checks local Bangladesh administrative database (all 64 districts & 495+ upazilas).
    2. Checks alias dictionary.
    3. Falls back to Open-Meteo geocoding STRICTLY filtered to Bangladesh bounds.
    4. Falls back to AI resolution for obscure Bangladesh villages/unions.
    """
    clean_q = query.strip()
    
    # 1. Primary check: Verified Bangladesh local database (instant 0ms, 100% GPS accuracy)
    try:
        from services.bd_geocoder import find_bd_location
        bd_loc = find_bd_location(clean_q)
        if bd_loc:
            return [bd_loc]
    except Exception as e:
        print(f"BD geocoder check error: {e}")

    # 2. Check alias dictionary
    try:
        from services.nlp_parser import COMMON_CITY_ALIASES, normalize_bengali_name
        lower_q = clean_q.lower()
        if lower_q in COMMON_CITY_ALIASES:
            clean_q = COMMON_CITY_ALIASES[lower_q]
        else:
            norm_q = normalize_bengali_name(lower_q)
            if norm_q in COMMON_CITY_ALIASES:
                clean_q = COMMON_CITY_ALIASES[norm_q]
        # Re-check BD geocoder with resolved alias
        from services.bd_geocoder import find_bd_location
        bd_loc_alias = find_bd_location(clean_q)
        if bd_loc_alias:
            return [bd_loc_alias]
    except Exception:
        pass

    async def _fetch_from_open_meteo(name_to_search: str) -> List[Dict[str, Any]]:
        params = {
            "name": name_to_search,
            "count": 10,
            "language": "en",
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(OPEN_METEO_GEOCODING_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return []
            
            # STRICTLY filter only Bangladesh locations (Lat: 20.5-26.7, Lon: 88.0-92.7)
            bd_res = []
            for r in results:
                country = r.get("country", "")
                country_code = r.get("country_code", "")
                try:
                    lat = float(r.get("latitude", 0))
                    lon = float(r.get("longitude", 0))
                except Exception:
                    continue

                is_bd = (country == "Bangladesh" or country_code.upper() == "BD" or 
                         (20.5 <= lat <= 26.7 and 88.0 <= lon <= 92.7))
                if is_bd:
                    bd_res.append(r)

            if not bd_res:
                return []

            output = []
            for item in bd_res:
                admin = item.get("admin1") or ""
                country = item.get("country") or "Bangladesh"
                loc_name = item.get("name")
                display_parts = [loc_name]
                if admin and admin != loc_name:
                    display_parts.append(admin)
                display_parts.append("Bangladesh")

                output.append({
                    "name": loc_name,
                    "display_name": ", ".join(display_parts),
                    "lat": item.get("latitude"),
                    "lon": item.get("longitude"),
                    "country": "Bangladesh",
                    "timezone": item.get("timezone", "Asia/Dhaka")
                })
            return output

    try:
        results = await _fetch_from_open_meteo(clean_q)
        if results:
            return results
        
        # 2. If no results and query may be Bengali/obscure, resolve with AI
        ai_resolved = await resolve_area_with_ai(query.strip())
        if ai_resolved and ai_resolved.lower() != clean_q.lower():
            results = await _fetch_from_open_meteo(ai_resolved)
            if results:
                return results
    except Exception as e:
        print(f"Geocoding error for '{query}': {e}")

    return []

async def get_weather_data(lat: float, lon: float, temp_unit: str = "C") -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive weather data including:
    - Current metrics (16+ parameters)
    - 24-hour hourly forecast
    - 7 to 10-day daily forecast
    - Air Quality
    - Moon Phase
    """
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,rain,weather_code,cloud_cover,pressure_msl,"
            "surface_pressure,wind_speed_10m,wind_direction_10m,dew_point_2m"
        ),
        "hourly": (
            "temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,"
            "precipitation_probability,precipitation,weather_code,wind_speed_10m,"
            "wind_direction_10m,uv_index,visibility"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
            "apparent_temperature_min,sunrise,sunset,uv_index_max,precipitation_sum,"
            "precipitation_probability_max,wind_speed_10m_max"
        ),
        "timezone": "auto",
        "forecast_days": 10
    }

    aqi_params = {
        "latitude": lat,
        "longitude": lon,
        "current": "us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
        "hourly": "us_aqi,pm2_5,pm10",
        "timezone": "auto"
    }

    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            w_res, aqi_res = await client.get(OPEN_METEO_FORECAST_URL, params=weather_params), await client.get(OPEN_METEO_AIR_QUALITY_URL, params=aqi_params)
            w_data = w_res.json()
            aqi_data = aqi_res.json() if aqi_res.status_code == 200 else {}
        except Exception as e:
            print(f"Error fetching weather/AQI for ({lat}, {lon}): {e}")
            return None

    current = w_data.get("current", {})
    hourly = w_data.get("hourly", {})
    daily = w_data.get("daily", {})
    aqi_cur = aqi_data.get("current", {})

    # Extract current metrics with safe defaults
    raw_temp = current.get("temperature_2m")
    temp = float(raw_temp) if raw_temp is not None else 25.0
    
    raw_feels = current.get("apparent_temperature")
    feels_like = float(raw_feels) if raw_feels is not None else temp
    
    raw_hum = current.get("relative_humidity_2m")
    humidity = int(raw_hum) if raw_hum is not None else 50
    
    wmo_code = int(current.get("weather_code", 0) or 0)
    
    raw_wind = current.get("wind_speed_10m")
    wind_speed = float(raw_wind) if raw_wind is not None else 0.0
    
    raw_deg = current.get("wind_direction_10m")
    wind_deg = float(raw_deg) if raw_deg is not None else 0.0
    
    raw_clouds = current.get("cloud_cover")
    cloud_cover = int(raw_clouds) if raw_clouds is not None else 0
    
    pressure = float(current.get("pressure_msl") or current.get("surface_pressure") or 1013.0)
    
    raw_dew = current.get("dew_point_2m")
    dew_point = float(raw_dew) if raw_dew is not None else temp
    
    rainfall_amount = float(current.get("precipitation") or current.get("rain") or 0.0)

    # Hourly rain probability for current or upcoming hours
    hourly_times = hourly.get("time", [])
    hourly_rain_prob = hourly.get("precipitation_probability", [])
    hourly_visibility = hourly.get("visibility", [])
    hourly_uv = hourly.get("uv_index", [])

    # Current visibility approx from hourly
    visibility_km = (hourly_visibility[0] / 1000.0) if hourly_visibility else 10.0
    current_uv = hourly_uv[0] if hourly_uv else 0.0
    current_rain_chance = hourly_rain_prob[0] if hourly_rain_prob else 0

    # Sunrise and Sunset for today
    sunrises = daily.get("sunrise", [])
    sunsets = daily.get("sunset", [])
    today_sunrise = sunrises[0].split("T")[1] if sunrises else "06:00"
    today_sunset = sunsets[0].split("T")[1] if sunsets else "18:00"
    today_max_temp = daily.get("temperature_2m_max", [temp])[0]
    today_min_temp = daily.get("temperature_2m_min", [temp])[0]
    today_max_uv = daily.get("uv_index_max", [current_uv])[0]
    today_rain_chance_max = daily.get("precipitation_probability_max", [current_rain_chance])[0]

    # Moon phase calculation
    moon_info = get_moon_phase()

    # Air Quality metrics
    us_aqi = aqi_cur.get("us_aqi") or 0
    pm2_5 = aqi_cur.get("pm2_5") or 0.0
    pm10 = aqi_cur.get("pm10") or 0.0
    co = aqi_cur.get("carbon_monoxide") or 0.0
    no2 = aqi_cur.get("nitrogen_dioxide") or 0.0
    so2 = aqi_cur.get("sulphur_dioxide") or 0.0
    o3 = aqi_cur.get("ozone") or 0.0

    return {
        "lat": lat,
        "lon": lon,
        "timezone": w_data.get("timezone", "UTC"),
        "temp_unit": temp_unit,
        "current": {
            "temp": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "wmo_code": wmo_code,
            "wind_speed": wind_speed,
            "wind_direction_deg": wind_deg,
            "cloud_cover": cloud_cover,
            "pressure": pressure,
            "dew_point": dew_point,
            "rainfall_amount": rainfall_amount,
            "rain_probability": current_rain_chance,
            "visibility_km": visibility_km,
            "uv_index": current_uv,
            "sunrise": today_sunrise,
            "sunset": today_sunset,
            "today_max_temp": today_max_temp,
            "today_min_temp": today_min_temp,
            "today_max_uv": today_max_uv,
            "today_rain_chance_max": today_rain_chance_max,
            "moon": moon_info,
            "aqi": {
                "us_aqi": us_aqi,
                "pm2_5": pm2_5,
                "pm10": pm10,
                "co": co,
                "no2": no2,
                "so2": so2,
                "o3": o3
            }
        },
        "hourly": hourly,
        "daily": daily
    }
