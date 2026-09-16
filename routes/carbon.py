"""
Farm Wise AI – Carbon Farming Advisor Routes
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, CarbonCredit
import random

carbon_bp = Blueprint("carbon", __name__, url_prefix="/carbon")

CARBON_PRACTICES = {
    "No-till farming": {"factor": 0.4, "description": "Reduces soil disturbance, preserving carbon in soil"},
    "Cover cropping": {"factor": 0.3, "description": "Increases soil organic matter and carbon sequestration"},
    "Agroforestry": {"factor": 1.5, "description": "Trees sequester large amounts of carbon over time"},
    "Composting": {"factor": 0.2, "description": "Returns organic carbon to soil, reduces methane emissions"},
    "Biochar application": {"factor": 0.8, "description": "Stable carbon form that persists in soil for centuries"},
    "Improved rice cultivation": {"factor": -0.3, "description": "AWD technique reduces methane from flooded paddies"},
    "Precision fertilization": {"factor": 0.15, "description": "Reduces N2O emissions from excess fertilizer"},
    "Organic farming": {"factor": 0.5, "description": "Builds soil carbon through organic inputs"},
}

CARBON_PRICE_INR = 1500  # ₹ per tonne CO2


@carbon_bp.route("/")
@login_required
def index():
    user_credits = CarbonCredit.query.filter_by(user_id=current_user.id).all()
    total_carbon = sum(c.carbon_captured for c in user_credits)
    total_credits = sum(c.credits_earned for c in user_credits)
    total_value = sum(c.estimated_value for c in user_credits)

    return render_template(
        "carbon/index.html",
        practices=CARBON_PRACTICES,
        user_credits=user_credits,
        total_carbon=round(total_carbon, 2),
        total_credits=round(total_credits, 2),
        total_value=round(total_value, 0),
    )


@carbon_bp.route("/calculate", methods=["POST"])
@login_required
def calculate():
    farm_size = float(request.form.get("farm_size", 1.0))
    crop_type = request.form.get("crop_type", "Wheat")
    practice = request.form.get("practice", "No-till farming")
    years = float(request.form.get("years", 1))

    factor = CARBON_PRACTICES.get(practice, {}).get("factor", 0.3)
    carbon_captured = round(farm_size * factor * years, 2)
    credits_earned = round(carbon_captured, 2)
    estimated_value = round(credits_earned * CARBON_PRICE_INR, 0)

    record = CarbonCredit(
        user_id=current_user.id,
        farm_size=farm_size,
        crop_type=crop_type,
        practice=practice,
        carbon_captured=carbon_captured,
        credits_earned=credits_earned,
        estimated_value=estimated_value,
    )
    db.session.add(record)
    db.session.commit()

    user_credits = CarbonCredit.query.filter_by(user_id=current_user.id).all()
    total_carbon = sum(c.carbon_captured for c in user_credits)
    total_credits = sum(c.credits_earned for c in user_credits)
    total_value = sum(c.estimated_value for c in user_credits)

    return render_template(
        "carbon/index.html",
        practices=CARBON_PRACTICES,
        user_credits=user_credits,
        total_carbon=round(total_carbon, 2),
        total_credits=round(total_credits, 2),
        total_value=round(total_value, 0),
        result={
            "carbon_captured": carbon_captured,
            "credits_earned": credits_earned,
            "estimated_value": int(estimated_value),
            "practice": practice,
            "practice_desc": CARBON_PRACTICES.get(practice, {}).get("description", ""),
        },
        form_data=request.form,
    )
