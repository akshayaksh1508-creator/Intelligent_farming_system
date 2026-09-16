import os
import re

app_path = r"D:\Akshay\Documents\scratch\farm-wise-ai\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import datetime if not exists
if "from datetime import datetime" not in content:
    content = content.replace("import os", "import os\nfrom datetime import datetime")

# Update api_login
login_replacement = """
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
"""
content = re.sub(
    r'@app\.route\("/api/auth/login", methods=\["POST"\]\)\s+def api_login\(\):.*?return jsonify\(\{"success": False, "error": "Invalid email or password"\}\), 401',
    login_replacement.strip(),
    content,
    flags=re.DOTALL
)

# New routes to inject before # Dashboard Stats API
new_routes = """
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
        
    # Dashboard Stats API
"""

content = content.replace("    # Dashboard Stats API\n", new_routes)

# Insert the admin account creation if it doesn't exist
admin_creation = """
        if not User.query.filter_by(username="admin").first():
            admin_user = User(username="admin", email="admin@farmwise.ai", full_name="Admin", role="admin", is_approved=True, profile_completed=True)
            admin_user.set_password("admin123")
            db.session.add(admin_user)
"""

if "username=\"admin\"" not in content:
    content = content.replace("db.create_all()", "db.create_all()" + admin_creation)

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("App patched successfully!")
