"""
Farm Wise AI – Weather Routes
"""

from flask import Blueprint, render_template, request
from services.weather_service import get_weather

weather_bp = Blueprint("weather", __name__, url_prefix="/weather")


@weather_bp.route("/")
def index():
    location = request.args.get("location", "New Delhi")
    weather = get_weather(location)
    cities = ["New Delhi", "Mumbai", "Bangalore", "Hyderabad", "Pune",
              "Chennai", "Kolkata", "Jaipur", "Lucknow", "Chandigarh"]
    return render_template("weather/index.html", weather=weather, cities=cities, selected_city=location)
