"""
Farm Wise AI – Marketplace Routes
"""

import random
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user
from models import db, Product

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")

SAMPLE_PRODUCTS = [
    {"name": "Hybrid Tomato Seeds – F1 Variety", "category": "seeds", "price": 450, "unit": "100g Pack", "brand": "Mahyco", "rating": 4.5, "review_count": 342, "is_organic": False, "emoji": "🍅"},
    {"name": "Urea Fertilizer – 45 kg", "category": "fertilizers", "price": 380, "unit": "45 kg Bag", "brand": "NFL", "rating": 4.2, "review_count": 1204, "is_organic": False, "emoji": "🌿"},
    {"name": "Neem Coated Urea – 50 kg", "category": "fertilizers", "price": 420, "unit": "50 kg Bag", "brand": "IFFCO", "rating": 4.4, "review_count": 876, "is_organic": False, "emoji": "🌾"},
    {"name": "Organic Vermicompost – 5 kg", "category": "organic", "price": 250, "unit": "5 kg Bag", "brand": "Green Earth", "rating": 4.7, "review_count": 563, "is_organic": True, "emoji": "🪱"},
    {"name": "Mini Drip Irrigation Kit", "category": "irrigation", "price": 3500, "unit": "Set/Acre", "brand": "Jain Irrigation", "rating": 4.6, "review_count": 234, "is_organic": False, "emoji": "💧"},
    {"name": "Power Sprayer – 16L", "category": "machinery", "price": 2800, "unit": "Unit", "brand": "Aspee", "rating": 4.3, "review_count": 445, "is_organic": False, "emoji": "⚙️"},
    {"name": "DAP Fertilizer – 50 kg", "category": "fertilizers", "price": 1350, "unit": "50 kg Bag", "brand": "IFFCO", "rating": 4.5, "review_count": 2341, "is_organic": False, "emoji": "🌱"},
    {"name": "Hybrid Maize Seeds – 5 kg", "category": "seeds", "price": 820, "unit": "5 kg Pack", "brand": "Pioneer", "rating": 4.4, "review_count": 678, "is_organic": False, "emoji": "🌽"},
    {"name": "Imidacloprid 70WS Pesticide", "category": "pesticides", "price": 340, "unit": "100g", "brand": "Bayer", "rating": 4.1, "review_count": 912, "is_organic": False, "emoji": "🐛"},
    {"name": "Bio-Fungicide Trichoderma", "category": "organic", "price": 180, "unit": "200g", "brand": "Multiplex", "rating": 4.6, "review_count": 328, "is_organic": True, "emoji": "🍄"},
    {"name": "Portable Weather Station", "category": "machinery", "price": 12500, "unit": "Unit", "brand": "AgriSense", "rating": 4.8, "review_count": 89, "is_organic": False, "emoji": "🌡️"},
    {"name": "MOP Potash Fertilizer – 50kg", "category": "fertilizers", "price": 1200, "unit": "50 kg Bag", "brand": "IPL", "rating": 4.3, "review_count": 445, "is_organic": False, "emoji": "🌿"},
    {"name": "Organic Neem Oil Spray", "category": "organic", "price": 320, "unit": "500ml", "brand": "Down to Earth", "rating": 4.5, "review_count": 721, "is_organic": True, "emoji": "🌿"},
    {"name": "Wheat Seeds – HD-3086", "category": "seeds", "price": 680, "unit": "10 kg Pack", "brand": "IARI", "rating": 4.6, "review_count": 1123, "is_organic": False, "emoji": "🌾"},
    {"name": "Solar Water Pump – 1 HP", "category": "irrigation", "price": 28000, "unit": "Unit", "brand": "Shakti", "rating": 4.7, "review_count": 156, "is_organic": False, "emoji": "☀️"},
    {"name": "Mancozeb Fungicide 75WP", "category": "pesticides", "price": 290, "unit": "250g", "brand": "Dhanuka", "rating": 4.2, "review_count": 534, "is_organic": False, "emoji": "🧪"},
]


def init_products():
    """Seed sample products if DB is empty."""
    if Product.query.count() == 0:
        for i, p in enumerate(SAMPLE_PRODUCTS):
            product = Product(
                name=p["name"],
                category=p["category"],
                price=p["price"],
                unit=p["unit"],
                brand=p["brand"],
                rating=p["rating"],
                review_count=p["review_count"],
                is_organic=p["is_organic"],
                description=f"High quality {p['name']} for Indian farmers. {p['brand']} certified product.",
                stock=random.randint(20, 200),
                is_featured=i < 4,
            )
            db.session.add(product)
        db.session.commit()


@marketplace_bp.route("/")
def index():
    category = request.args.get("category", "all")
    search = request.args.get("search", "")
    sort = request.args.get("sort", "featured")
    page = request.args.get("page", 1, type=int)

    query = Product.query
    if category != "all":
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "rating":
        query = query.order_by(Product.rating.desc())
    else:
        query = query.order_by(Product.is_featured.desc(), Product.created_at.desc())

    products = query.paginate(page=page, per_page=12, error_out=False)
    categories = ["all", "seeds", "fertilizers", "machinery", "pesticides", "organic", "irrigation"]

    return render_template(
        "marketplace/index.html",
        products=products,
        categories=categories,
        current_category=category,
        search=search,
        sort=sort,
        sample_products=SAMPLE_PRODUCTS,
    )


@marketplace_bp.route("/cart")
def cart():
    return render_template("marketplace/cart.html")


@marketplace_bp.route("/api/add-to-cart", methods=["POST"])
def add_to_cart():
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    cart = session.get("cart", {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session["cart"] = cart
    session.modified = True

    return jsonify({"success": True, "cart_count": sum(cart.values())})
