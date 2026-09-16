"""
Farm Wise AI – Main Routes (Landing Page, Home)
"""

from flask import Blueprint, render_template
from services.market_service import get_market_prices, get_trending_crops

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    trending = get_trending_crops()
    prices = get_market_prices(limit=8)
    return render_template("index.html", trending=trending, prices=prices)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")
