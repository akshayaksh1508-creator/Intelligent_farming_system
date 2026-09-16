from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default="farmer")  # farmer | admin
    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    farm_name = db.Column(db.String(150))
    farm_size = db.Column(db.Float, default=1.0)
    primary_crop = db.Column(db.String(100))
    aadhaar = db.Column(db.String(20))
    bio = db.Column(db.Text)
    # Approval workflow
    profile_completed = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def status(self):
        if self.is_rejected:
            return "rejected"
        if self.is_approved:
            return "approved"
        if self.profile_completed:
            return "pending"
        return "incomplete"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "state": self.state,
            "district": self.district,
            "farm_name": self.farm_name,
            "farm_size": self.farm_size,
            "primary_crop": self.primary_crop,
            "aadhaar": self.aadhaar,
            "bio": self.bio,
            "profile_completed": self.profile_completed,
            "is_approved": self.is_approved,
            "is_rejected": self.is_rejected,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }

class CropRecommendation(db.Model):
    __tablename__ = "crop_recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    state = db.Column(db.String(100))
    district = db.Column(db.String(100))
    season = db.Column(db.String(50))
    soil_type = db.Column(db.String(50))
    land_area = db.Column(db.Float)
    nitrogen = db.Column(db.Float)
    phosphorus = db.Column(db.Float)
    potassium = db.Column(db.Float)
    ph = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    rainfall = db.Column(db.Float)
    recommended_crop = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    expected_yield = db.Column(db.Float)
    expected_profit = db.Column(db.Float)
    fertilizer = db.Column(db.String(200))
    water_requirement = db.Column(db.String(100))
    harvest_time = db.Column(db.String(100))
    alternative_crops = db.Column(db.String(500))

    def to_dict(self):
        return {
            "id": self.id,
            "recommended_crop": self.recommended_crop,
            "confidence": self.confidence,
            "expected_yield": self.expected_yield,
            "expected_profit": self.expected_profit,
            "fertilizer": self.fertilizer,
            "water_requirement": self.water_requirement,
            "harvest_time": self.harvest_time,
            "alternative_crops": self.alternative_crops.split(", ") if self.alternative_crops else [],
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }

class DiseaseDetection(db.Model):
    __tablename__ = "disease_detections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(300))
    plant_type = db.Column(db.String(100))
    disease_name = db.Column(db.String(200))
    confidence = db.Column(db.Float)
    symptoms = db.Column(db.Text)
    treatment = db.Column(db.Text)
    medicine = db.Column(db.Text)
    organic_solution = db.Column(db.Text)
    preventive_measures = db.Column(db.Text)
    is_healthy = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "image_path": self.image_path,
            "plant_type": self.plant_type,
            "disease_name": self.disease_name,
            "confidence": self.confidence,
            "symptoms": self.symptoms,
            "treatment": self.treatment,
            "medicine": self.medicine,
            "organic_solution": self.organic_solution,
            "preventive_measures": self.preventive_measures,
            "is_healthy": self.is_healthy,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=100)
    emoji = db.Column(db.String(10), default="x")
    brand = db.Column(db.String(100))
    rating = db.Column(db.Float, default=4.5)
    review_count = db.Column(db.Integer, default=100)
    is_organic = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "price": self.price,
            "unit": self.unit,
            "stock": self.stock,
            "emoji": self.emoji,
            "brand": self.brand,
            "rating": self.rating,
            "review_count": self.review_count,
            "is_organic": self.is_organic,
        }

class CarbonCredit(db.Model):
    __tablename__ = "carbon_credits"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    farm_size = db.Column(db.Float)
    crop_type = db.Column(db.String(100))
    practice = db.Column(db.String(200))
    carbon_captured = db.Column(db.Float)
    credits_earned = db.Column(db.Float)
    estimated_value = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "farm_size": self.farm_size,
            "crop_type": self.crop_type,
            "practice": self.practice,
            "carbon_captured": self.carbon_captured,
            "credits_earned": self.credits_earned,
            "estimated_value": self.estimated_value,
            "created_at": self.created_at.strftime("%Y-%m-%d"),
        }
