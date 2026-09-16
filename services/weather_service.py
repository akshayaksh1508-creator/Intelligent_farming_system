import requests, random
from flask import current_app
from datetime import datetime, timedelta

def get_weather(location="New Delhi"):
    api_key = current_app.config.get("WEATHER_API_KEY", "")
    if api_key and api_key != "your_weatherapi_key_here":
        try:
            resp = requests.get(
                f"{current_app.config.get('WEATHER_API_BASE')}/forecast.json",
                params={"key": api_key, "q": location, "days": 7},
                timeout=4
            )
            if resp.status_code == 200:
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
                            "rain_chance": f["day"]["daily_chance_of_rain"]
                        } for f in forecast
                    ]
                }
        except Exception:
            pass

    # Demo Fallback
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
