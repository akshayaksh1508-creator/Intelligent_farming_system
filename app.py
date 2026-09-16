import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session
from config import config
from models import db, User, CropRecommendation, DiseaseDetection, Product, CarbonCredit
from ml_models.crop_model import get_crop_model
from ml_models.disease_model import get_disease_model
from services.weather_service import get_weather
from services.market_service import get_market_prices
from routes.simulation import simulation_bp

def create_app(env="development"):
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(config[env])

    os.makedirs(os.path.join(app.root_path, "static", "uploads"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)
    app.register_blueprint(simulation_bp)

    # ── Static Page Routes (Pure HTML, No Jinja) ──────────────────────────────
    @app.route("/")
    def serve_index():
        return send_from_directory("static/pages", "index.html")

    @app.route("/<path:page_name>")
    def serve_page(page_name):
        if not page_name.endswith(".html") and "." not in page_name:
            page_name += ".html"
        page_path = os.path.join(app.root_path, "static", "pages", page_name)
        if os.path.exists(page_path):
            return send_from_directory("static/pages", page_name)
        return send_from_directory("static/pages", "index.html")

    # ── REST API Endpoints ───────────────────────────────────────────────────

    # Auth APIs
    @app.route("/api/auth/register", methods=["POST"])
    def api_register():
        data = request.get_json() or {}
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not username or not email or not password:
            return jsonify({"success": False, "error": "Username, email, and password are required"}), 400

        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({"success": False, "error": "Username or Email already registered"}), 400

        user = User(
            username=username,
            email=email,
            full_name=data.get("full_name", username),
            phone=data.get("phone", ""),
            state=data.get("state", "Karnataka")
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        return jsonify({"success": True, "user": user.to_dict()})

    @app.route("/api/auth/login", methods=["POST"])
    def api_login():
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.role == "farmer":
                if user.is_rejected:
                    return jsonify({"success": False, "error": "Your account has been rejected."}), 403
                if not user.is_approved:
                    return jsonify({"success": False, "error": "Your account is pending admin approval."}), 403
            session["user_id"] = user.id
            return jsonify({"success": True, "user": user.to_dict()})
        return jsonify({"success": False, "error": "Invalid email or password"}), 401

    @app.route("/api/auth/logout", methods=["POST"])
    def api_logout():
        session.pop("user_id", None)
        return jsonify({"success": True})

    @app.route("/api/auth/me", methods=["GET"])
    def api_me():
        user_id = session.get("user_id")
        if user_id:
            user = User.query.get(user_id)
            if user:
                return jsonify({"authenticated": True, "user": user.to_dict()})
        return jsonify({"authenticated": False, "user": None})


    @app.route("/api/auth/complete-profile", methods=["POST"])
    def api_complete_profile():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "error": "Not logged in"}), 401
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
            
        data = request.get_json() or {}
        user.full_name = data.get("full_name", user.full_name)
        user.phone = data.get("phone", user.phone)
        user.state = data.get("state", user.state)
        user.district = data.get("district", user.district)
        user.farm_name = data.get("farm_name", user.farm_name)
        user.farm_size = data.get("farm_size", user.farm_size)
        user.primary_crop = data.get("primary_crop", user.primary_crop)
        user.aadhaar = data.get("aadhaar", user.aadhaar)
        user.bio = data.get("bio", user.bio)
        user.profile_completed = True
        
        db.session.commit()
        return jsonify({"success": True})

    # Admin APIs
    @app.route("/api/admin/login", methods=["POST"])
    def api_admin_login():
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        password = data.get("password", "")
        
        user = User.query.filter_by(email=email, role="admin").first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return jsonify({"success": True, "user": user.to_dict()})
        return jsonify({"success": False, "error": "Invalid admin credentials"}), 401

    @app.route("/api/admin/stats", methods=["GET"])
    def api_admin_stats():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                total_farmers = User.query.filter_by(role="farmer").count()
                pending = User.query.filter_by(role="farmer", profile_completed=True, is_approved=False, is_rejected=False).count()
                predictions = CropRecommendation.query.count() + DiseaseDetection.query.count()
                products = Product.query.count()
                return jsonify({
                    "total_farmers": total_farmers,
                    "pending_approvals": pending,
                    "ai_predictions": predictions,
                    "total_products": products
                })
        return jsonify({"error": "Unauthorized"}), 401
        
    @app.route("/api/admin/pending-farmers", methods=["GET"])
    def api_admin_pending():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                farmers = User.query.filter_by(role="farmer", profile_completed=True, is_approved=False, is_rejected=False).all()
                return jsonify([f.to_dict() for f in farmers])
        return jsonify([]), 401
        
    @app.route("/api/admin/approve-farmer", methods=["POST"])
    def api_admin_approve():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                data = request.get_json() or {}
                farmer = User.query.get(data.get("user_id"))
                if farmer:
                    farmer.is_approved = True
                    farmer.is_rejected = False
                    farmer.approved_at = datetime.utcnow()
                    db.session.commit()
                    return jsonify({"success": True})
        return jsonify({"error": "Unauthorized"}), 401

    @app.route("/api/admin/reject-farmer", methods=["POST"])
    def api_admin_reject():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                data = request.get_json() or {}
                farmer = User.query.get(data.get("user_id"))
                if farmer:
                    farmer.is_rejected = True
                    farmer.is_approved = False
                    db.session.commit()
                    return jsonify({"success": True})
        return jsonify({"error": "Unauthorized"}), 401

    @app.route("/api/admin/users", methods=["GET"])
    def api_admin_users():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                users = User.query.all()
                return jsonify([u.to_dict() for u in users])
        return jsonify([]), 401

    @app.route("/api/admin/delete-user", methods=["POST"])
    def api_admin_delete_user():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                data = request.get_json() or {}
                user = User.query.get(data.get("user_id"))
                if user and user.role != "admin":
                    db.session.delete(user)
                    db.session.commit()
                    return jsonify({"success": True})
        return jsonify({"error": "Unauthorized"}), 401
        
    @app.route("/api/admin/add-product", methods=["POST"])
    def api_admin_add_product():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                data = request.get_json() or {}
                prod = Product(
                    name=data.get("name"),
                    category=data.get("category"),
                    price=data.get("price"),
                    unit=data.get("unit"),
                    brand=data.get("brand"),
                    emoji=data.get("emoji")
                )
                db.session.add(prod)
                db.session.commit()
                return jsonify({"success": True})
        return jsonify({"error": "Unauthorized"}), 401
        
    @app.route("/api/admin/delete-product", methods=["POST"])
    def api_admin_delete_product():
        if session.get("user_id"):
            admin = User.query.get(session.get("user_id"))
            if admin and admin.role == "admin":
                data = request.get_json() or {}
                prod = Product.query.get(data.get("product_id"))
                if prod:
                    db.session.delete(prod)
                    db.session.commit()
                    return jsonify({"success": True})
        return jsonify({"error": "Unauthorized"}), 401
        
    # Public Stats API for Landing Page
    @app.route("/api/public/stats", methods=["GET"])
    def api_public_stats():
        farmers_count = User.query.filter_by(role="farmer").count()
        predictions_count = CropRecommendation.query.count()
        districts_count = db.session.query(User.district).filter(User.role == "farmer", User.district.isnot(None), User.district != "").distinct().count()
        
        return jsonify({
            "farmers": farmers_count,
            "predictions": predictions_count,
            "districts": districts_count
        })

    # Dashboard Stats API
    @app.route("/api/dashboard/stats", methods=["GET"])
    def api_dashboard_stats():
        user_id = session.get("user_id")
        weather = get_weather("New Delhi")
        prices = get_market_prices()

        recent_recs = []
        recent_diseases = []
        if user_id:
            recs = CropRecommendation.query.filter_by(user_id=user_id).order_by(CropRecommendation.created_at.desc()).limit(5).all()
            recent_recs = [r.to_dict() for r in recs]

            diseases = DiseaseDetection.query.filter_by(user_id=user_id).order_by(DiseaseDetection.created_at.desc()).limit(3).all()
            recent_diseases = [d.to_dict() for d in diseases]

        return jsonify({
            "weather": weather,
            "prices": prices[:6],
            "recent_crop_recs": recent_recs,
            "recent_diseases": recent_diseases,
            "yield_data": [30, 42, 38, 55, 48, 62, 58, 65, 72, 68, 75, 80],
            "profit_data": [45000, 62000, 55000, 78000, 70000, 95000, 88000, 105000, 112000, 120000, 128000, 140000],
            "market_trend": [2100, 2250, 2180, 2350, 2450, 2400, 2520]
        })

    # Crop Recommendation API
    @app.route("/api/crop/predict", methods=["POST"])
    def api_crop_predict():
        data = request.get_json() or {}
        n = float(data.get("nitrogen", 80))
        p = float(data.get("phosphorus", 60))
        k = float(data.get("potassium", 40))
        ph = float(data.get("ph", 6.5))
        temp = float(data.get("temperature", 28))
        humidity = float(data.get("humidity", 65))
        rainfall = float(data.get("rainfall", 80))
        soil_type = data.get("soil_type", "Loamy")
        season = data.get("season", "Kharif")
        land_area = float(data.get("land_area", 1.0))

        model = get_crop_model()
        res = model.predict(n, p, k, ph, temp, humidity, rainfall, soil_type, season, land_area)

        user_id = session.get("user_id")
        rec = CropRecommendation(
            user_id=user_id,
            state=data.get("state", "Karnataka"),
            district=data.get("district", "Bangalore"),
            season=season,
            soil_type=soil_type,
            land_area=land_area,
            nitrogen=n, phosphorus=p, potassium=k, ph=ph,
            temperature=temp, humidity=humidity, rainfall=rainfall,
            recommended_crop=res["recommended_crop"],
            confidence=res["confidence"],
            expected_yield=res["expected_yield"],
            expected_profit=res["expected_profit"],
            fertilizer=res["fertilizer"],
            water_requirement=res["water_requirement"],
            harvest_time=res["harvest_time"],
            alternative_crops=", ".join(res["alternative_crops"])
        )
        db.session.add(rec)
        db.session.commit()

        return jsonify({"success": True, "result": res})

    # Disease Detection API
    @app.route("/api/disease/analyze", methods=["POST"])
    def api_disease_analyze():
        if "plant_image" not in request.files:
            return jsonify({"success": False, "error": "No image file uploaded"}), 400
        file = request.files["plant_image"]
        image_bytes = file.read()
        plant_type = request.form.get("plant_type", "Tomato")

        model = get_disease_model()
        res = model.predict(image_bytes, plant_type)

        filename = f"disease_{file.filename}"
        user_id = session.get("user_id")
        detection = DiseaseDetection(
            user_id=user_id,
            image_path=filename,
            plant_type=res["plant_type"],
            disease_name=res["disease_name"],
            confidence=res["confidence"],
            symptoms=res["symptoms"],
            treatment=res["treatment"],
            medicine=res["medicine"],
            organic_solution=res["organic_solution"],
            preventive_measures=res["preventive_measures"],
            is_healthy=res["is_healthy"]
        )
        db.session.add(detection)
        db.session.commit()

        return jsonify({"success": True, "result": res})

    # Weather API
    @app.route("/api/weather", methods=["GET"])
    def api_weather():
        location = request.args.get("location", "New Delhi")
        return jsonify(get_weather(location))

    # Marketplace API
    @app.route("/api/marketplace/products", methods=["GET"])
    def api_products():
        category = request.args.get("category", "all")
        query = Product.query
        if category != "all":
            query = query.filter_by(category=category)
        products = [p.to_dict() for p in query.all()]
        return jsonify(products)

    # Chatbot API
    @app.route("/api/chatbot/message", methods=["POST"])
    def api_chatbot():
        data = request.get_json() or {}
        msg = data.get("message", "").lower()

        if "crop" in msg or "grow" in msg or "sow" in msg:
            resp = "🌾 For AI crop recommendations, visit the Crop Recommendation tool! You can input your soil NPK levels, temperature, and season for exact predictions."
        elif "disease" in msg or "sick" in msg or "leaf" in msg:
            resp = "🔬 You can upload an image of your plant on the Disease Detection page to diagnose diseases and receive immediate organic and chemical treatments."
        elif "weather" in msg or "rain" in msg:
            resp = "🌤️ Currently in New Delhi: 34°C, partly cloudy with 25% rain probability. Check the Weather tab for full 7-day forecasts!"
        elif "price" in msg or "rate" in msg or "market" in msg:
            resp = "📈 Today's top market rates: Tomato ₹2,450/q, Rice ₹2,183/q, Wheat ₹2,275/q, Cotton ₹6,620/q."
        elif "scheme" in msg or "government" in msg or "pm-kisan" in msg:
            resp = "🏛️ Key Scheme: PM-KISAN provides ₹6,000/year direct support to farmer families. PMFBY offers comprehensive crop insurance!"
        else:
            resp = "🤖 Hello! I am Farm Wise AI Assistant. I can assist you with Crop Recommendations, Disease Diagnosis, Weather Forecasts, Market Prices, and Government Schemes."

        return jsonify({"response": resp})

    # Carbon API
    @app.route("/api/carbon/calculate", methods=["POST"])
    def api_carbon_calculate():
        data = request.get_json() or {}
        farm_size = float(data.get("farm_size", 1.0))
        crop_type = data.get("crop_type", "Wheat")
        practice = data.get("practice", "No-till farming")

        factors = {
            "No-till farming": 0.4,
            "Cover cropping": 0.3,
            "Agroforestry": 1.5,
            "Composting": 0.2,
            "Biochar application": 0.8
        }
        factor = factors.get(practice, 0.3)
        carbon_captured = round(farm_size * factor, 2)
        credits_earned = carbon_captured
        estimated_value = int(credits_earned * 1500)

        user_id = session.get("user_id")
        rec = CarbonCredit(
            user_id=user_id,
            farm_size=farm_size,
            crop_type=crop_type,
            practice=practice,
            carbon_captured=carbon_captured,
            credits_earned=credits_earned,
            estimated_value=estimated_value
        )
        db.session.add(rec)
        db.session.commit()

        return jsonify({
            "success": True,
            "result": {
                "carbon_captured": carbon_captured,
                "credits_earned": credits_earned,
                "estimated_value": estimated_value,
                "practice": practice
            }
        })

    # Init & Seed DB
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", email="admin@farmwise.ai", full_name="Admin", role="admin", is_approved=True, profile_completed=True)
            admin_user.set_password("admin123")
            db.session.add(admin_user)

        if not User.query.filter_by(username="ramesh").first():
            demo_user = User(username="ramesh", email="ramesh@example.com", full_name="Ramesh Kumar", state="Maharashtra")
            demo_user.set_password("farmer123")
            db.session.add(demo_user)

        if Product.query.count() == 0:
            sample_prods = [
                Product(name="Hybrid Tomato Seeds F1", category="seeds", price=450, unit="100g", emoji="🍅", brand="Mahyco", is_organic=False),
                Product(name="Neem Coated Urea", category="fertilizers", price=380, unit="45kg", emoji="🌾", brand="IFFCO", is_organic=False),
                Product(name="Organic Vermicompost", category="organic", price=250, unit="5kg", emoji="🪱", brand="Green Earth", is_organic=True),
                Product(name="Mini Drip Kit", category="irrigation", price=3500, unit="Set", emoji="💧", brand="Jain Irrigation", is_organic=False),
                Product(name="Power Sprayer 16L", category="machinery", price=2800, unit="Unit", emoji="⚙️", brand="Aspee", is_organic=False),
                Product(name="Bio-Fungicide Trichoderma", category="organic", price=180, unit="200g", emoji="🍄", brand="Multiplex", is_organic=True),
            ]
            db.session.add_all(sample_prods)
        db.session.commit()

    return app

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  Farm Wise AI (Pure HTML/CSS/JS + Flask REST API)")
    print("  Server running at: http://127.0.0.1:5000")
    print("  Directory: D:\\Akshay\\Documents\\scratch\\farm-wise-ai")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
