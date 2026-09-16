"""
Farm Wise AI – Dashboard Routes
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.market_service import get_market_prices, get_trending_crops
from services.weather_service import get_weather
from models import CropRecommendation, DiseaseDetection
import random

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    # Weather for user's location (default: New Delhi)
    location = current_user.state or "New Delhi"
    weather = get_weather(location)

    # Market prices
    prices = get_market_prices(limit=6)

    # Recent activity
    recent_crops = CropRecommendation.query.filter_by(
        user_id=current_user.id
    ).order_by(CropRecommendation.created_at.desc()).limit(5).all()

    recent_diseases = DiseaseDetection.query.filter_by(
        user_id=current_user.id
    ).order_by(DiseaseDetection.created_at.desc()).limit(3).all()

    # Dashboard stats
    stats = {
        "total_recommendations": CropRecommendation.query.filter_by(user_id=current_user.id).count(),
        "disease_detections": DiseaseDetection.query.filter_by(user_id=current_user.id).count(),
        "ai_insights": random.randint(3, 12),
    }

    # Chart data – yield prediction (monthly)
    yield_data = [random.randint(20, 60) for _ in range(12)]
    profit_data = [random.randint(40000, 120000) for _ in range(12)]
    market_trend = [random.randint(2000, 3500) for _ in range(7)]

    return render_template(
        "dashboard/index.html",
        weather=weather,
        prices=prices,
        recent_crops=recent_crops,
        recent_diseases=recent_diseases,
        stats=stats,
        yield_data=yield_data,
        profit_data=profit_data,
        market_trend=market_trend,
    )
