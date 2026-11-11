import random
import requests
from flask import current_app
from datetime import datetime, timedelta

from services.geo_service import reverse_geocode

_CACHE_TTL_SECONDS = 300
_cache = {}

WMO_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Light Drizzle",
    53: "Drizzle",
    55: "Heavy Drizzle",
    61: "Light Rain",
    63: "Rain",
    65: "Heavy Rain",
    71: "Light Snow",
    73: "Snow",
    75: "Heavy Snow",
    80: "Light Showers",
    81: "Rain Showers",
    82: "Heavy Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Hail",
    99: "Thunderstorm with Hail",
}


def _fmt_hour(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%I:%M %p")
    except Exception:
        return "06:00 AM"


def _fetch_open_meteo(location, lat=None, lon=None):
    try:
        place_name = location
        region = None
        if lat is not None and lon is not None:
            geo = reverse_geocode(lat, lon) or {}
            place_name = geo.get("city") or location or "Your Location"
            region = geo.get("region")
            place_lat, place_lon = float(lat), float(lon)
        else:
            geo = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "language": "en"},
                timeout=5,
            )
            if geo.status_code != 200:
                return None
            results = (geo.json() or {}).get("results") or []
            if not results:
                return None
            place = results[0]
            place_lat, place_lon = place["latitude"], place["longitude"]
            place_name = place.get("name") or location
            region = place.get("admin1") or place.get("country") or "India"

        fc = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place_lat,
                "longitude": place_lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "weather_code,wind_speed_10m,surface_pressure",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,sunrise,sunset",
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=6,
        )
        if fc.status_code != 200:
            return None
        data = fc.json()
        current = data.get("current") or {}
        daily = data.get("daily") or {}

        days = daily.get("time") or []
        max_temps = daily.get("temperature_2m_max") or []
        min_temps = daily.get("temperature_2m_min") or []
        codes = daily.get("weather_code") or []
        rain_probs = daily.get("precipitation_probability_max") or []
        sunrises = daily.get("sunrise") or []
        sunsets = daily.get("sunset") or []

        weekly = []
        for i, day in enumerate(days[:7]):
            weekly.append(
                {
                    "day": datetime.strptime(day, "%Y-%m-%d").strftime("%a"),
                    "max_temp": round(max_temps[i], 1) if i < len(max_temps) else None,
                    "min_temp": round(min_temps[i], 1) if i < len(min_temps) else None,
                    "condition": WMO_CODES.get(codes[i] if i < len(codes) else -1, "Partly Cloudy"),
                    "rain_chance": rain_probs[i] if i < len(rain_probs) and rain_probs[i] is not None else 0,
                }
            )

        current_code = current.get("weather_code", -1)
        return {
            "location": place_name or location or "Your Location",
            "region": region or "India",
            "temp": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "pressure": current.get("surface_pressure"),
            "condition": WMO_CODES.get(current_code, "Partly Cloudy"),
            "rain_chance": weekly[0]["rain_chance"] if weekly else 0,
            "sunrise": _fmt_hour(sunrises[0]) if sunrises else "06:00 AM",
            "sunset": _fmt_hour(sunsets[0]) if sunsets else "06:30 PM",
            "is_demo": False,
            "weekly": weekly,
        }
    except Exception:
        return None


def _fetch_weatherapi(location):
    api_key = current_app.config.get("WEATHER_API_KEY", "")
    if not api_key or api_key == "your_weatherapi_key_here":
        return None
    try:
        resp = requests.get(
            f"{current_app.config.get('WEATHER_API_BASE')}/forecast.json",
            params={"key": api_key, "q": location, "days": 7},
            timeout=4,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        current = data["current"]
        forecast = data["forecast"]["forecastday"]
        return {
            "location": data["location"]["name"],
            "region": data["location"]["region"],
            "temp": current["temp_c"],
            "feels_like": current["feelslike_c"],
            "humidity": current["humidity"],
            "wind_speed": current["wind_kph"],
            "pressure": current["pressure_mb"],
            "condition": current["condition"]["text"],
            "rain_chance": forecast[0]["day"]["daily_chance_of_rain"],
            "sunrise": forecast[0]["astro"]["sunrise"],
            "sunset": forecast[0]["astro"]["sunset"],
            "is_demo": False,
            "weekly": [
                {
                    "day": datetime.strptime(f["date"], "%Y-%m-%d").strftime("%a"),
                    "max_temp": f["day"]["maxtemp_c"],
                    "min_temp": f["day"]["mintemp_c"],
                    "condition": f["day"]["condition"]["text"],
                    "rain_chance": f["day"]["daily_chance_of_rain"],
                }
                for f in forecast
            ],
        }
    except Exception:
        return None


def _demo_weather(location):
    cities = {
        "New Delhi": 34, "Mumbai": 30, "Bangalore": 25, "Hyderabad": 31, "Pune": 28
    }
    temp = cities.get(location, 29)
    weekly = []
    for i in range(7):
        day = datetime.now() + timedelta(days=i)
        weekly.append({
            "day": day.strftime("%a"),
            "max_temp": round(temp + random.uniform(0, 5), 1),
            "min_temp": round(temp - random.uniform(3, 7), 1),
            "condition": random.choice(["Sunny", "Partly Cloudy", "Light Rain", "Clear"]),
            "rain_chance": random.randint(10, 60)
        })

    return {
        "location": location,
        "region": "India",
        "temp": temp,
        "feels_like": temp - 2,
        "humidity": random.randint(55, 75),
        "wind_speed": random.randint(10, 22),
        "pressure": 1012,
        "condition": "Partly Cloudy",
        "rain_chance": 25,
        "sunrise": "06:12 AM",
        "sunset": "07:28 PM",
        "is_demo": True,
        "weekly": weekly
    }


def get_weather(location="New Delhi", lat=None, lon=None):
    if lat is not None and lon is not None:
        key = f"{float(lat):.3f},{float(lon):.3f}"
    else:
        key = (location or "New Delhi").strip().lower()
    now_ts = datetime.utcnow().timestamp()
    cached = _cache.get(key)
    if cached and cached[0] > now_ts:
        return cached[1]

    payload = (
        _fetch_open_meteo(location, lat, lon)
        or _fetch_weatherapi(location)
        or _demo_weather(location or "Your Location")
    )
    _cache[key] = (now_ts + _CACHE_TTL_SECONDS, payload)
    return payload
