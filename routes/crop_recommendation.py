"""
Farm Wise AI – Crop Recommendation Routes
"""

import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, CropRecommendation
from ml_models.crop_model import get_crop_model

crop_bp = Blueprint("crop", __name__, url_prefix="/crop")

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
]

SOIL_TYPES = ["Sandy Loam", "Loamy", "Clay Loam", "Clayey", "Black", "Red", "Alluvial", "Laterite"]
SEASONS = ["Kharif", "Rabi", "Zaid", "Annual"]


@crop_bp.route("/")
@login_required
def recommendation():
    return render_template(
        "crop/recommendation.html",
        states=INDIAN_STATES,
        soil_types=SOIL_TYPES,
        seasons=SEASONS,
    )


@crop_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    try:
        data = request.form
        n = float(data.get("nitrogen", 80))
        p = float(data.get("phosphorus", 60))
        k = float(data.get("potassium", 40))
        ph = float(data.get("ph", 6.5))
        temp = float(data.get("temperature", 28))
        humidity = float(data.get("humidity", 65))
        rainfall = float(data.get("rainfall", 80))
        soil_type = data.get("soil_type", "Loamy")
        season = data.get("season", "Kharif")
        state = data.get("state", "")
        district = data.get("district", "")
        land_area = float(data.get("land_area", 1.0))
        previous_crop = data.get("previous_crop", "")

        model = get_crop_model()
        result = model.predict(n, p, k, ph, temp, humidity, rainfall, soil_type, season)

        # Scale yield to land area
        result["expected_yield"] = round(result["expected_yield"] * land_area, 1)
        result["expected_profit"] = int(result["expected_profit"] * land_area)

        # Save to DB
        rec = CropRecommendation(
            user_id=current_user.id,
            state=state,
            district=district,
            season=season,
            soil_type=soil_type,
            land_area=land_area,
            nitrogen=n, phosphorus=p, potassium=k,
            ph=ph, temperature=temp, humidity=humidity, rainfall=rainfall,
            previous_crop=previous_crop,
            recommended_crop=result["recommended_crop"],
            confidence=result["confidence"],
            expected_yield=result["expected_yield"],
            expected_profit=result["expected_profit"],
            fertilizer=result["fertilizer"],
            water_requirement=result["water_requirement"],
            harvest_time=result["harvest_time"],
            alternative_crops=", ".join(result["alternative_crops"]),
        )
        db.session.add(rec)
        db.session.commit()
        result["recommendation_id"] = rec.id

        return render_template(
            "crop/recommendation.html",
            states=INDIAN_STATES,
            soil_types=SOIL_TYPES,
            seasons=SEASONS,
            result=result,
            form_data=data,
        )

    except Exception as e:
        flash(f"Error generating recommendation: {str(e)}", "danger")
        return redirect(url_for("crop.recommendation"))


@crop_bp.route("/api/predict", methods=["POST"])
def api_predict():
    """REST API endpoint for crop prediction."""
    data = request.get_json() or {}
    try:
        model = get_crop_model()
        result = model.predict(
            n=float(data.get("nitrogen", 80)),
            p=float(data.get("phosphorus", 60)),
            k=float(data.get("potassium", 40)),
            ph=float(data.get("ph", 6.5)),
            temperature=float(data.get("temperature", 28)),
            humidity=float(data.get("humidity", 65)),
            rainfall=float(data.get("rainfall", 80)),
            soil_type=data.get("soil_type", "Loamy"),
            season=data.get("season", "Kharif"),
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@crop_bp.route("/history")
@login_required
def history():
    recs = CropRecommendation.query.filter_by(
        user_id=current_user.id
    ).order_by(CropRecommendation.created_at.desc()).all()
    return render_template("crop/history.html", recommendations=recs)
